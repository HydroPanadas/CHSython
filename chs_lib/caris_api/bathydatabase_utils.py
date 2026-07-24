import os
from lxml import etree as et
import re
import time
from typing import Dict, Any, Optional, List, Union, Tuple

from . uri import URI, is_uri
from . models_type import AttributeType, FeatureType, CRSType
from . import coverage_utils as cu

from chs_lib.logger_utils import create_logger

# Option pour l'importation des modules avec un fichier global de configuration.
from chs_lib.caris_api.caris_api_facade import caris, bathy_db

# Sinon il est possible d'utiliser
# python_env = r'C:\Program Files\CARIS\BASE Editor\5.5\python\3.7' -> Chemin vers les librairies de Caris
# import sys
# sys.path.insert(0, python_env)
# import caris
# import caris.bathy.db as bathy_db


class BathyDataBaseUtils:
    """
    Classe permettant d'interagir avec BDB.
    """
    def __init__(self, p_log: Optional[str] = None) -> None:
        """
        Constructeur de la classe BathyDataBaseUtils.

        :param p_coverage: (CoverageUtils) Un objet CoverageUtils.
        :param p_log: (str) Le chemin du journal.
        """
        self._logger = create_logger('BathyDatabaseUtils', p_log, 'magenta')

    def connect_node(self, p_user: str, p_password: str, p_host: str) -> bathy_db.NodeManager:
        """
        Méthode permettant de se connecter au node manager et de retourner un objet NodeManager.

        :param p_user: (str) Le nom d'utilisateur.
        :param p_password: (str) Le mot de passe de l'utilisateur.
        :param p_host: (str) L'adresse de l'hôte du node manager.
        :return: (bathy_db.NodeManager) Un objet <caris.bathy.db.NodeManager>.
        :raise: AuthenticationError ou HostError si un problème de connection au serveur survient.
        """
        try:
            return bathy_db.NodeManager(p_user, p_password, p_host)

        except RuntimeError as e:
            if str(e).startswith('password'):
                self._logger.error(e)
                raise AuthenticationError(
                    f"Échec de l'authentification par mot de passe pour l'utilisateur '{p_user}'."
                )

            elif str(e).startswith('database'):
                self._logger.error(e)
                raise HostError("Échec de la connexion à l'hôte '{}'.".format(p_host))

            elif str(e).startswith('remaining'):
                self._logger.error(e)
                # remaining connection slots are reserved for non-replication superuser connections
            else:
                self._logger.error(e)

    def connect_database(self, p_node: bathy_db.NodeManager, p_db_name: str) -> bathy_db.Dataset:
        """
        Méthode permettant de se connecter à une base de données et de retourner un objet
        <class 'caris.bathy.db.Dataset'>.

        :param p_node: (bathy_db.NodeManager) Un objet de type <caris.bathy.db.NodeManager>.
        :param p_db_name: (str) Le nom de la base de données.
        :return: (bathy_db.Dataset) Un objet de type <class 'caris.bathy.db.Dataset'>.
        :raise: TypeError si p_node n'est pas un objet <caris.bathy.db.NodeManager>.
        :raise: BDError si p_db_name n'est pas un base de données existante dans le p_node.
        :raise: RuntimeError si la base de donnée n'est pas démarrée.
        """
        if not isinstance(p_node, bathy_db.NodeManager):
            type_error = "Il ne s'agit pas d'un objet <caris.bathy.db.NodeManager>."
            self._logger.error(type_error)

            raise TypeError(type_error)

        if p_db_name not in p_node.databases:
            bd_error = "'{}' n'existe pas sur ce NodeManager.".format(p_db_name)
            self._logger.error(bd_error)

            raise BDError(bd_error)

        state = self.get_db_state(p_node, p_db_name)
        if state != bathy_db.DatabaseState.STARTED:
            runtime_error = "'{}' est '{}'.".format(p_db_name, state)
            self._logger.error(runtime_error)

            raise RuntimeError(runtime_error)

        try:
            db = p_node.get_database(p_db_name)

        except RuntimeError as e:
            self._logger.error(e)
            return None

        return db

    @staticmethod
    def get_db_state(p_node: bathy_db.NodeManager, p_db_name: str) -> bathy_db.DatabaseState:
        """
        Méthode permettant de retourner l'état de la base de donnée.

        :param p_node: (bathy_db.NodeManager) <caris.bathy.db.NodeManager>
        :param p_db_name: (str) Le nom de la base de données.
        :return: (caris.bathy.db.DatabaseState) L'état de la base de donnée.
        """
        return p_node.get_database_state(p_db_name)

    @staticmethod
    def get_list_database(p_node: bathy_db.NodeManager) -> List[bathy_db.Dataset]:
        """
        Méthode permettant de retourner la liste des bases de données du serveur.

        :param p_node: (bathy_db.NodeManager) <caris.bathy.db.NodeManager>
        :return: (list[bathy_db.Dataset]) La liste des bases de données sur le serveur.
        """
        if isinstance(p_node, bathy_db.NodeManager):
            return [db for db in p_node.databases]

    @staticmethod
    def get_list_feature_definition_catalogue(p_db: bathy_db.Dataset) -> caris.FeatureDefinition:
        """
        Méthode permettant de retourner la liste de FeatureDefinition comprise dans
        le FeatureCatalogue de la base de données.

        :param p_db: (bathy_db.Dataset) Un objet de type <class 'caris.bathy.db.Dataset'>.
        :return: (list[FeatureDefinition]) Une liste de <class 'caris.FeatureDefinition'>.
        """
        return [domain for domain in p_db.catalogue]

    @staticmethod
    def query_all(p_db: bathy_db.Dataset, p_boid_only: Optional[bool] = True) -> List[Union[str, bathy_db.Feature]]:
        """
        Méthode permettant d'interroger la base de données et de retourner la liste complète
        des BOID ou des features.

        :param p_db: (bathy_db.Dataset) Un objet de type <class 'caris.bathy.db.Dataset'>.
        :param p_boid_only: (bool) True pour obtenir le BOID seulement, False pour des objet
                            <class 'caris.bathy.db.Feature'>.
        :return: list(<class 'caris.bathy.db.Feature'>) ou list(str). Une liste des BOID
                    des features ou une liste d'objet Feature en fonction de p_boid_onlu.
        """
        return [feature.id if p_boid_only else feature for feature in p_db.query_all()]

    @staticmethod
    def query(
            p_db: bathy_db.Dataset, p_feature_type: FeatureType = FeatureType.SURFAC, p_cql: Optional[str] = None,
            p_contains: Optional[caris.Geometry] = None, p_crosses: Optional[caris.Geometry] = None,
            p_intersects: Optional[caris.Geometry] = None, p_disjoint_from: Optional[caris.Geometry] = None,
            p_equal_to: Optional[caris.Geometry] = None, p_within: Optional[caris.Geometry] = None,
            p_overlaps: Optional[caris.Geometry] = None, p_touches: Optional[caris.Geometry] = None, p_boid_only=True
    ) -> List[Union[str, bathy_db.Feature]]:
        """
        Méthode permettant d'interroger la base de données et de retourner la liste les BOID ou des features
        remplissant les critères de la requête.

        :param p_db: (bathy_db.Dataset) Un objet de type <class 'caris.bathy.db.Dataset'>.
        :param p_feature_type: (FeatureType) Le nom du type de feature catalogue {'survey' ou 'surfac'}.
        :param p_cql: (str) Une requête CQL. (ex: "OBJNAM = '3005301'" ou "valsta IS { 'Validated/Valide' } OR valsta IS
                            { 'Not-validated/Non-valide' }")
        :param p_contains: (caris.Geometry) Un objet <class 'caris._py_caris.Geometry'>. Retourne les features qui
                            contiennent complètement la géométrie sans lui touché. L'opposé de p_within.
        :param p_crosses: (caris.Geometry) Un objet <class 'caris._py_caris.Geometry'>. Retourne les features qui ont
                            des points intérieurs en commun avec la geométrie.
        :param p_intersects: (caris.Geometry) Un objet <class 'caris._py_caris.Geometry'>. Retourne les features qui ont
                                au moins un point en commun avec la geométrie. L'opposé de p_disjoint_from.
        :param p_disjoint_from: (caris.Geometry) Un objet <class 'caris._py_caris.Geometry'>. Retourne les features qui
                                    ont aucun point en commun avec la geométrie. L'opposé de p_intersects.
        :param p_equal_to: (Geometry) Un objet <class 'caris._py_caris.Geometry'>. Retourne les features qui sont
                            topologiquement identique à la geométrie.
        :param p_within: (caris.Geometry) Un objet <class 'caris._py_caris.Geometry'>. Retourne les features qui sont
                            complétement à l'intérieur de la geométrie sans lui toucher. L'opposé de p_contains.
        :param p_overlaps: (caris.Geometry Un objet <class 'caris._py_caris.Geometry'>. Retourne les features qui ont
                            des points en commun avec la geométrie, mais pas tous les points. L'intersection des feature
                            et de la geométrie doit avoir la même dimension que les geométries elles-mêmes.
        :param p_touches: (caris.Geometry) Un objet <class 'caris._py_caris.Geometry'>. Retourne les features qui ont au
                            moins un point en commun avec la geométrie, mais aucun point intérieur.
        :param p_boid_only: (bool) True pour obtenir le BOID seulement, False pour des objet
                            <class 'caris.bathy.db.Feature'>.
        :return: list(<class 'caris.bathy.db.Feature'>) ou list(str). Une liste des BOID
                    des features ou une liste d'objet Feature en fonction de p_boid_onlu.
        """
        return [
            feature.id if p_boid_only else feature for feature in p_db.query(
                p_feature_type.value, CQL=p_cql, contains=p_contains, crosses=p_crosses, intersects=p_intersects,
                disjoint_from=p_disjoint_from, equal_to=p_equal_to, within=p_within, overlaps=p_overlaps,
                touches=p_touches
            )
        ]

    @staticmethod
    def create_crs(p_type: CRSType = CRSType.EPSG, p_value: str = '4326') -> caris.CoordinateReferenceSystem:
        """
        Méthode permettant de créer un objet <class 'caris._py_caris.CoordinateReferenceSystem'>.

        :param p_type: (CRSType) Un objet CRSType.
        :param p_value: (str) Le numéro EPSG si p_type=CRSType.EPSG, la string WKT si p_type=CRSType.WKT.
        :return: Un objet <class 'caris._py_caris.CoordinateReferenceSystem'>.
        """
        return caris.CoordinateReferenceSystem(p_type.value, p_value)

    @staticmethod
    def create_geometry(p_crs: caris.CoordinateReferenceSystem, p_wkt: str) -> caris.Geometry:
        """
        Méthode permettant de créer un objet <class 'caris._py_caris.Geometry'>.

        :param p_crs: (obj) Un objet <class 'caris._py_caris.CoordinateReferenceSystem'>.
        :param p_wkt: (str) Le WKT de la geométrie.
        :return: Un objet <class 'caris._py_caris.Geometry'>.
        """
        return caris.Geometry(p_crs, p_wkt)

    def get_feature(
            self, p_input: Union[str, bathy_db.Feature, URI], p_db: Optional[bathy_db.Dataset] = None
    ) -> bathy_db.Feature:
        """
        Méthode permettant de retourner un objet <class 'caris.bathy.db.Feature'>.

        :param p_input: (Union[str, caris.bathy.db.Feature, URI]) L'ID du feature ou un objet
                            <class 'caris.bathy.db.Feature'> ou un objet URI.
        :param p_db: (caris.bathy.db.Dataset) Un objet de type  <class 'caris.bathy.db.Dataset'>.
                        Obligatoire si p_input est un featureId.
        :return: Un objet <class 'caris.bathy.db.Feature'>.
        """
        if is_uri(p_input):
            return self._get_feature_from_uri(p_input)

        if isinstance(p_input, str) and p_db is not None:
            return self._get_feature_by_id(p_input, p_db)

        if isinstance(p_input, caris.bathy.db.Feature):
            return p_input

    @staticmethod
    def _get_feature_by_id(p_boid: str, p_db: bathy_db.Dataset) -> bathy_db.Feature:
        """
        Métode permettant de récupérer un feature dans la base de données à partir de son ID.

        :param p_boid: (str) L'ID du feature.
        :param p_db: (caris.bathy.db.Dataset) Un objet de type <class 'caris.bathy.db.Dataset'>.
        :return: Un objet <class 'caris.bathy.db.Feature'>.
        """
        return p_db.get_feature(p_boid)

    def _get_feature_from_uri(self, p_uri: URI) -> bathy_db.Feature:
        """
        Méthode permettant de retourner un objet <class 'caris.bathy.db.Feature'> à
        partir d'un URI.

        :param p_uri: (URI) Un objet URI représentant 'bdb://username:password@hostmane/bathydatabasename/featureId'.
        :return: (Feature) Un objet <class 'caris.bathy.db.Feature'>.
        """
        feature = None

        if is_uri(p_uri):
            return self.get_feature(
                p_uri.feature_id,
                self.connect_database(
                    self.connect_node(
                        p_uri.username,
                        p_uri.password,
                        p_uri.host_name
                    ), p_uri.bathy_database_name
                )
            )

    def get_attributes_from_feature(
            self, p_input: Union[str, bathy_db.Feature, URI], p_db: Optional[bathy_db.Dataset] = None,
            p_type: Optional[AttributeType] = None
    ) -> Union[caris.CoordinateReferenceSystem, List[str], str]:
        """
        Méthode permettant de retourner un objet <class 'caris._py_caris.AttributeDictionary'> ou une
        liste d'information concernant les attributs d'un feature.

        :param p_input: Union[str, caris.bathy.db.Feature, URI] L'ID du feature ou un objet
                            <class 'caris.bathy.db.Feature'> ou un URI au format
                            'bdb://username:password@hostmane/bathydatabasename/featureId'.
        :param p_db: (caris.bathy.db.Dataset) Un objet de type
                        <class 'caris.bathy.db.Dataset'>. Obligatoire si p_input est un featureId.
        :param p_type: (AttributeType) Le type de retour désiré {None: <class 'caris._py_caris.AttributeDictionary'>,
                                                 AttributeType.ITEMS : un tuple (clé, valeur),
                                                 AttributeType.KEYS : la clé des attributs,
                                                 AttributeType.VALUES: la valeur des attributs,
                                                 AttributeType.XML: représentation XML des attributs}.
        :return: Un objet <class 'caris._py_caris.AttributeDictionary'> ou une liste d'information selon le
                    paramètre p_type.
        """
        feature_attributes = self.get_feature(p_input, p_db=p_db).attributes

        if p_type is None:
            return feature_attributes

        attribute_type_dict = {
            AttributeType.ITEMS: feature_attributes.items,
            AttributeType.VALUES: feature_attributes.values,
            AttributeType.KEYS: feature_attributes.keys,
            AttributeType.XML: feature_attributes.to_xml
        }

        return attribute_type_dict[p_type]()

    def download_coverage(
            self, p_input: Union[str, bathy_db.Feature, URI], p_output: str, p_db: Optional[bathy_db.Dataset] = None,
            p_overwrite: Optional[bool] = True, p_set_time: Optional[bool] = True
    ) -> None:
        """
        Méthode permettant de télécharger un feature de la base de données.

        :param p_input: Union[str, caris.bathy.db.Feature, URI] L'ID du feature ou un objet
                            <class 'caris.bathy.db.Feature'> ou un URI au format
                            'bdb://username:password@hostmane/bathydatabasename/featureId'.
        :param p_output: (str) Le chemin du fichier .csar de sortie.
        :param p_db: (caris.bathy.db.Dataset) Un objet de type
                        <class 'caris.bathy.db.Dataset'>. Obligatoire si p_input est un featureId.
        :param p_overwrite; (bool) True pour écraser le fichier p_output s'il existe déjà, False sinon.
        :param p_set_time: (bool) True pour écrire les valeurs du SURSTA et du SUREND du feature comme valeur
                            du Minimum Time et Maximum Time du coverage, False sinon.
        """
        if p_overwrite:
            delete_csar(p_output)

        feature = self.get_feature(p_input, p_db=p_db)
        coverage = feature.coverage
        coverage.create_copy(p_output)

        if p_set_time:
            self.set_coverage_time_from_attribute(feature, p_output)

        xml = et.fromstring(self.get_attributes_from_feature(feature, p_db=p_db, p_type=AttributeType.XML))
        with open('{}.object.xml'.format(os.path.splitext(p_output)[0]), 'wb') as output_xml:
            output_xml.write(et.tostring(xml, xml_declaration=True,  pretty_print=True))

    def update_coverage(
            self, p_input: Union[str, bathy_db.Feature, URI], p_coverage: str, p_db: Optional[bathy_db.Dataset] = None
    ) -> None:
        """
        Méthode permettant de remplacer le coverage d'un objet un objet
        <class 'caris.bathy.db.Feature'>.

        :param p_input: Union[str, caris.bathy.db.Feature, URI] L'ID du feature ou un objet
                            <class 'caris.bathy.db.Feature'> ou un URI au format
                            'bdb://username:password@hostmane/bathydatabasename/featureId'.
        :param p_coverage: (str) Le chemin du fichier .csar servant à la mise à jour.
        :param p_db: (caris.bathy.db.Dataset) Un objet de type
                        <class 'caris.bathy.db.Dataset'>. Obligatoire si p_input est un featureId.
        :raise: ValueError lorsque le fichier .csar d'entrée est inexistant.
        """
        if not os.path.exists(p_coverage):
            raise ValueError('Fichier *.csar inexistant.')

        feature = self.get_feature(p_input, p_db=p_db)
        feature.upload_coverage(p_coverage)

    def upload_coverage(
            self, p_db: Optional[bathy_db.Dataset], p_coverage: str,
            p_feature_type: Optional[FeatureType] = FeatureType.SURFAC, p_objnam: Optional[str] = None
    ) -> Tuple[bathy_db.Feature, str]:
        """
        Méthode permettant de charger un fichier .csar dans une base de données.

        :param p_db: (caris.bathy.db.Dataset) Un objet de type <class 'caris.bathy.db.Dataset'>.
        :param p_coverage: (str) Le chemin du fichier .csar servant à la mise à jour.
        :param p_feature_type: (FeatureType) Le nom du type de feature catalogue {'survey' ou 'surfac'}.
        :param p_objnam: (str) Le OBJNAM du feature. Si None, les 7 premiers caractères du nom du
                            coverage seront conservés, plus _sup ou _valid si présent.
        :raise: FileNotFoundError lorsque le fichier .csar d'entrée est inexistant.
        :raise: GeomError lorsqye la geométrie du bounding polygon du fichier .csar est invalide.
        :raise: UniqueKeyError lorsque un feature de la BD à déjà le même OBJNAM.
        :return: (Tuple[bathy_db.Feature, str]) Un objet Feature et la valeur de l'OBJNAM.
        """
        if not os.path.exists(p_coverage):
            raise FileNotFoundError('Fichier {} inexistant.'.format(p_coverage))

        # Établissement de l'OBJNAM.
        if p_objnam is None:
            obj_name = os.path.split(os.path.splitext(p_coverage)[0])[-1]
            if not bool(re.match(r'\d{7}_sup\d*', obj_name)) and not bool(re.match(r'\d{7}_valid', obj_name)):
                obj_name = obj_name[0:7]  # todo à valider le comportement
        else:
            obj_name = p_objnam

        # Si l'OBJNAM existe déjà dans la BD.
        if self.query(p_db, p_cql="OBJNAM = '{}'".format(obj_name)):
            raise UniqueKeyError(
                f"Un fichier avec l'OBJNAM '{obj_name}' est déjà présent dans la base de données '{p_db.name}'. "
                f"Ce faisant, le fichier n'a pas été chargé."
            )  # todo à mettre optionel

        # Création d'un objet Geometry.
        crs = self.create_crs(p_type=CRSType.WKT, p_value=cu.get_coverage(p_coverage).wkt_cosys)
        geom = self.create_geometry(crs, cu.get_bounding_polygon(p_coverage))

        # Validation de la géométrie.
        if not geom.validate()[0]:
            raise GeomError(f"La geométrie du fichier est invalide. Impossible de charger le fichier '{obj_name}'.")

        # Création de l'objet Feature dans la DB.
        feature = p_db.create_feature(p_feature_type.value, geom)
        p_db.commit()
        time.sleep(1)  # Attendre après le commit.

        # Chargement du coverage.
        try:
            feature.upload_coverage(p_coverage)

        except RuntimeError as e:
            time.sleep(5)  # Attendre après le commit et réessayer.
            feature.upload_coverage(p_coverage)

        return feature, obj_name

    @staticmethod
    def get_items_from_xml(p_coverage: str) -> Dict[str, str]:
        """
        Méthode permettant de récuper les tags et les valeurs d'un fichier '*.object.xml' associé
        à un fichier '*.csar'.

        :param p_coverage: (str) Le chemin du fichier .csar.
        :return: (Dict[str, str]) Un dictionnaire contenant pour les clés les tags et pour les valeurs les valeurs
                    associées au tag.
        """
        xml = f'{os.path.splitext(p_coverage)[0]}.object.xml'
        root = et.parse(xml)
        dict_attributes = dict()

        # todo utiliser la méthode from_xml

        if root.getroot().tag == 'BDB_Simple_Attributes':
            for child in root.iter():
                key = None
                val = None
                if child.tag.strip() == 'Attribute':
                    key = child.get('name').strip()
                    for value in child.iter():
                        val = value.text.strip()
                if key is not None and val is not None:
                    dict_attributes[key] = val

        elif root.getroot().tag == 'Attributes':
            for attribute in root.iter():
                if attribute.text.strip() != '':
                    dict_attributes[attribute.tag.strip()] = attribute.text.strip()

        return dict_attributes

    def modify_attributes_from_xml(self) -> None:
        # new_feature.attributes.from_xml(attributes_xml)
        # todo utiliser la méthode from xml
        pass

    def modify_attribute(
            self, p_input: Union[str, bathy_db.Feature, URI],  p_db: bathy_db.Dataset, p_value: str,
            p_attribute: str = 'INFORM', p_mode: str = 'overwrite', p_feature_type: FeatureType = FeatureType.SURFAC
    ) -> None:
        """
        Méthode permettant de modifier la valeur d'un attribut d'un objet
        <class 'caris.bathy.db.Feature'>.

        :param p_input: Union[str, caris.bathy.db.Feature, URI] L'ID du feature ou un objet
                            <class 'caris.bathy.db.Feature'> ou un URI au format
                            'bdb://username:password@hostmane/bathydatabasename/featureId'.
        :param p_db: (caris.bathy.db.Dataset) Un objet de type
                        <class 'caris.bathy.db.Dataset'>.
        :param p_value: (str) La valeur de l'attribut.
        :param p_attribute: (str) La clé de l'attribut.
        :param p_mode: (str) {'append': pour ajouter à la suite de la valeur actuelle (ex : pour le champ INFORM),
                              'overwrite': pour remplacer la valeur}.
        :param p_feature_type: (str) Le nom du type de feature catalogue {'survey' ou 'surfac'}.
        :raise: KeyCatalogueError lorsque p_attribute n'existe pas dans le catalogue.
        :raise: ValueCatalogueError lorsque p_value n'est pas une valeur permise dans le domaine de p_attritube.
        """
        if p_attribute not in self.get_attributes_from_catalogue(
                p_db, p_type=AttributeType.KEYS,
                p_feature_type=p_feature_type
        ):
            raise KeyCatalogueError(
                f"L'attribut '{p_attribute}' n'existe pas dans le catalogue de la base de données '{p_db.name}'."
            )
        # todo modifer pour untiliser la methode valide

        feature = self.get_feature(p_input, p_db)

        values = p_value.split(',')
        for val in values:
            if not self._bool_is_valid_value(p_db, val, p_attribute, p_feature_type=p_feature_type):
                raise ValueCatalogueError("'{}' n'est pas une valeur possible pour l'attribut '{}'."
                                          .format(val, p_attribute))

        if p_mode == 'overwrite':
            p_value = p_value
        if p_mode == 'append':
            # todo si string vs list
            p_value = self.get_attribute_value_from_feature(p_input, p_db=p_db, p_attribute=p_attribute) + p_value

        self.get_attributes_from_feature(feature)[p_attribute] = p_value

        # todo validation
        # try:
        #     surfac.attributes.validate()
        # except RuntimeError as e:
        #     print("ERROR: Attributes are invalid, rolling back changes.")
        #     dataset.rollback()
        # else:
        #     print("Saving dataset changes.")
        #     dataset.commit()

        p_db.commit()

    def _bool_is_valid_value(
            self, p_db: bathy_db.Dataset, p_value: str, p_attribute: str,
            p_feature_type: FeatureType = FeatureType.SURFAC
    ) -> bool:
        """
        Méthode permettant de valider si la valeur est possible pour un certain attribut selon le catalogue de
        la base de données.

        :param p_db: (caris.bathy.db.Dataset) Un objet de type <class 'caris.bathy.db.Dataset'>.
        :param p_value: (str) La valeur de l'attribut.
        :param p_attribute: (str) La clé de l'attribut.
        :param p_feature_type: (FeatureType) Le nom du type de feature catalogue {'survey' ou 'surfac'}.
        :return: True si la valeur est permise dans le domaine du catalogue, False sinon.
        """
        is_valid = True
        domain = self.get_possible_values_from_definition(p_db, p_attribute=p_attribute, p_feature_type=p_feature_type)

        if domain['type'] == 'enum':
            keys = domain['values'].keys()
            values = domain['values'].values()
            value = p_value.split(',')
            for val in value:
                if val not in keys and val not in values:
                    is_valid = False

        # todo valider les autres type

        # todo utiliser la méthode validate de la classe AttributeDictionary

        return is_valid

    def get_attribute_value_from_feature(
            self, p_input: Union[str, bathy_db.Feature, URI], p_db: Optional[bathy_db.Dataset] = None,
            p_attribute: str = 'valsta'
    ) -> str:
        """
        Méthode permettant de retourner la valeur d'un attribut d'un objet
        <class 'caris.bathy.db.Feature'>.

        :param p_input: Union[str, caris.bathy.db.Feature, URI] L'ID du feature ou un objet
                            <class 'caris.bathy.db.Feature'> ou un URI au format
                            'bdb://username:password@hostmane/bathydatabasename/featureId'.
        :param p_db: (caris.bathy.db.Dataset) Un objet de type <class 'caris.bathy.db.Dataset'>.
                        Obligatoire si p_input est un featureId.
        :param p_attribute: (str) La clé de l'attribut.
        :return: (str) La valeur de l'attribut.
        """
        feature = self.get_feature(p_input, p_db=p_db)

        return self.get_attributes_from_feature(feature)[p_attribute]

    @staticmethod
    def get_attributes_from_catalogue(
            p_db: bathy_db.Dataset, p_feature_type: FeatureType = FeatureType.SURFAC, p_type: AttributeType = None
    ) -> caris.AttributeDefinitionDictionary:
        """
        Méthode permettant de retourner un objet <class 'caris._py_caris.AttributeDefinitionDictionary'> ou une
        liste d'information concernant les attributs de l'objet <class 'caris._py_caris.FeatureDefinition'>.

        :param p_db: (caris.bathy.db.Dataset) Un objet de type <class 'caris.bathy.db.Dataset'>.
        :param p_feature_type: (FeatureType) Le nom du type de feature catalogue {'survey' ou 'surfac'}.
        :param p_type: Le type de retour désiré {None: <class 'caris._py_caris.AttributeDefinitionDictionary'>,
                                         AttributeType.ITEMS: un tuple (clé, valeur),
                                         AttributeType.KEYS: la clé des attributs,
                                         AttributeType.VALUES: la valeur des attributs}.
        :return:  Un objet <class 'caris._py_caris.AttributeDefinitionDictionary'> ou une liste d'information selon le
                    paramètre p_type.
        """
        catalogue_attributes = p_db.catalogue.get_definition(p_feature_type.value).attributes

        if p_type is None:
            return catalogue_attributes

        attribute_type_dict = {
            AttributeType.ITEMS: catalogue_attributes.items,
            AttributeType.VALUES: catalogue_attributes.values,
            AttributeType.KEYS: catalogue_attributes.keys
        }

        return attribute_type_dict[p_type]()

    def get_possible_values_from_definition(
            self, p_db: bathy_db.Dataset, p_attribute: str = 'valsta', p_feature_type: FeatureType = FeatureType.SURFAC
    ) -> Dict[str, Any]:
        """
        Méthode permettant de retourne un dictionnaire contenant les informations sur les valeurs
        possibles pour un attribut du catalogue de la base de données.

        :param p_db: (caris.bathy.db.Dataset) Un objet de type <class 'caris.bathy.db.Dataset'>.
        :param p_attribute: (str) La clé de l'attribut.
        :param p_feature_type: (FeatureType) Le nom du type de feature catalogue {'survey' ou 'surfac'}.
        :return: (dict) Contenant les informations sur les valeurs possibles pour cet attribut sous la forme
                        dict('type':['enum', 'length' ou 'range'],
                            ['min':[la valeur ou la longeur minimale permise]](pour 'type' 'length' et 'range'),
                            ['max':[la valeur ou la longeur maximale permise]](pour 'type' 'length' et 'range'),
                            ['values': dicttionnaire des valeurs possibles](pour 'type' 'enum')).
        """
        attribute = self.get_attributes_from_catalogue(p_db, p_feature_type=p_feature_type)[p_attribute]

        if not isinstance(attribute, caris.AttributeDefinition):
            return None

        attribute_type = attribute.type

        if isinstance(attribute_type, caris.EnumType):
            return {
                'type': 'enum',
                'values': attribute.type.possible_values
            }

        if isinstance(attribute_type, caris.StringType):
            return {
                'type': 'length',
                'min': attribute_type.min_length,
                'max': attribute_type.max_length
            }

        if isinstance(attribute_type, caris.MeasurementType) or \
                isinstance(attribute_type, caris.DateType) or \
                isinstance(attribute_type, caris.DateTimeType) or \
                isinstance(attribute_type, caris.IntegerType) or \
                isinstance(attribute_type, caris.DoubleType) or \
                isinstance(attribute_type, caris.QuantityType):
            return {
                'type': 'range',
                'min': attribute_type.min_value,
                'max': attribute_type.max_value
            }

    def set_coverage_time_from_attribute(
            self, p_input:  Union[str, bathy_db.Feature, URI], p_coverage: str, p_db: bathy_db.Dataset = None,
            p_only_if_diff: bool = True
    ) -> None:
        """
        Méthode permettant de changer la valeur du Minimum Time et Maximum Time d'un fichier .csar
        à partir des attributs SURSTA et SUREND d'un feature dans la base de données.

        :param p_input: Union[str, caris.bathy.db.Feature] L'ID du feature ou un objet
                            <class 'caris.bathy.db.Feature'> ou un URI au format
                            'bdb://username:password@hostmane/bathydatabasename/featureId'.
        :param p_coverage: (str) Le chemin du fichier .csar à mettre à jour.
        :param p_db: (caris.bathy.db.Dataset) Un objet de type <class 'caris.bathy.db.Dataset'>.
                        Obligatoire si p_input est un featureId.
        :param p_only_if_diff: (bool) True pour procéder à la modification seulement s'il y a une différence
                                entre la date du feature et du coverage, False sinon.
        """
        feature = self.get_feature(p_input, p_db=p_db)
        sursta = self.get_attribute_value_from_feature(feature, p_db=p_db, p_attribute='SURSTA')
        surend = self.get_attribute_value_from_feature(feature, p_db=p_db, p_attribute='SUREND')
        min_time_coverage, max_time_coverage = cu.get_time_min_max(p_coverage)

        min_time = sursta[0:4] + '-' + sursta[4:6] + '-' + sursta[6:8] + 'T12:00:00'
        max_time = surend[0:4] + '-' + surend[4:6] + '-' + surend[6:8] + 'T12:00:00'

        if p_only_if_diff and min_time_coverage is not None and max_time_coverage is not None:
            if sursta[0:4] == min_time_coverage[0:4] and sursta[4:6] == min_time_coverage[5:7] and \
               sursta[6:8] == min_time_coverage[8:10]:
                min_time = None
            if surend[0:4] == max_time_coverage[0:4] and surend[4:6] == max_time_coverage[5:7] and \
               surend[6:8] == max_time_coverage[8:10]:
                max_time = None
            if min_time is not None or max_time is not None:
                cu.set_time(p_coverage, min_time, max_time)
        else:
            cu.set_time(p_coverage, min_time, max_time)   # todo à mettre dans coverage_util
            
    def get_next_sup(self, p_input: str, p_db: bathy_db.Dataset) -> int:
        """
        Méthode permettant de retourner le prochain numéro _sup de disponible
        dans la base de donnée pour un objnam.

        :param p_input: (str) L'objnam d'un fichier dans la base données.
        :param p_db: (caris.bathy.db.Dataset) Un objet de type <class 'caris.bathy.db.Dataset'>.
        :return: (int) Le prochain numéro _sup de disponible dans la base de données.
        """
        features = self.query(p_db, p_cql="OBJNAM LIKE '{}%'".format(p_input), p_boid_only=False)

        if len(features) == 0:
            return None

        numbers = []
        for feat in features:
            if bool(re.match(r'\d{7}_sup\d*', feat['OBJNAM'])):
                if bool(re.match(r'\d', feat['OBJNAM'][-1])):
                    numbers.append(int(feat['OBJNAM'][-1]))
                else:
                    numbers.append(1)

        return (max(numbers) + 1) if len(numbers) != 0 else None


class BDBError(Exception):
    """
    Classe de base pour les erreurs avec BDB
    """
    ...


class HostError(BDBError):
    """
    Erreur levée lorsqu'il est impossible de se connecter avec l'hôte.
    """
    ...


class AuthenticationError(BDBError):
    """
    Erreur levée lorsqu'il y a un échec de l'authentification par mot de passe pour l'utilisateur.
    """
    ...


class BDError(BDBError):
    """
    Erreur levée lorsqu'il la base de données est inexistante pour cet hôte.
    """
    ...


class KeyCatalogueError(BDBError):
    """
    Erreur levée lorsque l'attribut n'existe pas dans le catalogue du schéma.
    """
    ...


class ValueCatalogueError(BDBError):
    """
    Erreur levée lorsque la valeur n'est pas possible pour cet attribut dans le catalogue du schéma.
    """
    ...


class GeomError(BDBError):
    """
    Erreur levée lorsqu'il y a une erreur de géométrie avec le 'surfac'.
    """
    ...


class UniqueKeyError(BDBError):
    """
    Erreur levée lorsqu'il y a déjà un objet dans la base de données avec le même identifiant unique.
    """
    ...


def bathydatabase_diagnostics_tool(self):
    ...
    # todo


def delete_csar(p_csar_path):
    """
    Méthode permettant de supprimer un fichier .csar et ses fichiers associés (.csar0 et .object.xml)

    :param p_csar_path: Le chemin du fichier .csar à supprimer.
    :raise: IOError si le fichier .csar est verrouiller par une autre application.
    """
    if os.path.exists('{}.lock'.format(p_csar_path)):
        raise IOError('Le fichier .csar est verrouiller par une autre application.')

    if os.path.exists(p_csar_path):
        os.remove(p_csar_path)
    if os.path.exists('{}0'.format(p_csar_path)):
        os.remove('{}0'.format(p_csar_path))
    if os.path.exists('{}.object.xml'.format(os.path.splitext(p_csar_path)[0])):
        os.remove('{}.object.xml'.format(os.path.splitext(p_csar_path)[0]))


if __name__ == "__main__":
    db_name = 'bdb_que_rest'
    host = '142.130.48.49'
    user = 'bilodeauy'
    pw = 'bilodeauy'

    # todo test logger

    bdb = BathyDataBaseUtils()
    nm = bdb.connect_node(user, pw, host)
    db = bdb.connect_database(nm, db_name)

    boid = 'dc348742-a50c-11ea-8000-9457a56b97f0'
    out = r'D:\HDCS_Data\BDBTest\from_py.csar'

    # uri = URI(username=user, password=pw, host_name=host, bathy_database_name=db_name, feature_id=boid)
    # print(uri)

    coverage = r'D:\HDCS_Data\Test_chenal_bdb\21g0841251g1_final.csar'

    # crs_wkt = cu.get_cosys_wkt(coverage)
    # bp_wkt = cu.get_bounding_polygon(coverage)

    print(bdb.get_list_feature_definition_catalogue(db))

    # feat = bdb.get_feature(boid, db)
    # print(bdb.get_attributes_from_feature(feat, p_type=AttributeType.VALUES))

    features = bdb.query(
        db,
        p_cql="CoverageResolution > 1 AND (valsta IS { 'Validated/Valide' } AND CATZOC != 'zone of confidence A1')",
        p_boid_only=False
    )

    print(features)
    print(len(features))

    # for feature in features:
    #     print(bdb.get_attributes_from_feature(feature, p_type=AttributeType.ITEMS))

    # crs = bdb.create_crs(p_type=CRSType.WKT, p_value=cu.get_cosys_wkt(coverage))
    # geom = bdb.create_geometry(crs, cu.get_bounding_polygon(coverage))

    # feature = bdb.get_feature(boid, db)
    # print(feature.attributes)
    # print(bdb.get_attributes_from_feature(feature, p_type=AttributeType.ITEMS))

    # print(bdb.get_attributes_from_catalogue(db, p_type=AttributeType.ITEMS))
    # print(bdb.get_possible_values_from_definition(db, p_attribute='CoverageName'))

    # catalogue = bdb.get_list_feature_definition_catalogue(db)
    # print(catalogue[1].attributes)
    # for att in catalogue[1].attributes:
    #     print(bdb.get_possible_values_from_definition(db, p_attribute=att))

    # bdb.set_coverage_time_from_attribute(boid, out, db)

    # bdb.download_coverage(boid, out, db)

    # dict_att = bdb.get_items_from_xml(coverage)
    #
    # print(bdb.get_items_from_xml(coverage))

    # for item in bdb.get_attributes_from_catalogue(db, p_type=AttributeType.KEYS):
    #     poss = bdb.get_possible_values_from_definition(db, p_attribute=item)
    #     print(poss)

    # bdb.update_coverage(feature, out)

    # attributes = bdb.get_attributes_from_feature(boid, db)
    # print(attributes['valsta'])
    # xml = bdb.get_attributes_from_feature(boid, db, p_type=AttributeType.XML)
    # print(xml)
    # items = bdb.get_attributes_from_feature(feature, p_type=AttributeType.ITEMS)
    # print(items)

    # bdb.download_coverage(boid, out, db)
    # bdb.download_coverage(feature, out)
    # bdb.download_coverage(uri, out)

    # geom = bdb.create_geometry(bdb.create_crs('WKT', crs_wkt), bp_wkt)
    # features = bdb.query(db, p_cql="valsta IS { 'Validated/Valide' } OR valsta IS { 'Not-validated/Non-valide' }",
    #                      p_boid_only=False)
    #
    # compte = 0
    # for feature in features:
    #     print(feature)
    #     compte += 1
    #
    # print(compte)
