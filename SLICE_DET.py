import os

os.environ['PROJ_LIB'] = r"C:\Users\red\anaconda3\envs\pygdal\Library\share\proj"
import concurrent
from multiprocessing import freeze_support
import statistics
import argparse
from utils.helper_functions import *

if __name__ == "__main__":
    freeze_support()
    parser = argparse.ArgumentParser()

    parser.add_argument('--proj_lib', default=r"C:\Users\red\anaconda3\envs\pygdal\Library\share\proj")
    parser.add_argument('--mrsid_decoder_path',
                        default=r"C:\Users\red\ZoeDepth\MrSID_DSDK-9.5.5.5244-win64-vc17\MrSID_DSDK-9.5.5.5244-win64-vc17\Raster_DSDK\bin")
    parser.add_argument('--model_path', default=r"C:\Users\red\ZoeDepth\runs\detect\train19\weights\best.pt")
    parser.add_argument('--objects', nargs='+', default=['Sedan', 'Pickup', 'Other', 'Unknown'])
    parser.add_argument('--model_type', default="yolov8")
    parser.add_argument('--model_device', default='cuda:0')
    parser.add_argument('--model_confidence_threshold', type=float, default=0.4)
    parser.add_argument('--slice_height', type=int, default=512)
    parser.add_argument('--slice_width', type=int, default=512)
    parser.add_argument('--overlap_height_ratio', type=float, default=0.2)
    parser.add_argument('--overlap_width_ratio', type=float, default=0.2)
    parser.add_argument('--source_image_dir', default=r"D:\BRE_TIF\test_tif")
    parser.add_argument('--out_dir', default=r"C:\Users\red\ZoeDepth\BRE2018_OUT")
    parser.add_argument('--workers', type=int, default=4)
    parser.add_argument('--merge', type=bool, default=True)

    args = parser.parse_args()

    merge_shps = args.merge
    os.environ['PROJ_LIB'] = args.proj_lib
    os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'
    mrsid_decoder_path = args.mrsid_decoder_path
    model_path = args.model_path
    objects = args.objects
    model_type = args.model_type
    model_device = args.model_device
    model_confidence_threshold = args.model_confidence_threshold
    slice_height = args.slice_height
    slice_width = args.slice_width
    overlap_height_ratio = args.overlap_height_ratio
    overlap_width_ratio = args.overlap_width_ratio
    source_image_dir = args.source_image_dir
    out_dir = args.out_dir
    workers = args.workers
    sanity_check = True
    acceptable_files = ['.tif', '.tiff', '.geotiff', '.png', '.jpg', '.jpeg', '.bmp', '.sid']
    time_dict = {}
    time_dict['start'] = time.time()
    files = [f for f in os.listdir(source_image_dir) if str(f).endswith(tuple(acceptable_files))]
    list_predict_jobs = []
    num = 0
    # average file size of all files in the directory
    file_size = 0
    for file in files:
        file_size += os.path.getsize(os.path.join(source_image_dir, file))
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
            {'num': num, 'device': model_device, 'mrsid_exe': mrsid_decoder_path, 'detection_model': model_path,
             'model_confidence_threshold': 0.5, 'input_dir': source_image_dir, 'input_name': file,
             'slice_height': slice_height, 'slice_width': slice_width, 'overlap_height_ratio': overlap_height_ratio,
             'overlap_width_ratio': overlap_width_ratio, 'export_dir': out_dir,
             'file_type': ('sid' if file.endswith('.sid') else 'geotiff'), 'mt': mt, 'workers': workers})
        num += 1

    process_times = []
    to_process = len(list_predict_jobs)

    if mt:
        with concurrent.futures.ProcessPoolExecutor(max_workers=workers) as executor:
            execs = executor.map(get_result, list_predict_jobs)
            for exec in execs:
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
