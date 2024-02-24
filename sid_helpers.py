import os
import subprocess


def get_sid_info(input, sid_folder):
    """
    This function retrieves the metadata of a SID file using the provided MrSID info executable.

    Parameters:
    input (dict): A dictionary containing various parameters needed for the function. It should have 'input_dir' and 'input_name' keys.
    sid_info_exe (str): The path to the MrSID info executable.

    Returns:
    dict: A dictionary containing the metadata of the SID file. It includes 'ul' (upper left), 'ur' (upper right), 'll' (lower left), 'lr' (lower right), 'crs' (coordinate reference system), and 'res' (resolution) keys.
    """
    print("++++++++++++++++++++++++++++++++")
    print("Getting SID info on: " + input['input_name'])
    print("++++++++++++++++++++++++++++++++")

    sid_info_exe = os.path.join(sid_folder, 'mrsidinfo.exe')
    arguments = str(os.path.join(input['input_dir'], input['input_name']))
    ret_val = subprocess.check_output([sid_info_exe, '-wkt', arguments])
    crs_lines = []
    collecting_crs = False
    for val in ret_val.decode("utf-8").split('\n'):
        # Extract the upper left, upper right, lower left, and lower right coordinates from the output
        if "upper left" in val:
            ul = tuple(val.split(':')[1].strip().replace('(', '').replace(')', '').split(',')[0:2])
        elif "upper right" in val:
            ur = tuple(val.split(':')[1].strip().replace('(', '').replace(')', '').split(',')[0:2])
        elif "lower left" in val:
            ll = tuple(val.split(':')[1].strip().replace('(', '').replace(')', '').split(',')[0:2])
        elif "lower right" in val:
            lr = tuple(val.split(':')[1].strip().replace('(', '').replace(')', '').split(',')[0:2])
        # Extract the resolution from the output
        elif "X res" in val:
            res = float(val.split(':')[1].strip())
        # Collect the lines that form the WKT string of the CRS
        elif "PROJCS[" in val or collecting_crs:
            crs_lines.append(val)
            collecting_crs = True
            if "]]" in val:
                collecting_crs = False

    # Join the collected CRS lines to form the WKT string
    if crs_lines:
        crs = "\n".join(crs_lines)
    ret_val = {'ul': ul, 'ur': ur, 'll': ll, 'lr': lr, 'crs': crs, 'res': res}
    print("++++++++++++++++++++++++++++++++")
    print("SID info retrieved successfully.")
    print("SID File: " + input['input_name'])
    print("Total Area: " + str((float(lr[0]) - float(ul[0])) * (float(ul[1]) - float(ll[1]))))
    print("++++++++++++++++++++++++++++++++")
    return ret_val


def decode_sid(input, sid_folder):
    """
    This function decodes a SID file to a JPEG file using the provided MrSID decoder executable.

    Parameters:
    mrsid_decoder_path (str): The path to the MrSID decoder executable.
    input (dict): A dictionary containing various parameters needed for the function. It should have 'input_dir', 'input_name', and 'export_dir' keys.

    Returns:
    None: The function doesn't return anything. It saves the decoded JPEG file in the specified 'export_dir'.
    """
    print("++++++++++++++++++++++++++++++++")
    print("Decoding SID: " + input['input_name'])
    print("++++++++++++++++++++++++++++++++")
    mrsid_decoder_path = os.path.join(sid_folder, 'mrsiddecode.exe')
    subprocess.call([mrsid_decoder_path, "-i", os.path.join(input['input_dir'], input['input_name']), "-o",
                     os.path.join(input['export_dir'], os.path.basename(input['input_name'])[0:-4] + '.jpg'), '-of',
                     'jpg', '-quiet'])
    print("++++++++++++++++++++++++++++++++")
    print("SID File Decoded Successfully.")
    print("Decoded File: " + os.path.join(input['export_dir'], os.path.basename(input['input_name'])[0:-4] + '.jpg'))
    print("++++++++++++++++++++++++++++++++")
    return os.path.join(input['export_dir'], os.path.basename(input['input_name'])[0:-4] + '.jpg')
