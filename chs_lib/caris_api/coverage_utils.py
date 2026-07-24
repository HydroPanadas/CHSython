import dateutil.parser as dup
import datetime
from lxml import etree as et
import numpy as np
import os
import re
from typing import List, Iterable

# Option pour l'importation des modules avec un fichier global de configuration.
from chs_lib.caris_api.caris_api_facade import caris, cov

# Sinon il est possible d'utiliser
# python_env = r'C:\Program Files\CARIS\BASE Editor\5.5\python\3.7' -> Chemin vers les librairies de Caris
# import sys
# sys.path.insert(0, python_env)
# import caris
# import caris.caverage as coverage


gmi = "{http://www.isotc211.org/2005/gmi}"
gmd = "{http://www.isotc211.org/2005/gmd}"
xsi = "{http://www.w3.org/2001/XMLSchema-instance}"
gml = "{http://www.opengis.net/gml/3.2}"
gco = "{http://www.isotc211.org/2005/gco}"
xlink = "{http://www.w3.org/1999/xlink}"

ZONE_EXTENTS = {
    4: (-60, -63),
    5: (-63, -66),
    6: (-66, -69),
    7: (-69, -72),
    8: (-72, -75),
    9: (-75, -78)
}

EPSG_ZONE_MTM = {
    '32183': 3,
    '32184': 4,
    '32185': 5,
    '32186': 6,
    '32187': 7,
    '32188': 8,
    '32189': 9,
}


def delete_csar(csar_path):
    """
    Delete a csar file and its associated csar0 file
    if it is not locked for editing.

    :param csar_path: (str) Path to csar file to delete
    :raise: IOError Thrown when .csar file is locked for editing.
    """
    if os.path.exists(csar_path + ".lock"):
        raise IOError
    if os.path.exists(csar_path):
        os.remove(csar_path)
    if os.path.exists(csar_path + "0"):
        os.remove(csar_path + "0")


def copy_csar(file, output):
    """
    Copies a csar file and its associated csar0 file from source_path to destination_path if the
    csar file at the destination is not locked for editing.

    :param file: (str) Path to csar file to copy
    :param output: (str) Destination path for copied csar file
    """
    delete_csar(output)
    coverage = get_coverage(file)
    coverage.create_copy(output)


def get_coverage(coverage, write=False):
    """
    Open a coverage if coverage is a path, otherwise return the coverage. Optionally open coverage
    for writing.

    :param coverage: (str) A csar file
    :param write: (bool) Open coverage from writing if True
    :return: Opened Cloud, Raster, or VRS object
    """
    if isinstance(coverage, str):
        if not write:
            coverage = caris.open(file_name=coverage)
        else:
            coverage = caris.open(file_name=coverage, open_mode=caris.OpenMode.READ_WRITE)

    return coverage


def list_bands(coverage: str) -> list:
    """
    Print band names of a Cloud, Raster, or VRS object.

    :param coverage: (str) Coverage object or a path to one.
    :return: (list) Liste contenant le nom des couches.
    """
    return [band_name for band_name in get_coverage(coverage).band_info]


def remove_band(coverage: str, bands: Iterable = None, to_removed: bool = True) -> None:
    """
    Méthode permettant de supprimer des couches d'un fichier csar.

    :param coverage: (str ou un object Coverage) Le chemin d'un fichier csar ou un objet Caris.Coverage.
    :param bands: (list(str)) Une liste contenant le nom des couches à traiter.
    :param to_removed: (bool) True pour enlever les couches contenues dans band, False pour les garder et
                                supprimer toutes les couches qui ne sont pas dans band.
    """
    coverage = get_coverage(coverage, write=True)
    list_bands_ = list_bands(coverage)

    if to_removed:
        for band in bands:
            if band in list_bands_ and band != 'Depth':
                coverage.remove_band(band)
    else:
        for band in list_bands_:
            if band not in bands and band != 'Depth':
                coverage.remove_band(band)


def get_numpy_array_raster(coverage, band_name='Depth'):
    """
    Reads block sized chunks of raster data.

    :param coverage: (Raster) raster file to read data from
    :param band_name: (str) name of band to read data from
    :returns: (numpyarray)
    """
    if get_coverage_type(coverage) == 'raster':
        raster = get_coverage(coverage)
        data = raster.read_narray(band_name=band_name, area=((0, 0), raster.dims))

        return data


def iterate_raster_blocks(coverage, band_name='Depth', block_size=None):
    """
    Reads block sized chunks of raster data.

    :param coverage: (Raster) raster file to read data from
    :param band_name: (str) name of band to read data from
    :param block_size: (int, int) size of blocks to read at once,
                               if None recommended block size is used
    :returns: (block data, area of block)
    """
    if get_coverage_type(coverage) == 'raster':
        raster = get_coverage(coverage)
        if block_size is None:
            block_size = raster.block_size
        for x in range(0, raster.dims[0], block_size[0]):
            for y in range(0, raster.dims[1], block_size[1]):
                area = ((x, y), (x + block_size[0], y + block_size[1]))
                data = raster.read_np_array(band_name, area)

                yield data, area


def iterate_raster_blocks_(coverage, band_name='Depth', block_size=None):
    """
    Reads block sized chunks of raster data.

    :param coverage: (Raster) raster file to read data from
    :param band_name: (str) name of band to read data from
    :param block_size: (int, int) size of blocks to read at once,
                               if None recommended block size is used
    :returns: (block data, area of block)
    """
    if get_coverage_type(coverage) == 'raster':
        raster = get_coverage(coverage)
        if block_size is None:
            block_size = raster.block_size
        for x in range(0, raster.dims[0], block_size[0]):
            for y in range(0, raster.dims[1], block_size[1]):
                area = ((x, y), (x + block_size[0], y + block_size[1]))
                data = raster.read(band_name, area)

                yield data, area


def get_numpy_array_cloud(coverage, band_name='Depth'):
    """
    Reads array of cloud data.

    :param coverage: (Cloud) Cloud file to read data from.
    :param band_name: (str) Name of band to read data from.

    :return: (numpy.array))
    """
    if get_coverage_type(coverage) == 'cloud':
        cloud = get_coverage(coverage)

        array = None
        for index, block in enumerate(cloud):
            if index == 0:
                array = block[band_name]
            else:
                array = np.vstack((array, block[band_name]))

        return array


def iterate_cloud_blocks(coverage, band_name='Depth'):
    """
    Reads block sized chunks of cloud data.

    :param coverage: (Cloud) Cloud file to read data from.
    :param band_name: (str) Name of band to read data from.

    :return: list() Block of data
    """
    if get_coverage_type(coverage) == 'cloud':
        cloud = get_coverage(coverage)

        points = []
        for block in cloud:
            for pt in block[band_name]:
                points.append(pt)

        return points


def get_xml(coverage, export=False, destination_path='coverage.xml'):
    """
    Reads and return the xml string of the coverage object.

    :param coverage: (obj) Cloud, Raster, or VRS object or a path to one
    :param export: (bool) Save the xml file if True
    :param destination_path: (str) Destination path for xml file

    :return: (obj) A Element etree object

    """
    xml = get_coverage(coverage).iso19139_xml
    root = et.fromstring(xml)

    if export:
        with open(destination_path, 'wb') as output_xml:
            output_xml.write(et.tostring(root, xml_declaration=True,  pretty_print=True))

    return root


def get_resolution(coverage):
    """
    Reads the xml string from a coverage file and return the resolution.

    :param coverage: (obj) Cloud, Raster, or VRS object or a path to one
    :return: Coverage's resolution (resolution (str), unit (str))
    """
    resolution_list = []
    root = get_xml(coverage)

    if get_coverage_type(coverage) == 'raster':
        for resolutions in root.iter('{}Measure'.format(gco)):
            resolution_list.append((resolutions.text, resolutions.attrib['uom']))
        if resolution_list[0][0] != resolution_list[1][0]:
            return resolution_list[-1]  # todo à vérifer

        return resolution_list[0]


def get_cosys_wkt_vcosys(coverage):
    """
    Reads a coverage object and return the vertical coordinate system WKT.

    :param coverage: (obj) Cloud, Raster, or VRS object or a path to one.
    :return: WKT of the VCS.
    """
    root = get_xml(coverage)
    wkt = None

    for string in root.iter('{}CharacterString'.format(gco)):
        if string.text is not None:
            if string.text.startswith('VERT_CS'):
                wkt = string.text

    return wkt


def get_cosys_wkt(coverage, vert_cosys=False):
    """
    Reads a coverage object and return the coordinate system WKT.

    :param coverage: (obj) Cloud, Raster, or VRS object or a path to one.
    :param vert_cosys: (bool) True for the vertical cosys WKT, False for the cosys WKT.
    :return: WKT of the CS
    """
    wkt = None

    if vert_cosys:
        wkt = get_cosys_wkt_vcosys(coverage)

    else:
        wkt_cosys = get_coverage(coverage).wkt_cosys

        if wkt_cosys.startswith('PROJCS') or wkt_cosys.startswith('GEOGCS'):
            wkt = wkt_cosys
        elif wkt_cosys.startswith('COMPD_CS'):
            wkt = '\n'.join(
                line.strip() for line in wkt_cosys.split('VERT_CS')[0].split('\n')[1:]
            ).strip().strip(',')

    return wkt


def get_cosys(coverage, return_type='epsg'):
    """
    Reads a coverage object and return the coordinate system EPSG.
    :param coverage: (obj) Cloud, Raster, or VRS object or a path to one
    :param return_type: (str) epsg (ex. 31184) or datum (ex. NAD84 MTM 4)

    :return: EPSG or the datum name (st)
    """
    wkt = get_cosys_wkt(coverage).split('\n')
    datum = wkt[0].split('"')[1]
    epsg = wkt[-1].split('"')[3]
    result = None

    if return_type == 'epsg':
        result = epsg
    elif return_type == 'datum':
        result = datum

    return result


def get_extents(coverage):
    """
    Reads the xml string from a coverage file and return the extent.

    :param coverage: (obj) Cloud, Raster, or VRS object or a path to one
    :return: geographic coordinate coverage's extent [west (str), east (str),
                                                      south (str), north (str)]
    """
    root = get_xml(coverage)
    extents = []
    for coordinates in root.iter('{}Decimal'.format(gco)):
        extents.append(coordinates.text)

    return extents


def get_cosys_from_extents(coverage):
    """
    Return the coverage epsg according to its extent.

    :param coverage: (obj) Cloud, Raster, or VRS object or a path to one.
    :return: Coverage epsg according to its extent ['epsg1'(str), 'epsg2'(str), ...]
    """
    extents = get_extents(coverage)
    datum = []
    for epsg, bound in ZONE_EXTENTS.items():
        if float(extents[0]) < bound[0] and float(extents[1]) > bound[1]:
            datum.append(epsg)

    return list(set(datum))


def get_mtm_zone_from_epsg(coverage):
    """
    Return the mtm zone of the coverage according to its epsg (3218x, 294x).

    :param coverage: (obj) Cloud, Raster, or VRS object or a path to one.
    :return: (str) MTM zone.
    """
    try:
        return EPSG_ZONE_MTM[get_cosys(coverage)]

    except KeyError:
        return None


def get_vertical_cosys(coverage):
    """
    Return the vertical coordinate system.

    :param coverage: (obj) Cloud, Raster, or VRS object or a path to one.
    :return: (str) Vertical CRS.
    """
    try:
        wkt = get_cosys_wkt(coverage, vert_cosys=True).split('\n')

        return wkt[0].split('"')[1]

    except (KeyError, IndexError, AttributeError):
        return None


def get_bounding_polygon(coverage):
    """
    Return the bounding polygon's wkt.

    :param coverage: (obj) Cloud, Raster, or VRS object or a path to one.
    :return: (str) Actual bounding polygon's wkt.
    """
    return get_coverage(coverage).bounding_polygon


def generate_bounding_polygon(coverage):
    """
    Return the WKT string generated by Caris.

    :param coverage: (obj) Cloud, Raster, or VRS object or a path to one.
    :return: WKT string generated by Caris.
    """
    return cov.generate_polygon(get_coverage(coverage))  # Returns WKT string


def write_bounding_polygon(coverage, wkt):
    """
    Write a WKT string to the bounding polygon of a coverage object.

    :param coverage: (obj) Cloud, Raster, or VRS object or a path to one.
    :param wkt: (str) WKT string of a polygon.
    """
    options = cov.Options(open_type=cov.OpenType.WRITE)
    type_ = get_coverage_type(coverage)

    if type_ == 'raster':
        raster = cov.Raster(coverage, options=options)
        raster.bounding_polygon = wkt
    elif type_ == 'cloud':
        cloud = cov.Cloud(coverage, options=options)
        cloud.bounding_polygon = wkt
    elif type_ == 'vrs':
        vrs = cov.VRS(coverage, options=options)
        vrs.bounding_polygon = wkt


def get_coverage_type(coverage):
    """
    Return the coverage type.

    :param coverage: (obj) Cloud, Raster, or VRS object or a path to one.
    :return: The coverage type.
    """
    coverage = get_coverage(coverage)

    if isinstance(coverage, cov.Raster):
        return 'raster'
    elif isinstance(coverage, cov.Cloud):
        return 'cloud'
    elif isinstance(coverage,  cov.VRS):
        return 'vrs'


def get_coordinate_system_type(coverage):
    """
    Return the coordinate system type.

    :param coverage: (obj) Cloud, Raster, or VRS object or a path to one.
    :return: Coordinate system type.
    """
    wkt = get_cosys_wkt(coverage)
    cosys_type = None

    if wkt is not None:
        if wkt.startswith('PROJCS'):
            cosys_type = 'PROJCS'
        elif wkt.startswith('GEOGCS'):
            cosys_type = 'GEOGCS'

    return cosys_type


def get_count_points_cloud(coverage):
    """
    Return the count of points.

    :param coverage: (obj) Cloud object or a path to one.
    :return: The count.
    """
    coverage = get_coverage(coverage)

    return coverage.point_count


def get_time_min_max(coverage):
    """
    Get the minimum and maximum time of the coverage.

    :param coverage: (obj) Cloud, Raster, or VRS object or a path to one.
    :return: Minimum time  and maximum time yyyy-mm-ddThh:mm:ss.
    """
    coverage = get_coverage(coverage, write=True)
    root = get_xml(coverage)
    min_time = None
    max_time = None

    for string in root.iter("{}beginPosition".format(gml)):
        if string.text is not None:
            min_time = string.text

    for string in root.iter("{}endPosition".format(gml)):
        if string.text is not None:
            max_time = string.text

    return min_time, max_time


def set_time(coverage, min_time=None, max_time=None):
    """
    Function setting the minimum and maximum time of the coverage.

    :param coverage: (obj) Cloud, Raster, or VRS object or a path to one.
    :param min_time: (str) Minimum time yyyy-mm-ddThh:mm:ss.
    :param max_time: (str) Maximum time yyyy-mm-ddThh:mm:ss.
    :raise: ValueError if the format is incorrect.
    """
    temporal_extent = """<gmi:MI_Metadata xmlns:gmi="http://www.isotc211.org/2005/gmi" xmlns:gmd="http://www.isotc211.org/2005/gmd" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:gml="http://www.opengis.net/gml/3.2">          
      <gmd:temporalElement>
        <gmd:EX_TemporalExtent>
          <gmd:extent>
            <gml:TimePeriod gml:id="temporal-extent-1" xsi:type="gml:TimePeriodType">
              <gml:beginPosition>1900-01-01T00:00:00</gml:beginPosition>
              <gml:endPosition>1900-01-01T12:00:00</gml:endPosition>
            </gml:TimePeriod>
          </gmd:extent>
        </gmd:EX_TemporalExtent>
      </gmd:temporalElement>
    </gmi:MI_Metadata>"""

    coverage = get_coverage(coverage, write=True)
    root = get_xml(coverage, export=True)

    # Vérifie si le tag temporalElement est présent
    if sum(1 for _ in root.iter("{}beginPosition".format(gml))) == 0:
        index_insert = None
        for tag_xml in root.iter('{}identificationInfo'.format(gmd)):
            for child in tag_xml.iterdescendants():
                if child.tag == '{}geographicElement'.format(gmd):
                    index_insert = child
        # Ajout du tag temporalElement à la suite du tag geographicElement
        index_insert.append(et.fromstring(temporal_extent))

    if min_time is not None:
        if bool_is_datetime(min_time):
            for string in root.iter("{}beginPosition".format(gml)):
                if string.text is not None:
                    string.text = min_time
        else:
            raise ValueError('(in: {}) Le format doit être yyyy-mm-ddThh:mm:ss.'.format(min_time))

    if max_time is not None:
        if bool_is_datetime(max_time):
            for string in root.iter("{}endPosition".format(gml)):
                if string.text is not None:
                    string.text = max_time
        else:
            raise ValueError('(in: {}) Le format doit être yyyy-mm-ddThh:mm:ss.'.format(max_time))

    coverage.iso19139_xml = et.tostring(root).decode()


def bool_is_datetime(date_time):
    """
    A function to determine if the character string is well formatted yyyy-mm-ddThh:mm:ss.

    :param date_time: (str) yyyy-mm-ddThh:mm:ss.
    :return: (bool) True if the character string is well formatted, False otherwise.
    :raise: ValueError if the datetime object is less than 1752-09-14T00:00:01.
    :raise: ValueError if the datetime object is invalid.
    """
    try:
        date_time = dup.parse(date_time)
        if not date_time > datetime.datetime(1752, 9, 14, 0, 0, 1):
            raise ValueError('La date doit être supérieure à 1752-09-14 00:00:01.')
    except dup._parser.ParserError:
        raise ValueError('La date est invalide.')

    return bool(re.match(r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}$', datetime))


def list_contributor(coverage, out_st=None, out_pc=None, out_npc=None):
    """
    A function to obtain the list of contributors of a combine.

    :param coverage: (obj) Raster from a Combine.
    :param out_st: (str) The path of the output file for the string_table.
    :param out_pc: (str) The path of the output file for the participating contributors.
    :param out_npc: (str) The path of the output file for the non-participating contributors.
    :return: The list of the string table, the participating contributors et non-participating contributors.
    :raise: TypeError if coverage doesn't have a 'Contributor' band.
    """
    coverage = get_coverage(coverage)

    if 'Contributor' not in list_bands(coverage):
        raise TypeError("Il ne s'agit pas d'un combine. Le fichier *.csar n'a pas de couche 'Contributor'.")

    ndv = coverage.band_info['Contributor'].ndv
    data = coverage.read('Contributor', ((0, 0), coverage.dims))

    contributor_keys = []
    # Récupération des valeurs des contributeurs actifs dans le combine
    for value_ in data:
        if value_ != ndv and value_ not in contributor_keys:
            contributor_keys.append(value_)

    band_contributor = coverage.band_info['Contributor']

    string_table = []
    # Récupération des valeurs de la string table comprenant les fichiers qui ont participés au combine
    for value_ in band_contributor.string_table:
        string_table.append(value_.replace('|', ','))

    participating_contributor = []
    non_participating_contributor = string_table.copy()
    # Récupération des contributeurs participants et non-participant
    for key_ in contributor_keys:
        participating_contributor.append(string_table[key_])
        non_participating_contributor.remove(string_table[key_])

    # Écriture des fichiers csv
    if out_st is not None:
        with open(out_st, mode='w') as file_out:
            for value_ in string_table:
                file_out.write('{}\n'.format(value_))

    if out_pc is not None:
        with open(out_pc, mode='w') as file_out:
            for value_ in participating_contributor:
                file_out.write('{}\n'.format(value_))

    if out_npc is not None:
        with open(out_npc, mode='w') as file_out:
            for value_ in non_participating_contributor:
                file_out.write('{}\n'.format(value_))

    return string_table, participating_contributor, non_participating_contributor


def get_source(coverage) -> List[str]:
    """

    """
    coverage = get_coverage(coverage, write=False)
    root = get_xml(coverage)
    source = []

    for tag_xml in root.iter('{}source'.format(gmd)):
        for child in tag_xml.iterdescendants():
            if child.tag == '{}CharacterString'.format(gco):
                if child.text.startswith('Track Line ='):
                    source += [x.split('Line=')[-1] for x in child.text.split('?')[-1].split('&')]
                if child.text.startswith('Input =') and '?' in child.text:
                    source += [x for x in child.text.split('?')[-1].replace('&', '').split('Line=') if x != '']

    return source


if __name__ == "__main__":
    import time

    start = time.time()
    # file: str = r'D:\HDCS_Data\22c051117361\007-Surfaces\22c051117361_final.csar'
    file = r'D:\NONNAP10_4900N06900W.csar'
    raster = get_coverage(file)

    # file = r"D:\HDCS_Data\22-----3549-\007-Surfaces\4326.csar"

    # print(list_bands(file))
    # remove_band(file, ['Uncertainty_'])

    # bands = get_coverage(file).band_info
    # print(dir(bands))
    # for key, value in bands.items():
    #     print(key, value)
    #     print(key, value.category)

    # accepted = 1073741824
    # print('accepted   ', bin(accepted))
    # accepted1 = 134217728
    # print('accepted1  ', bin(accepted1))
    # designated = 1073742848
    # print('designated ', bin(designated))
    # designated1 = 1342178304
    # print('designated1', bin(designated1))
    # rejected = 1342177285
    # print('rejected   ', bin(rejected))
    # suppressed = 1342179328
    # print('suppressed ', bin(suppressed))
    # examined = 1342177792
    # print('examined   ', bin(examined))
    # outstanding = 1342177536
    # print('outstanding', bin(outstanding))

    # block_iterator = get_coverage(file, write=True).query(["Status"], flags=("Status", (), ()))
    # for block in block_iterator:
    #     print(block)
    #     if not block["Status"].any():  # No Designated points, skip this step
    #         continue
    #     updated_status = np.array([designated] * len(block["Status"]), dtype='uint32')
    #     block_iterator.write("Status", updated_status)

    # print(get_coverage(file, write=True).highest_level)

    # pts = get_numpy_array_cloud(cov, band_name=cov.position_band_name)
    # print(points)
    # print(points.size)

    # print(cov.point_count)
    # print(get_count_points_cloud(cov))
    # print(get_count_points_cloud(file))

    # cov_bands = set(list_bands(file))
    # print(cov_bands)
    #
    # bands = {'Density', 'Depth', 'Hypothesis_Count', 'Mean'}
    # print(bands)
    #
    # print(bands - cov_bands)
    # print(cov_bands - bands)

    # NEW_MIN_TIME = "1973-02-20T23:59:59"
    # NEW_MAX_TIME = "1973-10-29T12:00:00"
    #
    # min, max = get_time_min_max(file)
    # print(min)
    # print(max)
    # set_time(file, NEW_MIN_TIME, NEW_MAX_TIME)
    # min, max = get_time_min_max(file)
    # print(min)
    # print(max)

    # file = get_coverage(file, write=True)
    get_xml(file, True,  'PACD.xml')
    print(get_cosys_wkt(file))
    # print(get_coverage_type(file))
    # print(generate_bounding_polygon(file))
    # print(get_coverage_type(file))
    # write_bounding_polygon(file, wkt)
    # print(get_resolution(file))
    # print(file.extents)
    # print(file.bounding_polygon)
    # print(get_extents(file))
    # print(get_xml(file, True))
    # print(get_resolution(file))
    print(get_cosys_wkt(file))
    print(get_cosys(file))
    print(get_cosys(file, 'datum'))
    print(get_cosys(file, 'epsg'))
    # print(get_cosys_from_extents(file))
    # print(get_mtm_zone_from_epsg(file))
    # print(get_vertical_cosys(file))
    # print(list_bands(file))
    # print(get_coordinate_system_type(file))
