import os
from shapely.wkt import loads

import chs_lib.caris_api.coverage_utils as cu


class BoundingPolygonUtils:
    """
    Classe permettant d'interagir avec un bounding polygon.
    """
    def __init__(self, p_value):
        """
        Constructeur de la classe.

        :param p_value: (str) Le chemin vers un fichier csar ou une géométrie de type wkt.
        """

        if p_value.endswith('.csar') and not os.path.exists(p_value):
            raise ValueError('Fichier *.csar inexistant.')
        elif p_value.endswith('.csar'):
            self.wkt_bounding_polygon = self.wkt_from_csar(p_value)
        else:
            self.wkt_bounding_polygon = loads(p_value)

    @staticmethod
    def wkt_from_csar(file):
        """
        Méthode permettant de récupérer le bounding polygon d'un fichier csar et d'initialiser un objet shapely.

        :param file: (str) Le chemin vers un fichier csar.
        :return: Un objet shapely.
        """
        return loads(cu.get_bounding_polygon(file))

    def geometry_is_valid(self):
        """
        Méthode permettant de valider la géométrie du bounding polygon.

        :return: (bool) True si la géométrie du bounding polygon est valide, sinon False.
        """
        return self.wkt_bounding_polygon.is_valid

    def geometry_is_simple(self):
        """
        Méthode permettant de valider la géométrie du bounding polygon.

        :return: (bool) True si la géométrie du bounding polygon est simple, sinon False.
        """
        return self.wkt_bounding_polygon.is_simple

    def vector_intersect(self, wkt):
        """
        Méthode permettant de vérifier si le bounding polygon intersecte le
        vecteur passé en argument (intérieur ou frontière).

        :param wkt: Un objet shapely.
        :return: (bool) True si la géométrie du bounding polygon intersecte le vecteur passé en argument, sinon False.
        """
        return self.wkt_bounding_polygon.intersects(wkt)

    def vector_overlap(self, wkt):
        """
        Méthode permettant de vérifier si le bounding polygon chevauche le vecteur passé en argument.

        :param wkt: Un objet shapely.
        :return: (bool) True si la géométrie du bounding polygon chevauche le vecteur passé en argument, sinon False.
        """
        return self.wkt_bounding_polygon.overlaps(wkt)

    def vector_contains(self, wkt):
        """
        Méthode permettant de vérifier si le bounding polygon contient le vecteur passé en argument.

        :param wkt: Un objet shapely.
        :return: (bool) True si la géométrie du bounding polygon contient le vecteur passé en argument, sinon False.
        """
        return self.wkt_bounding_polygon.contains(wkt)

    def get_bounds(self, p_scale=0.0):
        """
        Méthode permettant de retourner les limites du bounding polygon.

        :param p_scale: (float) Un facteur d'échelle.
        :return: (tuple) Un tuple (minx, miny, maxx, maxy) de valeur de type float qui représente les limites
                         du bounding polygon.
        """
        minx, miny, maxx, maxy = self.wkt_bounding_polygon.bounds
        deltax = (maxx - minx) * p_scale
        deltay = (maxy - miny) * p_scale

        return ((minx - deltax),
                (miny - deltay),
                (maxx + deltax),
                (maxy + deltay))

    @property
    def area(self) -> float:
        return self.wkt_bounding_polygon.area


# if __name__ == '__main__':
#     # surface = BoundingPolygonUtils(r"D:\HDCS_Data\20e081111861\007-Surfaces\20e081111861.csar")
#     wkt = r"D:\Port_MTL\Combine_chenal\map\1317.wkt"
#
#     with open(wkt, 'r') as geom:
#         geometry = geom.read()
#
#     print(geometry)
#     surface = BoundingPolygonUtils(geometry)
#
#     print(surface.get_bounds())

    # if surface.geometry_is_valid():
        # print(surface.vector_intersect(wkt_surface))
        # print(surface.vector_intersect(surface.wkt_bounding_polygon))
        # print(surface.vector_contains(wkt_surface))
        # print(surface.vector_contains(surface.wkt_bounding_polygon))
        # print(surface.vector_overlap(wkt_surface))
        # print(surface.vector_overlap(surface.wkt_bounding_polygon))
    # else:
    #     raise ValueError('La géométrie du bounding polygon est invalide.')
