import numpy as np
import os
#from osgeo import gdal
from osgeo import gdal
from osgeo import ogr
from osgeo import osr
import subprocess

# this allows GDAL to throw Python Exceptions
gdal.UseExceptions()

# Dépendance : 'gdal_polygonize.exe', 'gdal_calc.exe', 'gdaltindex.exe'


def polygonize_raster_gdal(p_input: str, p_output: str, p_simplified: bool = False, p_path: str = '') -> str:
    """
    Méthode permettant de générer un vecteur à partir d'un raster.
    https://gdal.org/programs/gdal_polygonize.html

    :param p_input: (str) Un fichier raster.
    :param p_output: (str) Le chemin du fichier vectoriel de sortie.
    :param p_simplified: (bool) True pour limiter le nombre de polygone, False sinon.
    :param p_path: (str) Le chemin de la dépendance 'gdal_polygonize.exe'.
    :return: (str) Le chemin du fichier de sortie.
    :raise: ValueError lorsque le fichier est inexistant.
    """
    path, file = os.path.split(p_input)[0], os.path.splitext(os.path.split(p_input)[1])[0]
    tmp = os.path.join(path, "{}_Rsimplified.tiff".format(file))

    if not os.path.exists(p_input):
        raise ValueError('Fichier raster inexistant.')

    shp_driver = ogr.GetDriverByName('ESRI Shapefile')
    if os.path.exists(p_output):
        shp_driver.DeleteDataSource(p_output)

    if p_simplified:
        p_input = create_binary_raster_gdal(p_input, tmp, p_path=p_path)

    cmdline = [os.path.join(p_path, 'gdal_polygonize.exe'),
               p_input,
               p_output,
               '-q']

    subprocess.call(cmdline, creationflags=0x08000000)

    if os.path.exists(tmp):
        os.remove(tmp)

    return p_output


def create_binary_raster_gdal(p_input: str, p_output: str,  p_path: str = '') -> str:
    """
    Méthode permettant d'attribuer, pour un raster provenant d'une surface bathymétrique .csar,
     la valeur de 1 s'il y a une valeur de profondeur, 0 pour nodata.
     https://gdal.org/programs/gdal_calc.html

    :param p_input: (str) Un fichier raster.
    :param p_output: (str) Le chemin du fichier raster de sortie.
    :param p_path: (str) Le chemin de la dépendance 'gdal_calc.exe'.
    :return (str) Le chemin du fichier de sortie.
    :raise: ValueError lorsque le fichier est inexistant.
    """
    if not os.path.exists(p_input):
        raise ValueError('Fichier raster inexistant.')

    gtiff_driver = gdal.GetDriverByName('Gtiff')
    if os.path.exists(p_output):
        gtiff_driver.Delete(p_output)

    cmdline = [os.path.join(p_path, 'gdal_calc.exe'),
               '-A', p_input,
               '--outfile', p_output,
               '--calc=1*(A<10000)',
               '--NoDataValue=0',
               '--quiet']

    subprocess.call(cmdline, creationflags=0x08000000)

    return p_output


def create_tile_index(p_input: str, p_output: str,  p_path: str = '') -> str:
    """
    Méthode permettant de créer un rectangle encadrant le fichier raster.
    https://gdal.org/programs/gdaltindex.html

    :param p_input: (str) Un fichier raster.
    :param p_output: (str) Le chemin du fichier vectoriel de sortie.
    :param p_path: (str) Le chemin de la dépendance 'gdaltindex.exe'.
    :return: (str) Le chemin du fichier de sortie.
    :raise: ValueError lorsque le fichier est inexistant.
    """
    if not os.path.exists(p_input):
        raise ValueError('Fichier raster inexistant.')

    shp_driver = ogr.GetDriverByName('ESRI Shapefile')
    if os.path.exists(p_output):
        shp_driver.DeleteDataSource(p_output)

    cmdline = [os.path.join(p_path, 'gdaltindex.exe'),
               p_output,
               p_input]
    subprocess.call(cmdline, creationflags=0x08000000)

    return p_output


def create_contour(p_input, p_output, p_isobathe='1000'):
    """
    Méthode permettant de créer des polygones représentant les isobathes du fichier raster.
    https://gdal.org/programs/gdal_contour.html

    :param p_input: (str) Un fichier raster.
    :param p_output: (str) Le chemin du fichier vectoriel de sortie.
    :param p_isobathe: (str) L'écart désiré entre les isobathe.
    :return: (str) Le chemin du fichier de sortie.
    :raise: ValueError lorsque le fichier est inexistant.
    """
    if not os.path.exists(p_input) and p_input != '':
        raise ValueError('Fichier raster inexistant.')

    shp_driver = ogr.GetDriverByName('ESRI Shapefile')
    if os.path.exists(p_output):
        shp_driver.DeleteDataSource(p_output)

    cmdline = ['gdal_contour.exe',
               p_input,
               p_output,
               '-i', p_isobathe,
               '-p']
    subprocess.call(cmdline, creationflags=0x08000000)

    return p_output


def from_object_to_gdal_dataset(p_input: str):
    """
    Méthode permettant d'ouvrir un fichier raster et de retourner un objet Dataset.

    :param p_input: (str) Un fichier dans un format supporté par gdal, un objet de Dataset.
    :return: Un objet de type Dataset de gdal.
    :raise: ValueError lorsque le fichier est inexistant.
    """
    if isinstance(p_input, str):
        if not os.path.exists(p_input):
            raise ValueError('Fichier inexistant.')
        return gdal.Open(p_input)

    elif isinstance(p_input, gdal.Dataset):
        return p_input


def translate(p_input, p_xres=0.0, p_yres=0.0, p_width=0.0, p_height=0.0, p_output='', p_driver='MEM',
              p_resample="bilinear", p_binary=False):
    """
    Méthode permettant de rééchantillonner le raster afin de modififier sa résolution.
    https://gdal.org/programs/gdal_translate.html

    :param p_input: (str | osgeo.gdal.Dataset) Un fichier raster ou un objet Dataset.
    :param p_xres: (float) La résolution en x d'un pixel. p_xres ne peut-être combiné à p_width.
    :param p_yres: (float) La résolution en y d'un pixel. p_yres ne peut-être combiné à p_height.
    :param p_width: (float) Largeur des pixels en pourcentage (100 = largeur initiale).
                            p_width ne peut-être combiné à p_xres.
    :param p_height: (float) Hauteur des pixels en pourcentage (100 = hauteur initiale).
                             p_height ne peut-être combiné à p_yres.
    :param p_binary: (bool) True pour modifier les valeurs de pixel en 1 et -9999, False sinon. 1 représente
                            la présence d'une valeur et -9999 no_data_value.
    :param p_output: (str) Le nom du fichier de sortie. Utiliser '' comme paramètre pour le driver 'MEM'.
    :param p_driver: (str) Le format du fichier résultant.
    :param p_resample: (str) L'algorithmeré de rééchantillonnage utilisée.
    :return: (str | osgeo.gdal.Dataset) Le chemin du fichier de sortie ou un objet Dataset.
    :raise: ValueError lorsque le fichier est inexistant.
    """
    dataset = from_object_to_gdal_dataset(p_input)

    no_data_value = None
    scale = None
    if p_binary:
        no_data_value = -9999
        scale = [[0, 0, 1, 1]]

    translated = gdal.Translate(p_output, dataset, format=p_driver, resampleAlg=p_resample, xRes=p_xres, yRes=p_yres,
                                projWinSRS=dataset.GetProjection(), widthPct=p_width, heightPct=p_height,
                                noData=no_data_value, scaleParams=scale)

    return translated if p_output == '' else p_output


def calc_binary(p_input, p_output='', p_band=1, p_max_value=10000, p_no_data_value=-9999, p_driver='MEM'):
    """
   Méthode permettant de créer un raster binaire. Valeur de 1 ou de no_data_value.

   :param p_input: (str | osgeo.gdal.Dataset) Un fichier raster ou un objet Dataset.
   :param p_output: (str) Le nom du fichier de sortie. Utiliser '' comme paramètre pour le driver 'MEM'.
   :param p_band: (int) La bande du raster.
   :param p_max_value: (int) La valeur maximale acceptable.
   :param p_no_data_value: (int) La valeur pour les pixel sans données.
   :param p_driver: (str) Le format du fichier résultant.
   :return: (str | osgeo.gdal.Dataset) Le chemin du fichier de sortie ou un objet Dataset.
   :raise: ValueError lorsque le fichier est inexistant.
   """
    # Ouverture d'objet Dataset à partir d'un fichier raster et lecture de la bande dans un numpy array.
    dataset = from_object_to_gdal_dataset(p_input)
    band = dataset.GetRasterBand(p_band)
    array = band.ReadAsArray()

    # Filtre sur le numpy array. Les valeurs inférieures à la valeur maximale prennent
    # la valeur de 1, sinon, la valeur de no_data_value.
    [cols, rows] = array.shape
    array_calc = np.where((array <= p_max_value), 1, p_no_data_value)

    # Écriture du fichier avec le numpy array filtré.
    driver = gdal.GetDriverByName(p_driver)
    data_calc = driver.Create(p_output, rows, cols, 1, gdal.GDT_UInt16)
    data_calc.SetGeoTransform(dataset.GetGeoTransform())
    data_calc.SetProjection(dataset.GetProjection())
    data_calc.GetRasterBand(p_band).WriteArray(array_calc)
    data_calc.GetRasterBand(p_band).SetNoDataValue(-p_no_data_value)

    return data_calc if p_output == '' else p_output


def raster_to_vector(p_input, p_output='', p_band=1, p_driver='Memory', p_mask=True):
    """
    Méthode permettant de vectoriser les pixels de même valeur d'un raster.

   :param p_input: (str | osgeo.gdal.Dataset) Un fichier raster ou un objet Dataset.
   :param p_output: (str) Le nom du fichier de sortie. Utiliser '' comme paramètre pour le driver 'MEM'.
   :param p_band: (int) La bande du raster.
   :param p_driver: (str) Le format du fichier résultant.
   :param p_mask: (bool) True pour appliquer un masque sur les no_data_value, False sinon.
   :return: (str | osgeo.gdal.Dataset) Le chemin du fichier de sortie ou un objet Dataset.
   :raise: ValueError lorsque le fichier est inexistant.
    """
    dataset = from_object_to_gdal_dataset(p_input)
    mask = dataset.GetRasterBand(p_band) if p_mask else None

    src = osr.SpatialReference()
    src.ImportFromWkt(dataset.GetProjection())

    driver = ogr.GetDriverByName(p_driver)
    vectorized = driver.CreateDataSource(p_output)

    layer = vectorized.CreateLayer("polygonized", srs=src)
    field = ogr.FieldDefn('Bounding', ogr.OFTInteger)
    layer.CreateField(field)

    gdal.Polygonize(dataset.GetRasterBand(p_band), mask, layer, 0, [], callback=None)

    return vectorized if p_output == '' else p_output


if __name__ == '__main__':
    try:
        from chs_lib import vector_utils as vu
        from chs_lib import chs_utils as chsu
        import chs_lib.caris_api.coverage_utils as cu
    except ImportError:
        import vector_utils as vu
        import lib as chsu

    print(chsu.get_time_local())

    csar = r'D:\HDCS_Data\BDBTest\4013962_ShiftedtoPACD_Central.csar'
    coverage = r'D:\HDCS_Data\BDBTest\geotiff.tiff'
    coverage_resampled = r'D:\HDCS_Data\BDBTest\resampled.tiff'
    coverage_calculated = r'D:\HDCS_Data\BDBTest\calculated.tiff'
    coverage_shp = r'D:\HDCS_Data\BDBTest\polygonized.shp'
    wkt_file = r'D:\HDCS_Data\BDBTest\Bounding_resampled.wkt'
    bound_shp = r'D:\HDCS_Data\BDBTest\Bounding_resampled.shp'

    gtiff = gdal.Open(coverage)
    band = gtiff.GetRasterBand(1)
    array = band.ReadAsArray()
    print(array)
    print(chsu.get_time_local())
    input('pause')

    print(chsu.get_time_local(), 'Opening Gtiff')
    gtiff = gdal.Open(coverage)
    epsg = gtiff.GetProjection()
    gt = gtiff.GetGeoTransform()
    pixelSizeX = gt[1]
    pixelSizeY = -gt[5]
    print(pixelSizeX, pixelSizeY)
    print(gtiff.RasterXSize, gtiff.RasterYSize, gtiff.RasterXSize * gtiff.RasterYSize)

    resample = 20  # Ex: 20 % = 5 x la résolution initiale
    res = pixelSizeX * 15

    print(chsu.get_time_local(), 'Resampling')
    ds_translated = translate(
        gtiff, p_width=resample, p_height=resample, p_binary=True)  # , p_output=coverage_resampled, p_driver='Gtiff')
    # trans = gdal.Open(ds_translated)
    gt = ds_translated.GetGeoTransform()
    pixelSizeX = gt[1]
    pixelSizeY = -gt[5]
    print(pixelSizeX, pixelSizeY)
    print(ds_translated.RasterXSize, ds_translated.RasterYSize, ds_translated.RasterXSize * ds_translated.RasterYSize)

    # print(chsu.get_time_local(), 'Recalculating')
    # calc = calc_binary(ds_translated, p_output=coverage_calculated, p_driver='Gtiff')
    # # ds_translated.FlushCache()
    # ds_translated = None

    print(chsu.get_time_local(), 'Polygonize')
    vector = raster_to_vector(ds_translated, p_output=coverage_shp, p_driver='ESRI Shapefile')
    ds_translated.FlushCache()
    ds_translated = None
    # calc.FlushCache()
    # calc = None

    result = vu.from_object_to_geodataframe(vector)
    vector = None

    print(chsu.get_time_local(), 'Buffered')
    result = vu.create_buffer(result, res, p_join_style=2)
    print(chsu.get_time_local(), 'Union')
    result = vu.unary_union(result)
    print(chsu.get_time_local(), 'Simplify')
    result = vu.simplify_geometry(result, res * 0.95)
    # try:
    #     result = vu.dissolve_inner_ring(result)  # , p_area=100)
    # except ValueError:
    #     from shapely import speedups
    #     speedups.disable()
    #     result = vu.dissolve_inner_ring(result)  # , p_area=100)

    wkt = vu.get_wkt_from_object(result, p_type='string')
    vu.write_file('{}\n{}\n'.format(epsg, wkt), wkt_file)
    vu.from_geopandas_to_file(result, bound_shp, p_epsg=epsg)
    nb_poly, nb_point = vu.get_count_poly_points(result)
    print('-------------------------------------------------------')
    print("Le Bounding Polygon compte {} polygone(s) et un total de {} sommets.".format(nb_poly, nb_point))
    print(chsu.get_time_local())




