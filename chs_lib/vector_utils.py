from bs4 import BeautifulSoup
import geopandas as gpd
import numpy as np
import os
from osgeo import ogr
from shapely import speedups
from shapely.wkt import loads
import shapely.geometry as geometry
import warnings
import shapely.ops as shapely_ops
from scipy.spatial import Delaunay
from typing import Optional, Union


def get_wkt_from_object(p_input, p_type: str = 'shapely'):
    """
    Fonction permettant de récupérer la géométrie d'un shapefile ou d'initialiser un objet shapely.

    :param p_input: (str) Un fichier dans un format supporté par Fiona.
    :param p_type: (str) shapely pour avoir un objet de ce type, string pour avoir un objet de ce type.
    :return: Un objet shapely ou string.
    """
    gdf = from_object_to_geodataframe(p_input)

    if not isinstance(gdf, gpd.geodataframe.GeoSeries):
        gdf_geom = [geom.wkt for geom in gdf['geometry'].tolist() if geom is not None]
    else:
        gdf_geom = [geom.wkt for geom in gdf.tolist() if geom is not None]

    if len(gdf_geom) == 1:
        geometry_wkt = loads(gdf_geom[0])
    else:
        geometry_wkt = geometry.MultiPolygon([loads(wkt_string) for wkt_string in gdf_geom])

    if p_type == 'string':
        return geometry_wkt.wkt
    elif p_type == 'shapely':
        return geometry_wkt


def get_wkt_epsg(p_epsg_code: str):
    """
    Fonction permettant de récupérer le wkt d'une projection.

    :param p_epsg_code: (str) Le code epsg.
    :return: (str) Un chaine de caractères représentant le wkt formaté.
    """
    import requests
    try:
        wkt = requests.get("http://spatialreference.org/ref/epsg/{0}/prettywkt/".format(p_epsg_code))
        soup = BeautifulSoup(wkt.content, "html.parser")
        epsg_wkt = soup.string.replace(" ", "").replace("\n", "")

        if epsg_wkt.split(',')[0].strip() == 'Notfound':
            epsg_wkt = None

        return epsg_wkt

    except requests.exceptions.SSLError:
        return None


def get_epsg_from_object(p_input):
    """
    Fonction permettant de retourner le EPSG de l'object
    :param p_input: (str) Un fichier dans un format supporté par Fiona, un objet de type geodataframe ou un
                          objet de type Shapely.
    :return: (str) Le EPSG.
    """
    try:
        gdf = from_object_to_geodataframe(p_input)
        epsg = gdf.crs.srs.split(':')[-1]

        return epsg

    except AttributeError:
        return None


def write_caris_wkt(p_input, p_output):
    """
    Fonction permettant de créer un fichier Caris WKT.

    :param p_input: (str) Un fichier dans un format supporté par Fiona, un objet de type geodataframe ou un
                          objet de type Shapely.
    :param p_output: (str) Le chemin du fichier de sortie
    :raise: ValueError s'il est impossible de récupérer le système de référenre en format WKT.
    """
    gdf = from_object_to_geodataframe(p_input)
    epsg = None

    if isinstance(p_input, str):
        if p_input.endswith('.shp'):
            if os.path.exists('{}.prj'.format(os.path.splitext(p_input)[0])):
                with open('{}.prj'.format(os.path.splitext(p_input)[0]), 'r') as prj:
                    epsg = prj.readline()
            elif os.path.exists('{}.shp_rxl'.format(os.path.splitext(p_input)[0])):
                with open('{}.shp_rxl'.format(os.path.splitext(p_input)[0]), 'r') as shp_rxl:
                    contents = shp_rxl.read()
                soup = BeautifulSoup(contents, 'xml')
                epsg = soup.find('wkt').text.replace(" ", "").replace("\n", "")
    else:
        epsg = get_wkt_epsg(get_epsg_from_object(gdf))

    if epsg is not None and epsg != '':
        write_file('{}\n{}\n'.format(epsg, get_wkt_from_object(gdf)), p_output)
    else:
        raise ValueError('Impossible de récupérer le système de référenre en format WKT pour ce fichier.')


def write_file(p_text, p_output):
    """
    Fonction permettant de créer un fichier .txt.

    :param p_text: (str) Une chaine de caractères .
    :param p_output: (str) Le chemin du fichier de sortie.
    """
    with open(p_output, 'w') as out:
        out.write(p_text)


def delete_vector(p_input, p_driver='ESRI Shapefile'):
    """
    Fonction permettant de supprimer un fichier.

    :param p_input: (str) Un fichier dans un format supporté par Fiona.
    :param p_driver: (str) Le format du driver utilisé pour supprimer le fichier.
    """
    shp_driver = ogr.GetDriverByName(p_driver)
    if os.path.exists(p_input):
        shp_driver.DeleteDataSource(p_input)


def rename_shapefile(p_input, p_output):
    """
    Fonction permettant de renommer un fichier shapefile et ses extensions associés.

    :param p_input: (str) Un fichier shapefile à renommer.
    :param p_output: (str) Le nom du fichier final.
    :retrun: (str) Le chemin du fichier shapefile renommé.
    """
    path, file_ = os.path.split(p_input)[0], os.path.split(p_input)[1]
    name_file = file_.split('.')[0]
    for ext in ['.prj', '.cpg', '.dbf', '.shx', '.shp']:
        aux_file = os.path.join(path, '{}{}'.format(name_file, ext))
        if os.path.exists(aux_file):
            output_file = os.path.join(path, '{}{}'.format(p_output, ext))
            if os.path.exists(output_file):
                os.remove(output_file)
            os.rename(aux_file, output_file)

    return os.path.join(path, '{}.shp'.format(p_output))


def from_object_to_geodataframe(p_input):
    """
    Fonction permettant d'ouvrir un fichier vectoriel et de retourner un objet geodataframe.

    :param p_input: (str) Un fichier dans un format supporté par Fiona, un objet de type geodataframe, un
                          objet de type Shapely ou un object de type.
    :return: Un objet de type geodataframe de Geopandas.
    :raise: ValueError lorsque le fichier est inexistant.
    """
    if isinstance(p_input, str):
        if not os.path.exists(p_input):
            raise ValueError('Fichier inexistant.')
        try:
            return gpd.GeoSeries.from_file(p_input)
        except ValueError:
            speedups.disable()
            return gpd.GeoSeries.from_file(p_input)

    elif isinstance(p_input, geometry.Polygon) or isinstance(p_input, geometry.MultiPolygon) \
            or isinstance(p_input, geometry.Point) or isinstance(p_input, geometry.MultiPoint) \
            or isinstance(p_input, geometry.LineString) or isinstance(p_input, geometry.LinearRing) \
            or isinstance(p_input, geometry.MultiLineString):
        return gpd.GeoSeries(loads(p_input.wkt))

    elif isinstance(p_input, gpd.geodataframe.GeoDataFrame) or isinstance(p_input, gpd.geodataframe.GeoSeries):
        return p_input

    elif isinstance(p_input, ogr.DataSource):
        wkt_list = []
        for feature in p_input.GetLayer():
            geom = feature.GetGeometryRef()
            wkt = geom.ExportToWkt()
            wkt_list.append(wkt)

        if len(wkt_list) == 1:
            return gpd.GeoSeries(loads(wkt_list[0]))
        else:
            poly = [loads(wkt) for wkt in wkt_list]
            return gpd.GeoSeries(poly)


def from_array_of_points_to_object(p_input, p_type='GeoPandas'):
    """
    Fonction permettant de transformer un numpy array de point en un fichier.

    :param p_input: (list, np array) un objet itérable contenant des points.
    :param p_type: (str) GeoPandas ou Shapely
    :return: Un objet de type geodataframe de Geopandas ou MultiPoints de shapely.
    """
    stack = np.vstack(p_input)
    if p_type == 'GeoPandas':
        return gpd.GeoSeries([geometry.Point(point[0], point[1]) for point in stack])

    elif p_type == 'Shapely':
        return geometry.MultiPoint([geometry.Point(point[0], point[1]) for point in stack])


def from_geopandas_to_file(
        p_input,
        p_output: str,
        p_driver: Optional[str] = 'ESRI Shapefile',
        p_layer: Optional[str] = None,
        p_epsg: Optional[Union[int, str, None]] = None
) -> str:
    """
    Fonction permettant d'enregistrer un objet geodataframe en fichier.

    :param p_input: (obj) Un objet geodataframe de geopandas.
    :param p_output: (str) Le chemin du fichier de sortie.
    :param p_driver: (str) Le format du driver utilisé pour écrire un
                     fichier ('GPKG', 'ESRI Shapefile', 'GeoJSON', ...).
    :param p_layer: (str) Le nom de la couche.
    :param p_epsg: (str, int) Le CRS du fichier en format WKT ou le numéro du epsg.
    :return: (str) Le chemin du fichier de sortie.
    """
    if p_epsg is not None:
        p_input = p_input.set_crs(p_epsg, allow_override=True) ##LD: Conditional override due to passing crs being incompatible with the pyogrio engine
        
    p_input.to_file(p_output, p_driver, layer=p_layer) #crs=p_epsg
    if p_driver == 'ESRI Shapefile' and p_epsg is not None:
        write_file(p_epsg, os.path.join(os.path.split(p_output)[0], '{}.prj'.format(
            os.path.splitext(os.path.split(p_output)[1])[0])))

    return p_output


def transform_proj(p_input, p_epsg: int):
    """
    Fonction permettant de changer la projection d'un fichier.

    :param p_input: Un fichier dans un format supporté par Fiona ou un objet shapely ou geodataframe.
    :param p_epsg: (int) Le code epsg de la projection désirée.
    :return: (objet) Un objet geodataframe.
    """
    gdf = from_object_to_geodataframe(p_input)
    gpd_trans = gdf.to_crs(epsg=p_epsg)

    return gpd_trans


def create_buffer(p_input, p_distance, p_resolution=16, p_cap_style=1, p_join_style=1, p_mitre_limit=5):
    """
    Fonction permettant de créer un buffer autour d'un fichier shapefile.

    :param p_input: (str) Un fichier dans un format supporté par Fiona ou un objet shapely ou geodataframe.
    :param p_distance: (float) La distance du buffer (unité de mesure selon la projection utilisé).
    :param p_resolution: (float) La résolution du buffer autour de chaque vertex.
    :param p_cap_style: (int) Les styles des coins sont spécifiés par des valeurs entières :
                        1 (rond), 2 (plat), 3 (carré).
    :param p_join_style: (int) Les styles de jointures entre les segments sont spécifiés par des valeurs entières :
                         1 (rond), 2 (onglet) et 3 (biseau).
    :param p_mitre_limit: (int) Limite pour les jointure en onglet.
    :return: (objet) Un objet geodataframe.
    """
    # p_resolution=16, p_cap_style=3, p_join_style=2, p_mitre_limit=5
    warnings.simplefilter(action='ignore', category=UserWarning)

    gdf = from_object_to_geodataframe(p_input)

    if not isinstance(gdf, gpd.geodataframe.GeoSeries):
        gdf = [geom for geom in gdf['geometry'].tolist() if geom is not None]
        gdf = gpd.GeoDataFrame(gpd.GeoSeries(gdf), columns=['geometry'])
    elif isinstance(gdf, gpd.geodataframe.GeoSeries):
        gdf = [geom for geom in gdf.tolist() if geom is not None]
        gdf = gpd.GeoSeries(gdf)

    gdf_buffer = gdf.buffer(p_distance, resolution=p_resolution, cap_style=p_cap_style,
                            join_style=p_join_style, mitre_limit=p_mitre_limit)

    return gdf_buffer


def simplify_geometry(p_input, p_tolerance):
    """
    Fonction permettant de simplifier la géométrie d'un fichier shapefile.

    :param p_input: (str) Un fichier dans un format supporté par Fiona ou un objet shapely ou geodataframe.
    :param p_tolerance: La tolérance pour la simplification (unité de mesure selon la projection utilisé).
    :return: (objet) Un objet geodataframe.
    """
    gdf = from_object_to_geodataframe(p_input)
    gdf_simplified = gdf.simplify(p_tolerance, preserve_topology=True)

    return gdf_simplified


def unary_union(p_input):
    """
    Fonction permettant de fusionner les polygones qui s'intersectant dans un Multipolygon.

    :param p_input: (str) Un fichier dans un format supporté par Fiona ou un objet shapely ou geodataframe.
    :return: (objet) Un objet geodataframe.
    """
    gdf = from_object_to_geodataframe(p_input)

    if not isinstance(gdf, gpd.geodataframe.GeoSeries):
        gdf = [geom for geom in gdf['geometry'].tolist() if geom is not None]
        gdf = gpd.GeoDataFrame(gpd.GeoSeries(gdf), columns=['geometry'])
    elif isinstance(gdf, gpd.geodataframe.GeoSeries):
        gdf = [geom for geom in gdf.tolist() if geom is not None]
        gdf = gpd.GeoSeries(gdf)

    union_gdf = gpd.GeoSeries(gdf.unary_union)

    return union_gdf


def explode(p_input):
    """
    Fonction permettant de séparer les polygones d'un multi-polygones.

    :param p_input: (str) Un fichier dans un format supporté par Fiona ou un objet shapely ou geodataframe.
    :return: (objet) Un objet geodataframe.
    """
    in_gdf = gpd.GeoDataFrame(geometry=gpd.GeoSeries(from_object_to_geodataframe(p_input)))
    out_gdf = gpd.GeoDataFrame(columns=in_gdf.columns)

    for idx, row in in_gdf.iterrows():
        if type(row.geometry) == geometry.Polygon:
            out_gdf = out_gdf.append(row, ignore_index=True)

        if type(row.geometry) == geometry.MultiPolygon:
            multdf = gpd.GeoDataFrame(columns=in_gdf.columns)
            recs = len(row.geometry)
            multdf = multdf.append([row]*recs, ignore_index=True)
            for geom in range(recs):
                multdf.loc[geom, 'geometry'] = row.geometry[geom]
            out_gdf = out_gdf.append(multdf, ignore_index=True)

    return out_gdf


def convex_hull(p_input):
    """
     Fonction permettant de créer une enveloppe convexe à un vecteur.

    :param p_input: (str) Un fichier dans un format supporté par Fiona ou un objet shapely ou geodataframe.
    :return: (objet) Un objet geodataframe.
    """
    gdf = from_object_to_geodataframe(p_input)
    con_hull = gdf.convex_hull

    return con_hull


def alpha_shape(p_points, p_alpha):
    """
    Fonction permettant de créer une enveloppe concave à un vecteur.

    :param p_points: (numpy array) Un liste contenant l'ensemble des points (x, y).
    :param p_alpha: (int) Valeur influençant la proximité du polgygon des points.
    :return: Un objet shapely représentant l'enveloppe et une liste des sommets de l'enveloppe.
    """
    try:
        if len(p_points) <= 3:
            return geometry.MultiPoint(list(p_points)).convex_hull, None

        coords = p_points
        tri = Delaunay(coords)
        triangles = coords[tri.vertices]
        a = ((triangles[:, 0, 0] - triangles[:, 1, 0]) ** 2 + (triangles[:, 0, 1] - triangles[:, 1, 1]) ** 2) ** 0.5
        b = ((triangles[:, 1, 0] - triangles[:, 2, 0]) ** 2 + (triangles[:, 1, 1] - triangles[:, 2, 1]) ** 2) ** 0.5
        c = ((triangles[:, 2, 0] - triangles[:, 0, 0]) ** 2 + (triangles[:, 2, 1] - triangles[:, 0, 1]) ** 2) ** 0.5

        s = (a + b + c) / 2.0
        areas = (s * (s - a) * (s - b) * (s - c)) ** 0.5
        circums = a * b * c / (4.0 * areas)
        filtered = triangles[circums < (1.0 / p_alpha)]
        edge1 = filtered[:, (0, 1)]
        edge2 = filtered[:, (1, 2)]
        edge3 = filtered[:, (2, 0)]

        edge_points = np.unique(np.concatenate((edge1, edge2, edge3)), axis=0).tolist()
        m = geometry.MultiLineString(edge_points)
        triangles = list(shapely_ops.polygonize(m))

        return shapely_ops.unary_union(triangles), edge_points

    except ZeroDivisionError:
        return geometry.MultiPoint(list(p_points)).convex_hull, None


def list_polygons_from_geopanda(p_input):
    """
    Fonction retournant une liste de polygones décomposés (MultiPolygon to Polygon) à partir d'un
    object geodataframe.

    :param p_input: (str) Un fichier dans un format supporté par Fiona ou un objet shapely ou geodataframe.
    :return: Une liste d'oject shapely.
    """
    gdf = from_object_to_geodataframe(p_input)

    shapely = []
    if isinstance(gdf, gpd.geodataframe.GeoDataFrame):
        shapely = gdf['geometry'].tolist()
    elif isinstance(gdf, gpd.geodataframe.GeoSeries):
        shapely = gdf.tolist()

    polygons = []
    for poly in shapely:
        if poly is not None and poly.geom_type == 'MultiPolygon':
            for geom in list(poly.geoms):
                polygons.append(geom)
        elif poly is not None and poly.geom_type == 'Polygon':
            polygons.append(poly)

    return polygons


def dissolve_inner_ring(p_input, p_area=None):
    """
    Fonction permettant d'éliminer les inner rings.

    :param p_input: (str) Un fichier dans un format supporté par Fiona ou un objet shapely ou geodataframe.
    :param p_area: (float) Une valeur de superficie pour remplir les inner rings.
    :return: (objet) Un objet geodataframe.
    """
    gdf = from_object_to_geodataframe(p_input)

    polygons = list_polygons_from_geopanda(gdf)

    fill_hole = []
    for poly in polygons:
        inners = list(poly.interiors)
        if len(inners) != 0:
            exteriror = list(poly.exterior.coords)
            interiors = []
            if p_area is not None:
                for inner in inners:
                    if geometry.Polygon(list(inner.coords)).area >= p_area:
                        interiors.append(list(inner.coords))
            fill_hole.append(geometry.Polygon(exteriror, interiors))
        else:
            fill_hole.append(poly)

    gdf_filled = gpd.GeoSeries(geometry.MultiPolygon(fill_hole))

    return unary_union(gdf_filled)


def get_count_poly_points(p_input):
    """
    Fonction permettant de compter le nombre de polygones et le nombre de sommets dans la géométrie de l'objet.

    :param p_input: (str) Un fichier dans un format supporté par Fiona ou un objet shapely ou geodataframe.
    :return: (int, int) Le nombre de polygones et le nombre de sommets.
    """
    gdf = from_object_to_geodataframe(p_input)

    polygons = list_polygons_from_geopanda(gdf)

    nb_polygon = 0
    nb_point = 0
    for poly in polygons:
        nb_polygon += 1
        nb_point += len(poly.exterior.coords)
        for inner in list(poly.interiors):
            nb_point += len(inner.coords)

    return nb_polygon, nb_point


def get_ogr_driver(p_file: str) -> str:
    """
    Méthode permettant de récupérer le driver de OGR selon l'extension du fichier.

    :param p_file: (str) Le chemin ou le nom du fichier
    :return: (string) Le driver OGR.
    """
    return {'.gml': 'GML', '.shp': 'ESRI Shapefile', '.json': 'GeoJSON'}[os.path.splitext(p_file)[-1]]


# if __name__ == '__main__':
#     file = r''
