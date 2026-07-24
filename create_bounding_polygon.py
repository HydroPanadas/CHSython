import argparse
import json
import numpy as np
import os
from shapely.errors import TopologicalError
import sys
from tkinter import messagebox
import traceback

from chs_lib.caris_batch.exceptions_batch import BandError
from chs_lib.caris_batch.caris_batch_be_facade import get_base_editor_facade
import chs_lib.caris_api.coverage_utils as cu
from chs_lib import bounding_polygon_utils
from chs_lib import chs_utils as chsu
from chs_lib import ctypes_utils
from chs_lib import raster_utils as ru
from chs_lib import vector_utils as vu

#from bounding_polygon import interface_bp

__author__ = "Yan Bilodeau"
__copyright__ = ""
__credits__ = ["Yan Bilodeau"]
__license__ = ""
__version__ = "1.1.0"
__maintainer__ = "Yan Bilodeau"
__email__ = "yan.bilodeau@dfo-mpo.gc.ca"
__status__ = "Production"


APPLICATION_PATH = ''
if getattr(sys, 'frozen', False):
    APPLICATION_PATH = os.path.dirname(sys.executable)
elif __file__:
    APPLICATION_PATH = os.path.dirname(__file__)

try:
    with open(os.path.join(APPLICATION_PATH, 'param', 'param.json'), "r",
              encoding='utf-8') as param:
        environment = json.load(param)
        ALFA = environment['param']['ALPHA_INI']                                           # Valeur initiale pour le Alpha
        ALPHA_THRESHOLD = environment['param']['ALPHA_THRESHOLD']                          # Treshold maximum pour la valeur Alpha
        BUFFER_MIN_RASTER = environment['param']['MIN_BUFFER_RASTER']                      # Valeur minimale du buffer en mètre pour les rasters
        BUFFER_GEOGCS_MIN_RASTER = environment['param']['MIN_BUFFER_GEOGCS_RASTER']        # Valeur minimale du buffer en degré pour les rasters
        BUFFER_MIN_PC = environment['param']['MIN_BUFFER_PC']                              # Valeur minimale du buffer en mètre pour les point clouds
        BUFFER_GEOGCS_MIN_PC = environment['param']['MIN_BUFFER_GEOGCS_PC']                # Valeur minimale du buffer en degré pour les point clouds
        style = environment['param']['STYLE_BUFFER']                                       # Valeur pour le style des vertex
        DEFAULT_DIR = environment['param']['DEFAULT_DIR']                                  # Répertoire par défaut
        to_csar = environment['param']['TO_CSAR']                                          # Bool, true pour écrire le bounding polygon dans le fichier *.csar
        to_shp = environment['param']['TO_SHP']                                            # Bool, true pour enregistrer le bounding polygon dans un fichier shapefile
        to_wkt = environment['param']['TO_WKT']                                            # Bool, true pour enregistrer le bounding polygon dans un fichier WKT
        to_gml = environment['param']['TO_GML']                                            # Bool, true pour enregistrer le bounding polygon dans un fichier GML
        FACTOR_BP = environment['param']['FACTOR_BP']                                      # Facteur multiplicateur pour le buffer
        FACTOR_TOL = environment['param']['FACTOR_TOL']                                    # Facteur multiplicateur pour la tolérance par rapport au buffer
        fill_hole = environment['param']['FILL_HOLE']                                      # Bool, true pour filtrer les inner ring du bounding polygon
        delete_hole = environment['param']['DELETE_HOLE']                                  # Bool, true pour supprimer les inner ring du bounding polygon
        FACTOR_AREA = environment['param']['FACTOR_AREA']                                  # Facteur multiplicateur pour la superficie maximale

except FileNotFoundError:
    messagebox.showinfo("Avertissement", "Problème avec le fichier './param/param.json'.")
    raise sys.exit(-1)


def _manage_exception(e):
    """
    Méthode qui permet de détailler les erreurs.

    :param e: un objet de type exception
    """
    # Get current system exception
    e_type, e_value, e_traceback = sys.exc_info()

    # Extract unformatter stack traces as tuples
    trace_back = traceback.extract_tb(e_traceback)

    # Format stacktrace
    stack_trace = list()

    for trace in trace_back:
        stack_trace.append("File : {}, Line : {}, Func.Name : {}, Message : {}"
                           .format(trace[0], trace[1], trace[2], trace[3]))

    print("Exception type : {}".format(e_type.__name__))
    print("Exception message : {}".format(e_value))
    print("Stack trace : {}".format(stack_trace))


def optimized(p_pts, p_alpha, p_geom_pts):
    """
    Fonction permettant de trouver la valeur alpha optimale et de créer l'enveloppe concave.

    :param p_pts: (numpy array) Un liste contenant l'ensemble des points (x, y).
    :param p_alpha: (int) Valeur influençant la proximité du polgygon des points.
    :param p_geom_pts: Un objet shapely Multipoints.
    :return: Un objet shapely représentant l'enveloppe, une liste des sommets de l'enveloppe et la valeur
            alpha finale.
    """
    completed = False
    sup = None
    inf = 0
    hull = None
    edge = None
    alpha = p_alpha
    print('Alpha : ', end='')

    while not completed:
        try:
            print(alpha, end='... ')
            hull, edge = vu.alpha_shape(p_pts, alpha)
            if hull:
                shape = vu.from_object_to_geodataframe(hull).buffer(0.00001)
                # container = vu.get_wkt_from_object(shape, p_type='shapely')

                # if not container.contains(p_geom_pts):
                if not shape.contains(p_geom_pts).bool():
                    sup = alpha
                    if (sup - inf) <= 1:
                        if alpha > 1:
                            alpha -= 1
                        else:
                            alpha -= (sup - inf) / 2
                    else:
                        alpha -= int((sup - inf) / 2)
                else:
                    inf = alpha
                    if edge is None:
                        completed = True
                    elif sup is None:
                        alpha *= 2
                    elif (sup - inf) > ALPHA_THRESHOLD:
                        alpha += round(int((sup - inf) / 2))
                    else:
                        completed = True

            else:
                sup = alpha
                if alpha > 1:
                    alpha = round(int(alpha / 2))
                else:
                    alpha -= (sup - inf) / 2

        # except (ValueError, AttributeError):
        #     sup = alpha
        #     if alpha > 1:
        #         alpha = round(int(alpha / 2))
        #     else:
        #         alpha -= (sup - inf) / 2

        except Exception as e:
            _manage_exception(e)

    print('')
    return hull, edge, alpha


def compute_parameters(p_input):
    """
    Fonction permettant de calculer le buffer et la tolérance à partir des paramètres par défaut.

    :param p_input: (str) Un fichier .csar.
    :return: (float, float) La valeur du buffer et de tolérance à utiliser
    """
    buffer = 0

    cosys_type = cu.get_coordinate_system_type(p_input)
    cov_type = cu.get_coverage_type(p_input)

    if cov_type == 'cloud':
        if cosys_type == 'PROJCS':
            buffer = BUFFER_MIN_PC
        elif cosys_type == 'GEOGCS':
            buffer = BUFFER_GEOGCS_MIN_PC

    elif cov_type == 'raster':
        resolution = cu.get_resolution(p_input)
        if cosys_type == 'PROJCS':
            buffer = max(BUFFER_MIN_RASTER, FACTOR_BP * float(resolution[0]))
        elif cosys_type == 'GEOGCS':
            buffer = max(BUFFER_GEOGCS_MIN_RASTER, FACTOR_BP * float(resolution[0]))

    tolerance = FACTOR_TOL * buffer

    return buffer, tolerance


def create_bp(p_input: str, p_buffer: float, p_tolerance: float, p_style: int = None, p_write_bp_to_csar: bool = None,
              p_write_bp_to_shp: bool = None, p_write_bp_to_wkt: bool = None, p_write_to_gml: bool = None,
              p_delete_hole: bool = None, p_fill_hole: bool = None, p_fill_area: float = 0, p_mute: bool = False,
              p_band: str = 'Depth'):
    """
    Fonction permettant de générer le bounding polygon d'un fichier.

    :param p_input: (str) Un fichier .csar.
    :param p_buffer: (float) La valeur du buffer.
    :param p_tolerance: (float) La valeur de la tolérance.
    :param p_style: (int) Les styles de jointures entre les segments sont spécifiés par des valeurs entières :
                         1 (rond), 2 (onglet) et 3 (biseau).
    :param p_write_bp_to_csar: (bool) Vrai pour écrire le bounding polygon dans le fichier .csar.
    :param p_write_bp_to_shp: (bool) Vrai pour écrire le bounding polygon dans un fichier shapefile.
    :param p_write_bp_to_wkt: (bool) Vrai pour écrire le bounding polygon dans un fichier Caris WKT.
    :param p_write_to_gml: (bool) Vrai pour écrire le bounding polygon dans un fichier gml en WGS84.
    :param p_delete_hole: (bool) Vrai pour supprimer les inner ring du bounding polygon.
    :param p_fill_hole: (bool) Vrai pour remplir les inner ring du bounding polygon.
    :param p_fill_area: (float) Valeur indiquant la superficie maximale des trous à remplir.
    :param p_mute: (bool) True pour ne pas afficher les étapes de traitement, False sinon.
    :param p_band: (str) Le nom de la couche à utiliser.
    :return: (str)  1- Le nombre de polygone dans le bounding polygon,
             (str)  2- Le nombre de sommets dans le bounding polygon,
             (bool) 3- True si le bounding polygon englobe la surface, False sinon,
             (bool) 4- True si le bounding polygon intersect la surface, False sinon,
             (bool) 5- True si la géométrie valide, False sinon.
             (str)  6- Le wkt de la projection.
             (str)  7- Le wkt de la geométrie.
    """
    def print_stdout(p_message):
        if not p_mute:
            print(p_message)

    path, file = os.path.split(p_input)[0], os.path.splitext(os.path.split(p_input)[1])[0]

    geotiff = os.path.join(path, "{}.tiff".format(file))
    vectorized = os.path.join(path, "{}_Cvectorized.shp".format(file))
    bound = os.path.join(path, '{}_boundingPolygon.shp'.format(file))
    wkt_file = os.path.join(path, '{}_boundingPolygon.wkt'.format(file))
    gml_file = os.path.join(path, '{}_boundingPolygon(WGS84).gml'.format(file))
    wkt_surface = None

    if p_write_bp_to_csar is None:
        p_write_bp_to_csar = to_csar
    if p_write_bp_to_shp is None:
        p_write_bp_to_shp = to_shp
    if p_write_bp_to_wkt is None:
        p_write_bp_to_wkt = to_wkt
    if p_write_to_gml is None:
        p_write_to_gml = to_gml
    if p_delete_hole is None:
        p_delete_hole = delete_hole
    if p_fill_hole is None:
        p_fill_hole = fill_hole
    if p_style is None:
        p_style = style

    try:
        cov = cu.get_coverage(p_input)
        try:
            epsg = cu.get_cosys_wkt(cov).replace(" ", "").replace("\n", "")
        except Exception as e:
            _manage_exception(e)
            epsg = None

        print_stdout("Creating the bounding polygon for {}.csar.".format(file))

        result = None

        # todo accepter les goetiff
        if cu.get_coverage_type(cov) == 'raster':
            print_stdout('====== Exporting the file to GeoTiff: {} ======'
                         .format(chsu.get_time_local()))

            beu = get_base_editor_facade()

            try:
                response = beu.export_csar_to_raster(
                    p_input, geotiff, include_band=p_band
                )
                print_stdout(response)

            except BandError as e:
                _manage_exception(e)
                print_stdout('-------------------------------------------------------')
                print_stdout('Bounding Polygon creation failed.')
                print_stdout('-------------------------------------------------------')
                return None, None, None, None, None, None, None

            print_stdout('====== GeoTIFF vectorization: {} ======'
                         .format(chsu.get_time_local(), ))

            # todo modifier les méthodes utilisées de gdal
            result = ru.polygonize_raster_gdal(
                geotiff,
                vectorized,
                p_simplified=True,
                p_path=os.path.join(APPLICATION_PATH, 'Dependencies')
            )

            wkt_surface = vu.get_wkt_from_object(result)

        elif cu.get_coverage_type(cov) == 'cloud':
            if p_buffer == 0:
                if cu.get_coordinate_system_type(cov) == 'GEOGCS':
                    p_buffer = 0.00001
                else:
                    p_buffer = 0.1

            print_stdout("====== Create concave envelope: {} ======"
                         .format(chsu.get_time_local()))
            points = np.delete(cu.get_numpy_array_cloud(cov, cov.position_band_name), 2, 1)
            wkt_surface = vu.from_array_of_points_to_object(points, p_type='Shapely')
            hull, _, alfa = optimized(points, ALFA, wkt_surface)
            result = vu.from_object_to_geodataframe(hull)

        area = 0
        for pol in vu.from_object_to_geodataframe(result):
            area += pol.area

        if p_buffer != 0:
            print_stdout("====== Creating buffers: {} ======"
                         .format(chsu.get_time_local()))
            result = vu.create_buffer(result, p_buffer, p_join_style=p_style)

        print_stdout("====== Merging Polygons: {} ======"
                     .format(chsu.get_time_local()))
        result = vu.unary_union(result)

        if p_tolerance != 0:
            print_stdout("====== Simplifying Polygons: {} ======"
                         .format(chsu.get_time_local()))
            result = vu.simplify_geometry(result, p_tolerance)

        if p_delete_hole:
            print_stdout("====== Removing holes: {} ======"
                         .format(chsu.get_time_local()))
            result = vu.dissolve_inner_ring(result)
        elif p_fill_hole:
            print_stdout("====== Filling holes: {} ======"
                         .format(chsu.get_time_local()))
            result = vu.dissolve_inner_ring(result, p_area=p_fill_area)

        wkt = vu.get_wkt_from_object(result, p_type='string')

        try:
            if p_write_bp_to_csar:
                print_stdout("====== Writing the Bounding Polygon: {} ======"
                             .format(chsu.get_time_local()))
                del cov
                cu.write_bounding_polygon(p_input, wkt)
                cov = cu.get_coverage(p_input)
        except Exception as e:
            _manage_exception(e)
            cov = cu.get_coverage(p_input)
            print_stdout("Unable to write Bounding Polygon to csar file")

        if p_write_bp_to_shp:
            print_stdout("====== Saving in shapefile format: {} ======"
                         .format(chsu.get_time_local()))
            try:
                vu.from_geopandas_to_file(result, bound, p_driver='ESRI Shapefile', p_epsg=epsg)
            except Exception as e:
                _manage_exception(e)
                print_stdout('Unable to create shapefile.')

        if p_write_bp_to_wkt:
            print_stdout("====== Saving in wkt format: {} ======"
                         .format(chsu.get_time_local()))
            vu.write_file('{}\n{}\n'.format(epsg, wkt), wkt_file)

        if p_write_to_gml:
            print_stdout("====== Saving in gml format: {} ======"
                         .format(chsu.get_time_local()))
            try:
                if epsg is not None:
                    gml = result.set_crs(epsg)
                    gml_wgs84 = gml.to_crs(epsg=4326)
                    vu.from_geopandas_to_file(gml_wgs84, gml_file, 'GML')
                else:
                    print_stdout('Unable to create gml file.')
            except Exception as e:
                _manage_exception(e)
                print_stdout('Unable to create gml file.')

        nb_poly, nb_point = vu.get_count_poly_points(result)
        print_stdout('-------------------------------------------------------')
        print_stdout("Bounding Polygon created for {}.csar.\n"
                     "The Bounding Polygon has {} polygon(s) and a total of {} vertices."
                     .format(file, nb_poly, nb_point))

    except Exception as e:
        if isinstance(e.args[0], str):
            if e.args[0].startswith('Cannot access'):
                print_stdout("{} is currently being used by another process.".format(file))
        else:
            _manage_exception(e)
        print_stdout('-------------------------------------------------------')
        print_stdout('Bounding Polygon creation failed.')
        print_stdout('-------------------------------------------------------')
        return None, None, None, None, None, None, None

    contains = None
    overlap = None
    geometry_is_valid = None
    try:
        if p_write_bp_to_csar:
            bpu = bounding_polygon_utils.BoundingPolygonUtils(p_input)
            contains = bpu.vector_contains(wkt_surface)
            overlap = bpu.vector_overlap(wkt_surface)
            geometry_is_valid = bpu.geometry_is_valid()
        else:
            contains = result.contains(wkt_surface).bool()
            overlap = result.overlaps(wkt_surface).bool()
            geometry_is_valid = result.is_valid.bool()

        if not contains:
            print_stdout("Avertissement : Le Bounding Polygon ne contient pas l'ensemble de la surface du "
                         "fichier {}.csar.".format(file))
        if overlap:
            print_stdout("Avertissement : Le Bounding Polygon croise la surface du fichier {}.csar.".format(file))
        if not geometry_is_valid:
            print_stdout("Avertissement : La geométrie du Bounding Polygon est invalide pour le "
                         "fichier {}.csar.".format(file))

    except TopologicalError:
        geometry_is_valid = False
        print_stdout("Avertissement : La geométrie du Bounding Polygon est invalide pour le "
                     "fichier {}.csar.".format(file))
    except Exception as e:
        _manage_exception(e)
        print_stdout('Échec de la validation du Bounding Polygon.')
        print_stdout('-------------------------------------------------------')

##    if os.path.exists(geotiff):
##        os.remove(geotiff)
    for _file in [vectorized]:
        vu.delete_vector(_file)

    print_stdout('-------------------------------------------------------')

    info = os.path.join(path, 'infoBoundingPolygon.csv')
    if not os.path.exists(info):
        with open(info, 'w') as f:
            f.write('{},{},{},{},{},{},{}\n'.format(
                'Fichier', 'Sommets', 'Buffer', 'Type', 'Superficie', 'Résolution', 'Unité'))

    with open(info, 'a') as f:
        f.write('{},{},{},{},{},{},{}\n'.format(
            file, nb_point, p_buffer, cu.get_coverage_type(cov), area,
            cu.get_resolution(cov)[0] if cu.get_coverage_type(cov) != 'cloud' else None,
            cu.get_resolution(cov)[1] if cu.get_coverage_type(cov) != 'cloud' else None))

    return nb_poly, nb_point, contains, overlap, geometry_is_valid, epsg, wkt


def create_command_line():
    """
    Fonction permettant de construire une ligne de commande avec ses arguments.

    :return : (arg.parse.ArgumentParser) La ligne de commande.
    """
    parser = argparse.ArgumentParser(description="Création d'un Bounding Polygon")
    parser.add_argument('--csar',
                        help="Le chemin d'un fichier *.csar.",
                        required=True)
    parser.add_argument('--buffer',
                        help='Une valeur pour la création du Buffer (valeur positive).',
                        required=True,
                        type=float)
    parser.add_argument('--tolerance',
                        help='Une valeur de tolérance pour la simplification du Bounding Polygon (valeur positive).',
                        required=True,
                        type=float)
    parser.add_argument('--style',
                        help='Les styles de jointures entre les segments sont spécifiés par des valeurs entières : '
                             '1 (rond), 2 (onglet) et 3 (biseau).',
                        nargs='?',
                        const=1,
                        type=int,
                        default=1)
    parser.add_argument('--to_csar',
                        help="Permet d'enregistrer le Bounding Polygon dans le fichier *.csar.",
                        default=False,
                        action='store_true')
    parser.add_argument('--to_shp',
                        help="Permet d'exporter le Bounding Polygon dans un fichier shapefile.",
                        default=False,
                        action='store_true')
    parser.add_argument('--to_wkt',
                        help="Permet d'exporter le Bounding Polygon dans un fichier wkt.",
                        default=False,
                        action='store_true')
    parser.add_argument('--delete_hole',
                        help="Permet de supprimer les inner rings du Bounding Polygon",
                        default=False,
                        action='store_true')
    parser.add_argument('--fill_hole',
                        help="Permet de remplir les inner rings du Bounding Polygon",
                        default=False,
                        action='store_true')
    parser.add_argument('--fill_area',
                        help='Valeur indiquant la superficie maximale des trous à remplir.',
                        required=False,
                        type=float)

    return parser


def arg_parser():
    """
    Fonction permettant de trier les arguments système de la requête et de générer le bounding polygon.
    """
    parser = create_command_line()
    args = parser.parse_args()

    if args.to_csar or args.to_shp:
        create_bp(args.csar, args.buffer, args.tolerance, p_style=args.style, p_write_bp_to_csar=args.to_csar,
                  p_write_bp_to_shp=args.to_shp, p_write_bp_to_wkt=args.to_wkt, p_delete_hole=args.delete_hole,
                  p_fill_hole=args.fill_hole, p_fill_area=args.fill_area)


def main(p_coverage=None):
    """
    Fonction principale pour générer un bounding polygon. Si des arguments système sont passés en paramètre,
    la Fonction arg_parser est appelée, sinon le GUI est ouvert.

    :param p_coverage: (str) Le chemin d'un fichier .csar pour initialiser le GUI avec celui-ci. Optionnel.
    """
    if len(sys.argv) == 1 or len(sys.argv) == 2:
        if p_coverage is not None:
            if not os.path.exists(p_coverage):
                p_coverage = None

        ctypes_utils.hide_console()
        interface_bp.BoundingPolygonGUI(p_coverage=p_coverage)

    else:
        arg_parser()


if __name__ == '__main__':
    main()

# todo save as
# todo methode rapide avec resampling
# todo option en batch
# todo implémenter un système de cache

# todo export du bp seulement sans générer un nouveau bp (shp, gml)
