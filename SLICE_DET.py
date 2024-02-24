import os

import yaml

os.environ['PROJ_LIB'] = r"C:\Users\red\anaconda3\envs\pygdal\Library\share\proj"
import concurrent
from multiprocessing import freeze_support
import statistics
import argparse
from utils.helper_functions import *

if __name__ == "__main__":
    freeze_support()
    parser = argparse.ArgumentParser()

    parser.add_argument('--env_yaml', default=r"C:\Users\red\Desktop\SpatialNetForge\enviroment_helper.yaml",
                        help="Path to Enviroment YAML")
    parser.add_argument('--job_yaml', default=r"C:\Users\red\Desktop\SpatialNetForge\job.yaml", help="Path to Job YAML")

    args = parser.parse_args()

    # Load the configuration from the YAML file
    with open(args.env_yaml, 'r') as file:
        env_config = yaml.safe_load(file)
    with open(args.job_yaml, 'r') as file:
        job_config = yaml.safe_load(file)
    # Access the configuration values
    os.environ['PROJ_LIB'] = env_config['proj_lib']
    os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'
    mrsid_decoder_path = env_config['mrsid_decoder_path']
    model_path = job_config['model_path']
    objects = job_config['objects']
    model_type = job_config['model_type']
    model_device = job_config['model_device']
    model_confidence_threshold = job_config['model_confidence_threshold']
    slice_height = job_config['slice_height']
    slice_width = job_config['slice_width']
    overlap_height_ratio = job_config['overlap_height_ratio']
    overlap_width_ratio = job_config['overlap_width_ratio']
    source_image_dir = job_config['source_image_dir']
    out_dir = job_config['out_dir']
    workers = job_config['workers']
    merge_shps = job_config['merge']

    sanity_check = True
    acceptable_files = ['.tif', '.tiff', '.geotiff', '.png', '.jpg', '.jpeg', '.bmp', '.sid']
    sid_memory_adjustment = 64
    tif_memory_adjustment = 3.6
    small_file_adjustment = 64
    time_dict = {}
    time_dict['start'] = time.time()
    files = [f for f in os.listdir(source_image_dir) if str(f).lower().endswith(tuple(acceptable_files))]
    list_predict_jobs = []
    num = 0
    # average file size of all files in the directory
    file_size = 0
    for file in files:
        file_sz = os.path.getsize(os.path.join(source_image_dir, file))
        if str(file).endswith(".sid"):
            file_size += file_sz * sid_memory_adjustment
        elif str(file).lower().endswith(".tiff") or str(file).lower().endswith(".tif") or str(file).lower().endswith(
                "geotiff"):
            file_size += file_sz * tif_memory_adjustment
        else:
            file_size += file_sz * small_file_adjustment
    file_size = file_size / len(files)

    if workers > 1 and sanity_check:
        mt = True
        workers, workers_dict = worker_sanity_check(workers, model_device, model_path, file_size)
    elif workers == 1:
        mt = False
    else:
        mt = True

    if os.path.exists(out_dir):
        pass
    else:
        os.makedirs(out_dir)
    if os.path.exists(os.path.join(out_dir, 'shps', 'polys')):
        pass
    else:
        os.makedirs(os.path.join(out_dir, 'shps', 'polys'))
    if os.path.exists(os.path.join(out_dir, 'shps', 'pnts')):
        pass
    else:
        os.makedirs(os.path.join(out_dir, 'shps', 'pnts'))

    for file in files:
        list_predict_jobs.append(
            {'num': num, 'job_config': job_config, 'env_config': env_config, 'input_name': file,
             'file_type': ('sid' if file.endswith('.sid') else 'geotiff')})
        num += 1

    process_times = []
    to_process = len(list_predict_jobs)

    if mt:
        with concurrent.futures.ProcessPoolExecutor(max_workers=workers) as executor:
            execs = executor.map(get_result, list_predict_jobs)
            for exec in execs:
                if exec != None:
                    if time_dict.get('predict') == None:
                        time_dict['predict_times'] = [exec['time_dict']]
                    else:
                        time_dict['predict_times'].append(exec['time_dict'])
                    time_dict_print = exec['time_dict']
                    time_dict_print['start'] = time_dict['start']
                    to_process -= 1
                    process_times.append(exec['time_dict']['result_time'])
                    ave_total = statistics.median(process_times)
                    if exec['num'] % workers == 0:
                        pass
                    print_prediction_result(exec, time_dict_print, to_process, ave_total, workers)
    else:
        for job in list_predict_jobs:
            exec = get_result(job)
            if exec != None:
                if time_dict.get('predict') == None:
                    time_dict['predict_times'] = [exec['time_dict']]
                else:
                    time_dict['predict_times'].append(exec['time_dict'])
                time_dict_print = exec['time_dict']
                time_dict_print['start'] = time_dict['start']
                to_process -= 1
                process_times.append(exec['time_dict']['result_time'])
                ave_total = statistics.median(process_times)
                print_prediction_result(exec, time_dict_print, to_process, ave_total, workers)
    if merge_shps:
        poly_shps = [f for f in os.listdir(os.path.join(out_dir, 'shps', 'polys')) if f.endswith('.shp')]
        act_poly_shps = []
        for poly_shp in poly_shps:
            act_poly_shps.append(os.path.join(os.path.join(out_dir, 'shps', 'polys'), poly_shp))

        act_pnt_shps = []
        pnt_shps = [f for f in os.listdir(os.path.join(out_dir, 'shps', 'pnts')) if f.endswith('.shp')]
        for pnt_shp in pnt_shps:
            act_pnt_shps.append(os.path.join(os.path.join(out_dir, 'shps', 'pnts'), pnt_shp))
        merge_shapefiles(act_poly_shps, os.path.join(out_dir, 'shps', 'polys_merged.shp'))
        merge_shapefiles(act_pnt_shps, os.path.join(out_dir, 'shps', 'pnts_merged.shp'))
