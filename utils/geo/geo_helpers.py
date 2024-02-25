import math


def convert_wgs_to_utm(lon: float, lat: float):
    """Based on lat and lng, return best utm epsg-code"""
    utm_band = str((math.floor((lon + 180) / 6) % 60) + 1)
    if len(utm_band) == 1:
        utm_band = '0' + utm_band
    if lat >= 0:
        epsg_code = '326' + utm_band
        return epsg_code
    epsg_code = '327' + utm_band
    return epsg_code


def convert_gsd_to_Meters(gsd: float, unit_name: str):
    """Converts the model's GSD to meters"""
    feet = ['ft', 'Feet', 'feet', 'ftUS']
    us_survey_ft = ['us_survey_ft', 'US Survey Feet', 'us_survey_ft', 'US survey foot']
    inches = ['in', 'Inches', 'inches']
    cm = ['cm', 'Centimeters', 'centimeters']
    meters = ['m', 'Meters', 'meters']
    if unit_name in meters:
        return gsd
    elif unit_name in feet:
        return gsd * 0.3048
    elif unit_name in us_survey_ft:
        return gsd * 0.3048006096012192
    elif unit_name in inches:
        return gsd * 0.0254
    elif unit_name in cm:
        return gsd * 0.01
    else:
        return gsd
