import os

import osgeo.gdal as gdal
import osgeo.ogr as ogr
import osgeo.osr as osr


def results_to_poly(results, input, img_meta, layer_name='Layer', driver_name='ESRI Shapefile'):
    """
    This function exports the results to a polygon shapefile.

    Parameters:
    results (list): A list of dictionaries. Each dictionary represents a result and should have 'bbox', 'category_name', and 'score' keys.
    input (dict): A dictionary containing various parameters needed for the function. It should have 'export_dir' and 'input_name' keys.
    img_meta (dict): A dictionary containing the image metadata. It should have 'crs' key.
    layer_name (str): The name of the layer to be created in the shapefile.
    driver_name (str): The name of the driver to be used for creating the shapefile.

    Returns:
    None: The function doesn't return anything. It saves the polygon shapefile in the specified 'export_dir'.
    """
    print("++++++++++++++++++++++++++++++++")
    print("Exporting Result: " + input['input_name'] + " to Polygons")
    print("++++++++++++++++++++++++++++++++")
    # Get the ESRI Shapefile driver
    driver = ogr.GetDriverByName(driver_name)
    # Create a new data source and a new layer
    ds = driver.CreateDataSource(
        os.path.join(input['export_dir'], 'shps', 'polys', input['input_name'][:-4] + '_poly' + '.shp'))
    srs = osr.SpatialReference()
    # Set the spatial reference system of the layer to the CRS of the image
    if input['file_type'] == 'sid':
        srs.ImportFromWkt(img_meta['crs'])
    else:
        srs.ImportFromWkt(img_meta['crs'])
    if ds.GetLayer(layer_name):
        print(f"Layer {layer_name} already exists.")
    else:
        # Check if the spatial reference system is defined
        if srs is None:
            print("The spatial reference system is not defined.")
        else:
            try:
                # Try to create the layer
                layer = ds.CreateLayer(layer_name, srs, ogr.wkbPolygon)
            except Exception as e:
                print(f"Failed to create layer. Error: {e}")
    # Create a new field for the category name
    field_name = ogr.FieldDefn("Catagory", ogr.OFTString)
    field_name.SetWidth(24)
    layer.CreateField(field_name)
    # Create a new field for the confidence score
    conf_layer = ogr.FieldDefn("Confidence", ogr.OFTReal)
    conf_layer.SetWidth(6)
    conf_layer.SetPrecision(3)
    layer.CreateField(conf_layer)
    # Iterate over the results
    for result in results:
        try:
            # Calculate the corners of the bounding box
            bbox = result['bbox']
            geom = ogr.Geometry(ogr.wkbLinearRing)
            x1, y1 = pixel(img_meta, bbox[0], bbox[1])
            x2, y2 = pixel(img_meta, bbox[0] + bbox[2], bbox[1])
            x3, y3 = pixel(img_meta, bbox[0] + bbox[2], bbox[1] + bbox[3])
            x4, y4 = pixel(img_meta, bbox[0], bbox[1] + bbox[3])
            # Add the corners to the geometry
            geom.AddPoint(x1, y1)
            geom.AddPoint(x2, y2)
            geom.AddPoint(x3, y3)
            geom.AddPoint(x4, y4)
            geom.AddPoint(x1, y1)
            # Create a new feature
            feature = ogr.Feature(layer.GetLayerDefn())
            if not feature:
                print("Failed to create feature for result:", result)
                continue
            # Create a polygon geometry and add the linear ring to it
            poly = ogr.Geometry(ogr.wkbPolygon)
            poly.AddGeometry(geom)
            # Set the geometry and fields of the feature
            feature.SetGeometry(poly)
            feature.SetField("Catagory", result['category_name'])
            feature.SetField("Confidence", float(result['score']))
            # Add the feature to the layer
            if layer.CreateFeature(feature) != 0:
                print("Failed to create feature on layer for result")
            feature.Destroy()
        except Exception as e:
            print("Failed to create feature on layer for result:", result, e)
            if feature != None:
                feature.Destroy()

    print("++++++++++++++++++++++++++++++++")
    print("Result: " + input['input_name'] + " exported to Polygons successfully.")
    print("Number of Polygons: " + str(len(layer)))
    print("++++++++++++++++++++++++++++++++")
    # Destroy the data source to flush to disk
    ds.Destroy()
    return


def get_geotiff_info(input):
    """
    This function retrieves the metadata of a GeoTIFF file using the GDAL library.

    Parameters:
    input (dict): A dictionary containing various parameters needed for the function. It should have 'input_dir' and 'input_name' keys.

    Returns:
    dict: A dictionary containing the metadata of the GeoTIFF file. It includes 'ul' (upper left), 'ur' (upper right), 'll' (lower left), 'lr' (lower right), 'crs' (coordinate reference system), and 'res' (resolution) keys.
    """
    print('++++++++++++++++++++++++++++++++')
    print('Getting GeoTIFF info on: ' + input['input_name'])
    print('++++++++++++++++++++++++++++++++')
    # Open the GeoTIFF file using GDAL
    ds = gdal.Open(os.path.join(input['input_dir'], input['input_name']), gdal.GA_ReadOnly)
    # Get the geotransform of the GeoTIFF file
    gt = ds.GetGeoTransform()
    # Get the projection of the GeoTIFF file
    proj = ds.GetProjection()
    # Calculate the upper left, upper right, lower left, and lower right coordinates using the geotransform
    ul = (gt[0], gt[3])
    ur = (gt[0] + ds.RasterXSize * gt[1], gt[3])
    ll = (gt[0], gt[3] + ds.RasterYSize * gt[5])
    lr = (gt[0] + ds.RasterXSize * gt[1], gt[3] + ds.RasterYSize * gt[5])
    # Get the coordinate reference system and resolution from the geotransform
    crs = proj
    res = gt[1]
    # Create a dictionary with the metadata
    ret_val = {'ul': ul, 'ur': ur, 'll': ll, 'lr': lr, 'crs': crs, 'res': res}
    # Close the GeoTIFF file
    ds = None
    print('++++++++++++++++++++++++++++++++')
    print('GeoTIFF info retrieved successfully.')
    print('GeoTiff File: ' + input['input_name'])
    print("Total Area: " + str((float(lr[0]) - float(ul[0])) * (float(ul[1]) - float(ll[1]))))
    print('++++++++++++++++++++++++++++++++')

    return ret_val


def results_to_pnt(results, input, img_meta, layer_name='Layer', driver_name='ESRI Shapefile'):
    """
    This function exports the results to a point shapefile.

    Parameters:
    results (list): A list of dictionaries. Each dictionary represents a result and should have 'bbox', 'category_name', and 'score' keys.
    input (dict): A dictionary containing various parameters needed for the function. It should have 'export_dir' and 'input_name' keys.
    img_meta (dict): A dictionary containing the image metadata. It should have 'crs' key.
    layer_name (str): The name of the layer to be created in the shapefile.
    driver_name (str): The name of the driver to be used for creating the shapefile.

    Returns:
    None: The function doesn't return anything. It saves the point shapefile in the specified 'export_dir'.
    """
    print('++++++++++++++++++++++++++++++++')
    print('Exporting Result: ' + input['input_name'] + ' to Points')
    print('++++++++++++++++++++++++++++++++')
    # Get the ESRI Shapefile driver
    driver = ogr.GetDriverByName(driver_name)
    # Create a new data source and a new layer
    ds = driver.CreateDataSource(
        os.path.join(input['export_dir'], 'shps', 'pnts', input['input_name'][:-4] + '_pnts' + '.shp'))
    srs = osr.SpatialReference()
    # Set the spatial reference system of the layer to the CRS of the image
    if input['file_type'] == 'sid':
        srs.ImportFromWkt(img_meta['crs'])
    else:
        srs.ImportFromWkt(img_meta['crs'])
    layer = ds.CreateLayer(layer_name, srs, ogr.wkbPoint)
    # Create a new field for the category name
    field_name = ogr.FieldDefn("Catagory", ogr.OFTString)
    field_name.SetWidth(64)
    layer.CreateField(field_name)
    # Create a new field for the confidence score
    conf_layer = ogr.FieldDefn("Confidence", ogr.OFTReal)
    conf_layer.SetWidth(6)
    conf_layer.SetPrecision(3)
    layer.CreateField(conf_layer)
    # Iterate over the results
    for result in results:
        try:
            # Calculate the center of the bounding box
            bbox = result['bbox']
            center = (bbox[0] + bbox[2] / 2, bbox[1] + bbox[3] / 2)
            # Create a new point geometry
            geom = ogr.Geometry(ogr.wkbPoint)
            # Calculate the geographical coordinates of the center of the bounding box
            x1, y1 = pixel(img_meta, center[0], center[1])
            geom.AddPoint(x1, y1)
            # Create a new feature
            feature = ogr.Feature(layer.GetLayerDefn())
            feature.SetGeometry(geom)
            # Set the category name and confidence score of the feature
            feature.SetField("Catagory", result['category_name'])
            feature.SetField("Confidence", float(result['score']))
            # Add the feature to the layer
            if layer.CreateFeature(feature) != 0:
                print("Failed to create feature on layer for result:", result)
            feature.Destroy()
        except Exception as e:
            print("Failed to create feature on layer for result:", result, e)
            if feature != None:
                feature.Destroy()

    # Destroy the data source to flush to disk

    print('++++++++++++++++++++++++++++++++')
    print('Number of Points: ' + str(len(layer)))
    print('Result: ' + str(input['input_name']) + ' exported to Points successfully.')
    print('=' * 32)
    ds.Destroy()
    return


def pixel(img_meta, dx, dy):
    """
    This function calculates the geographical coordinates (x, y) for a given pixel (dx, dy) in the image.
    It uses the image metadata (img_meta) which contains the upper left coordinates (ul) and the resolution (res) of the image.

    Parameters:
    img_meta (dict): A dictionary containing the image metadata. It should have 'ul' and 'res' keys.
    dx (int): The x-coordinate of the pixel in the image.
    dy (int): The y-coordinate of the pixel in the image.

    Returns:
    tuple: A tuple containing the geographical coordinates (x, y) corresponding to the given pixel.
    """
    # Extract the upper left x and y coordinates from the image metadata
    px = float(img_meta['ul'][0])
    py = float(img_meta['ul'][1])

    # Extract the resolution in x and y directions from the image metadata
    rx = float(img_meta['res'])
    ry = float(img_meta['res'])

    # Calculate the geographical coordinates for the given pixel
    x = dx * rx + px
    y = py - dy * ry

    return x, y
