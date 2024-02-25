from ..geo.geo_helpers import *


def resize_calculator(img_res, img_sr, input):
    img_gsd = convert_gsd_to_Meters(img_res, img_sr.GetLinearUnitsName())
    job_config = input['job_config']
    job_model_gsd = convert_gsd_to_Meters(job_config['model_gsd'], job_config['model_gsd_unit'])
    resize_factor = img_gsd / job_model_gsd
    if resize_factor < 1:
        test = 1 - resize_factor
        if test > job_config['model_gsd_accuracy']:
            resize_factor = resize_factor
        else:
            resize_factor = 1
    elif resize_factor > 1:
        test = resize_factor - 1
        if test > job_config['model_gsd_accuracy']:
            resize_factor = resize_factor
        else:
            resize_factor = 1
    return resize_factor, img_gsd, job_model_gsd
