from typing import Dict

from . exceptions_config import (
    SchemaError,
    SchemaInfoSchemaError,
    ConfigAPISchemaError,
    ConfigEnvironmentSchemaError,
    ConfigCarisBatchSchemaError,
    ConfigGUISchemaError
)
from . import ids_environment_config as ids
from . models_config import CarisAPIConfig, CarisBatchConfig, EnvironmentConfig, GUIConfig, SchemaInfo


ConfigDict = Dict[str, str]


def get_schema_config_from_dict(p_config_dict: ConfigDict) -> SchemaInfo:
    """
    Fonction permettant de retourner un objet SchemaInfo contenant les informations sur le schema.

    :param p_config_dict: (ConfigDict) Un dictionnaire qui est structuré tel que :
                    {Version' : str|int}

    :return: (SchemaInfo) Un objet SchemaInfo.
    :raise SchemaInfoSchemaError si le schéma n'est pas respecté.
    """
    try:
        return SchemaInfo(**p_config_dict)

    except TypeError:
        raise SchemaInfoSchemaError(
            "Le schéma suivant doit être respecté : {Version' : str|int}."
        )


def get_caris_api_config_from_dict(p_config_dict: ConfigDict) -> CarisAPIConfig:
    """
    Fonction permettant de retourner un objet CarisAPIConfig contenant les informations de l'API de Caris.

    :param p_config_dict: (ConfigDict) Un dictionnaire qui est structuré tel que :
                    {Base_path' : str, 'Software' : str, 'Version' : str, 'Python_version' : str}

    :return: (CarisAPIConfig) Un objet CarisAPIConfig.
    :raise ConfigAPISchemaError si le schéma n'est pas respecté.
    """
    try:
        return CarisAPIConfig(**p_config_dict)

    except TypeError:
        raise ConfigAPISchemaError(
            "Le schéma suivant doit être respecté : {Base_path' : str, 'Software' : str, 'Version' : str, "
            "'Python_version' : str}."
        )


def get_caris_batch_config_from_dict(p_config_dict: ConfigDict) -> CarisBatchConfig:
    """
    Fonction permettant de retourner un objet CarisBatchConfig contenant les informations de Caris Batch utility.

    :param p_config_dict: (ConfigDict) Un dictionnaire qui est structuré tel que :
                                {'Base_path': str, 'Software': str, 'Version': str}

    :return: (CarisBatchConfig) Un objet CarisAPIConfig.
    :raise ConfigCarisBatchSchemaError si le schéma n'est pas respecté.
    """
    try:
        return CarisBatchConfig(**p_config_dict)

    except TypeError:
        raise ConfigCarisBatchSchemaError(
            "Le schéma suivant doit être respecté : {'Base_path': str, 'Software': str, 'Version': str}."
        )


def get_gui_config_from_dict(p_config_dict: ConfigDict) -> GUIConfig:
    """
    Fonction permettant de retourner un objet GUIConfig contenant les informations des GUI.

    :param p_config_dict: (ConfigDict) Un dictionnaire qui est structuré tel que : {'Theme': str, 'Style': str}

    :return: (GUIConfig) Un objet GUIConfig.
    :raise ConfigGUISchemaError si le schéma n'est pas respecté.
    """
    try:
        return GUIConfig(**p_config_dict)

    except TypeError:
        raise ConfigGUISchemaError(
            "Le schéma suivant doit être respecté : {'Theme': str, 'Style': str}."
        )


def get_environment_config_from_dict(p_config_dict: Dict[str, ConfigDict]) -> EnvironmentConfig:
    """
    Fonction permettant de retourner un objet EnvironmentConfig contenant les informations de Caris Batch utility pour
    Base Editor et Hips and Sips ainsi que pour l'API de Caris et du GUI.

    :param p_config_dict: (Dict[str, ConfigDict]) Un dictionnaire qui est structuré tel que :
                    {'Schema Info': {'Version': str|int}
                     'Caris API': {'Base_path': str, 'Software': str, 'Version': str, 'Python_version': str},
                     'Caris Batch HIPS and SIPS': {'Base_path': str, 'Software': str, 'Version': str},
                     'Caris Batch BASE Editor': {'Base_path': str, 'Software': str, 'Version': str},
                     'GUI': {'Theme': str, 'Style': str}
                     }

    :return: (ConfigEnvironmentSchemaError) Un objet EnvironmentConfig.
    :raise ConfigGUISchemaError si le schéma n'est pas respecté.
    """
    try:
        return EnvironmentConfig(
            get_schema_config_from_dict(p_config_dict[ids.SCHEMA]),
            get_caris_api_config_from_dict(p_config_dict[ids.CARIS_API_CONFIG]),
            get_caris_batch_config_from_dict(p_config_dict[ids.CARIS_BATCH_BE]),
            get_caris_batch_config_from_dict(p_config_dict[ids.CARIS_BATCH_HIPS]),
            get_gui_config_from_dict(p_config_dict[ids.GUI])  # todo initialiser seulement ce qui est présent
        )

    except SchemaError:
        raise ConfigEnvironmentSchemaError(
            "Le schéma suivant doit être respecté : {'Schema Info': {'Version': str|int} 'Caris API': "
            "{'Base_path': str, 'Software': str, 'Version': str, 'Python_version': str}, 'Caris Batch HIPS and SIPS': "
            "{'Base_path': str, 'Software': str, 'Version': str}, 'Caris Batch BASE Editor': "
            "{'Base_path': str, 'Software': str, 'Version': str}, 'GUI': {'Theme': str, 'Style': str}}."
        )
