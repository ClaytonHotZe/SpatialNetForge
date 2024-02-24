import time

import geopandas as gpd
import pandas as pd
import psutil
import torch
from PIL import Image
from sahi import AutoDetectionModel
from sahi.predict import get_sliced_prediction

from gdal_helpers import *
from sid_helpers import *


def merge_shapefiles(shapefile_list, output_file):
    """
    Merge shapefiles into a single shapefile.

    Parameters:
    - shapefile_list: List of paths to shapefiles.
    - output_file: Path for the output merged shapefile.
    """
    # Initialize an empty list to hold the dataframes
    gdf_list = []

    # Loop through the list of shapefiles
    for shapefile in shapefile_list:
        # Read the shapefile as a GeoDataFrame
        gdf = gpd.read_file(shapefile)
        # Append the GeoDataFrame to the list
        gdf_list.append(gdf)

    # Concatenate all GeoDataFrames in the list into one GeoDataFrame
    merged_gdf = gpd.GeoDataFrame(pd.concat(gdf_list, ignore_index=True))

    # Ensure the CRS is consistent for all GeoDataFrames, if needed
    # For example, set to the CRS of the first shapefile (optional)
    # merged_gdf.crs = gdf_list[0].crs

    # Save the merged GeoDataFrame as a new shapefile
    merged_gdf.to_file(output_file)


def worker_sanity_check(workers, device, model_path, ave_file_size, overhead=8):
    """
    This function checks the system's resources (CPU threads, CUDA memory if available) and recommends the maximum number of workers that can be used for a task based on the available resources.

    Parameters:
    workers (int): The number of workers intended to be used.
    device (str): The device to be used for the task ('cpu' or 'cuda:0').
    model_path (str): The path to the model file. This is used to calculate the memory requirements if the device is 'cuda:0'.
    ave_file_size (int): The average size of the files to be processed. This is used to calculate the recommended memory.
    overhead (int, optional): A factor used to calculate the recommended memory. Default is 4.

    Returns:
    int: The recommended maximum number of workers based on the available resources.
    dict: A dictionary containing various information about the system's resources and the recommended number of workers.
    """
    # Calculate the recommended memory based on the average file size and the overhead
    rec_memory = ave_file_size * overhead
    max_rec_workers = 1
    ret_dict = {}
    # Get the number of CPU threads
    threads = os.cpu_count()
    print(f'Number of threads: {threads}')
    # If the device is 'cuda:0', get the CUDA memory and calculate the number of workers that can be used based on the CUDA memory
    if device == 'cuda:0':
        cuda_mem = torch.cuda.mem_get_info()
        print(f'Cuda Memory: {cuda_mem}')
        cuda_workers = cuda_mem[0] / (os.path.getsize(model_path) * overhead)
        print(f'Cuda Workers: {cuda_workers}')
        # If the number of CUDA workers is less than the intended number of workers, recommend using the number of CUDA workers
        if cuda_workers < workers:
            print(
                f'You are trying to use {workers} workers, but you only have enough memory for {cuda_workers} workers')
            print(
                f'You may want to consider reducing the number of workers or increasing the amount of memory available')
            max_rec_workers = cuda_workers
            print(f'Max recommended workers: {max_rec_workers}')
        else:
            max_rec_workers = workers
            print(f'Max recommended workers: {max_rec_workers}')
        ret_dict['cuda_workers'] = cuda_workers
        ret_dict['cuda_mem'] = cuda_mem
        ret_dict['max_rec_workers'] = max_rec_workers
    else:
        max_rec_workers = 1
        print(f'Max recommended workers: {max_rec_workers}')
        ret_dict['max_rec_workers'] = max_rec_workers
    # Get the system memory and calculate the number of workers that can be used based on the system memory
    system_mem = psutil.virtual_memory()
    cpu_memory_rec = system_mem[0] / (ave_file_size * 32)
    ret_dict['system_mem'] = system_mem
    ret_dict['cpu_memory_rec'] = cpu_memory_rec
    print(f'System Memory: {system_mem}')
    print(f'CPU Memory Recommended: {cpu_memory_rec}')
    # If the number of workers that can be used based on the system memory is less than the intended number of workers, recommend using the number of workers that can be used based on the system memory
    if cpu_memory_rec < workers:
        print(f'You are trying to use {workers} workers, but you only have enough memory for {cpu_memory_rec} workers')
        print(f'You may want to consider reducing the number of workers or increasing the amount of memory available')
        max_rec_workers = cpu_memory_rec
        print(f'Max recommended workers: {max_rec_workers}')
    else:
        max_rec_workers = workers
        print(f'Max recommended workers: {max_rec_workers}')
    max_rec_workers = int(max_rec_workers)
    ret_dict['max_rec_workers'] = max_rec_workers
    return max_rec_workers, ret_dict


def results_to_shp(results, input, img_meta):
    """
    This function exports the results to both a polygon and a point shapefile.

    Parameters:
    results (list): A list of dictionaries. Each dictionary represents a result and should have 'bbox', 'category_name', and 'score' keys.
    input (dict): A dictionary containing various parameters needed for the function. It should have 'export_dir' and 'input_name' keys.
    img_meta (dict): A dictionary containing the image metadata. It should have 'crs' key.

    Returns:
    None: The function doesn't return anything. It saves the shapefiles in the specified 'export_dir'.
    """
    print("++++++++++++++++++++++++++++++++")
    print("Exporting results to shapefile")
    print("Length of results: " + str(len(results)))
    print("++++++++++++++++++++++++++++++++")
    results_to_poly(results, input, img_meta)
    results_to_pnt(results, input, img_meta)


def get_result(input, save=False, keep_tiff=False, score_thresh=0.5, mt=False, cull_shp=False):
    """
    This function processes an image file, performs object detection on it, and exports the results.

    Parameters:
    input (dict): A dictionary containing various parameters needed for the function.
    save (bool): If True, the visuals of the result will be exported as a JPEG file.
    keep_tiff (bool): If True, the TIFF file will be kept after processing.
    score_thresh (float): The score threshold for the results.
    mt (bool): If True, the function will pause for a certain amount of time if the 'num' value in the 'input' dictionary is less than 5.
    device (str): The device to use for the model ('cpu' or 'cuda:0').
    cull_shp (bool): If True and there are results above the threshold, the results will be exported to a shapefile.

    Returns:
    dict: A dictionary containing various information about the results.
    """
    device = input['device']
    # Initialize the 'geo_file' and 'file_type' variables
    geo_file = True
    file_type = None
    time_dict = {}
    non_sid_files = ['.tif', '.tiff', '.geotiff', '.png', '.jpg', '.jpeg', '.bmp']

    # If the 'mt' flag is set to True, the following block of code will be executed
    if input['mt']:
        # If the 'num' value in the 'input' dictionary is less than 5, the program will pause for a certain amount of time
        # The pause duration is calculated as the 'num' value multiplied by 4/6 seconds
        # This can be useful in scenarios where you want to introduce a delay in the execution of your program
        if input['num'] < input['workers']:
            time.sleep(input['num'] * 2)
            print(f'Paused for {input["num"] * 2} seconds')
    # If the 'input_name' value in the 'input' dictionary ends with '.sid', we decode the SID file to a JPEG file
    # We then get the SID metadata using the 'get_sid_info' function which sets the CRS and resolution of the image
    time_dict['decode_time'] = time.time()
    time_dict['result_time'] = time.time()
    if str(input['input_name']).endswith('.sid'):
        if input['mrsid_exe'] == None:
            print('No MrSID decoder provided')
            geo_file = False
            return

        try:
            jpg_sid = decode_sid(input, input['mrsid_exe'])
        except:
            print('Error decoding sid')
        try:
            img_meta = get_sid_info(input, input['mrsid_exe'])
        except:
            print('Error getting sid info')

        file_type = 'sid'
        time_dict['decode_time'] = time.time() - time_dict['decode_time']

    # If the input file is a valid geotiff file, we get the geotiff metadata using the 'get_geotiff_info' function
    # If the input file is not a valid geotiff file, we open the file in PIL and get the image dimensions
    elif str(input['input_name']).endswith(tuple(non_sid_files)):
        try:
            img_meta = get_geotiff_info(input)
        except:
            print('Error getting geotiff info')
            geo_file = False
            print('Using Blank CRS')
            ## open the file in PIL and get the image dimensions and use them as the geotiff info
            img = Image.open(os.path.join(input['input_dir'], input['input_name']))
            img_meta = {'ul': (0, 0), 'ur': (img.width, 0), 'll': (0, img.height), 'lr': (img.width, img.height),
                        'crs': None, 'res': 1}
            img.Destroy()
            geo_file = False
        time_dict['decode_time'] = time.time() - time_dict['decode_time']
        file_type = str(input['input_name']).split('.')[-1]
    # if the file type is not supported, we set the 'geo_file' variable to False and return
    else:
        print('File type not supported')
        geo_file = False
        return
    # We load the model using the 'AutoDetectionModel' class and the 'from_pretrained' method
    time_dict['model_load_time'] = time.time()
    detection_model = AutoDetectionModel.from_pretrained(
        model_type='yolov8',
        model_path=input['detection_model'],
        confidence_threshold=input['model_confidence_threshold'],
        device=device,  # or 'cuda:0'
    )
    time_dict['model_load_time'] = time.time() - time_dict['model_load_time']

    # We get the sliced prediction using the 'get_sliced_prediction' function from SAHI
    time_dict['detect_time'] = time.time()
    if file_type == 'sid':
        image_file = jpg_sid
    else:
        image_file = os.path.join(input['input_dir'], input['input_name'])
    result = get_sliced_prediction(
        image_file,
        detection_model,
        slice_height=input['slice_height'],
        slice_width=input['slice_width'],
        overlap_height_ratio=input['overlap_height_ratio'],
        overlap_width_ratio=input['overlap_width_ratio']
    )
    time_dict['detect_time'] = time.time() - time_dict['detect_time']
    # If the 'save' flag is set to True, we export the visuals of the result to the 'export_dir' directory as a JPEG file
    if save:
        time_dict['save_time'] = time.time()
        result.export_visuals(export_dir=os.path.join(input['export_dir'], 'out'), hide_labels=True, hide_conf=True,
                              rect_th=1,
                              file_name=os.path.basename(input['input_name'])[0:-4])
        time_dict['save_time'] = time.time() - time_dict['save_time']

    # Process the results
    time_dict['result_process_time'] = time.time()
    result = result.to_coco_annotations()
    ## sort through the results and remove any that are below the score threshold
    above_thresh_result = [x for x in result if x['score'] > score_thresh]

    ## if the cull_shp flag is set to True and there are results above the threshold, we export the results to a shapefile
    if cull_shp and len(above_thresh_result) > 0:
        results_to_shp(above_thresh_result, input, img_meta)
    elif len(result) > 0:
        results_to_shp(result, input, img_meta)
    time_dict['result_process_time'] = time.time() - time_dict['result_process_time']
    ## if the cull_shp flag is set to True and there are results above the threshold, we export the results to a shapefile
    if file_type == 'sid' and keep_tiff == False:
        os.remove(jpg_sid)
    time_dict['result_time'] = time.time() - time_dict['result_time']

    ## Create a dictionary of the results
    ret_dict = {
        'input_name': input['input_name'],
        'total_results': len(result),
        'above_thresh_results': len(above_thresh_result),
        'above_thresh': above_thresh_result,
        'all_results': result,
        'num': input['num'],
        'input_dir': input['input_dir'],
        'export_dir': input['export_dir'],
        'time_dict': time_dict
    }
    return ret_dict


def results_to_dict(results):
    """
    This function takes a list of results and returns a dictionary with the count and confidence scores of each category.

    Parameters:
    results (list): A list of dictionaries. Each dictionary represents a result and should have 'category_name' and 'score' keys.

    Returns:
    dict: A dictionary where each key is a category name from the results. The value is another dictionary with 'count' and 'confidences' keys.
          'count' is the total number of occurrences of the category in the results. 'confidences' is a list of all confidence scores for that category.
    """
    ret_val = {}
    catagories = []
    # Iterate over the results
    for result in results:
        # If the category of the current result is not in the categories list, add it
        if result['category_name'] not in catagories:
            catagories.append(result['category_name'])
            # Initialize the count and confidences list for the new category in the return dictionary
            ret_val[result['category_name']] = {'count': 1, 'confidences': [result['score']]}
        else:
            # If the category is already in the categories list, increment the count and append the score to the confidences list
            ret_val[result['category_name']]['count'] += 1
            ret_val[result['category_name']]['confidences'].append(result['score'])
    return ret_val


def print_prediction_result(result, time_dict, to_process, ave_total, workers):
    print('---------------------------------------------------')
    print(f"Processed {result['input_name']}")
    print('---------------------------------------------------')
    for key in time_dict.keys():
        if key == 'start':
            print("Time From Start: " + f"{key}: {time.time() - time_dict[key]}")
        else:
            print(f"{key}: {time_dict[key]}")
    print('---------------------------------------------------')

    print('Estimated Time Remaining: ' + f'{(ave_total / workers * to_process) / 60} minutes')
    print('---------------------------------------------------')
    elapsed = round((time.time() - time_dict['start']) / 60, 2)
    print('Time Elapsed: ' + f'{elapsed} minutes')
    print('Remaining Files: ' + f'{to_process}')
    print('+++++++++++++++++++++++++++++++++++++++++++++++++++')
