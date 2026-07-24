from functools import partial
import os
from typing import Callable, Dict, Any, Optional
from shutil import copyfile
import sys

from . caris_module import CarisModuleImporter
from . exceptions_config import VersionError
from . schema_importer import EnvironmentConfig, get_environment_config_from_dict
from . import ids_environment_config as ids

from chs_lib.config_adapter_utils.config_adapter import get_config_from_factories, Config


CONFIG_PATH = os.path.join(os.getenv(ids.PROGRAMDATA), ids.TOOLS)
CONFIG_FILE_PATH = os.path.join(CONFIG_PATH, ids.CONFIG_FILE)
SOURCE_FILE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), ids.CONFIG_FILE)

ConfigDict = Dict[str, Any]


class ConfigManager:
    def __init__(self, user_config: Config, source_config: Config) -> None:
        """
        Construteur de la classe.

        :param user_config: (Config) Un objet Config représentant les configurations de l'usager.
        :param source_config: (Config) Un objet Config représentant les configurations source.
        """
        self.user_config = user_config
        self.source_config = source_config

    def get_user_config_to_dict(self) -> ConfigDict:
        """
        Méthode permettant d'obtenir les configurations de l'usager sous forme de dictionnaire.

        :return: (ConfigDict) Un dictionnaire contenant les informations de configuration.
        """
        return self.user_config.configuration

    def get_source_config_to_dict(self) -> ConfigDict:
        """
        Méthode permettant d'obtenir les configurations source sous forme de dictionnaire.

        :return: (ConfigDict) Un dictionnaire contenant les informations de configuration source.
        """
        return self.source_config.configuration


class GlobalConfigManager(ConfigManager):
    def __init__(self, user_config: Config, source_config: Config):
        """
        Construteur de la classe.

        :param user_config: (Config) Un objet Config représentant les configurations de l'usager.
        :param source_config: (Config) Un objet Config représentant les configurations source.

        Les fichiers de configuration doivent respecter le schéma de la classe EnvironmentConfig.
        """
        super().__init__(user_config, source_config)
        self.environment = self.get_environment_config_user()
        self.environment_source = self.get_environment_config_source()

    def get_user_config_version(self) -> int:
        """
        Méthode permettant de récupérer la version du fichier de configuration.

        :return: (int) La version du fichier de configuration.
        """
        return self.environment.SCHEMA.Version

    def get_source_config_version(self) -> int:
        """
        Méthode permettant de récupérer la version du fichier de configuration source.

        :return: (int) La version du fichier de configuration source.
        """
        return self.environment_source.SCHEMA.Version

    def update_user_config_from_source_config(self, output_file: Optional[str] = None) -> None:
        """
        Méthode permettant de mettre à jour le fichier de configuration à partir du fichier source.

        :param output_file: (str) Le fichier de configuration pour enregistrer les mises à jour.
        """
        self.user_config.update_config(self.get_source_config_to_dict())
        self.user_config.config[ids.SCHEMA][ids.VERSION] = self.get_source_config_version()
        if output_file is not None:
            self.user_config.write_config_to_file(output_file)

    def get_environment_config_user(self) -> EnvironmentConfig:
        """
        Méthode permettant d'instancier un objet EnvironmentConfig à partir du fichier de configuration.

        :return: (EnvironmentConfig) Un objet EnvironmentConfig.
        """
        config_dict = self.get_user_config_to_dict()

        return get_environment_config_from_dict(config_dict)

    def get_environment_config_source(self) -> EnvironmentConfig:
        """
        Méthode permettant d'instancier un objet EnvironmentConfig à partir du fichier de configuration source.

        :return: (EnvironmentConfig) Un objet EnvironmentConfig.
        """
        config_dict = self.get_source_config_to_dict()

        return get_environment_config_from_dict(config_dict)

    def get_caris_module(self) -> CarisModuleImporter:
        """
        Méthode permettant d'instancier un objet CarisModuleImporter à partir du fichier de configuration.

        :return: (CarisModuleImporter) Un objet CarisModuleImporter.
        """
        return CarisModuleImporter(self.environment.API)

    def get_caris_batch_be(self) -> str:
        """
        Méthode permettant de récupérer l'environnement de Caris Batch pour BE.
        """
        return self.environment.BE.Caris_batch

    def get_caris_batch_hips(self) -> str:
        """
        Méthode permettant de récupérer l'environnement de Caris Batch pour HIPS.
        """
        return self.environment.HIPS.Caris_batch

    def validate_setting_api(self, with_action: bool = False) -> None:
        """
        Méthode permettant de valider si les valeurs pour l'API sont valides.

        :param with_action: (bool) True pour avertir l'usager et ouvrir le fichier de configuration si une error
                                ValueError est attrapée, sinon False.
        """
        self._validate_wrapper(self.environment.API.validate, with_action)

    def validate_setting_be(self, with_action: bool = False) -> None:
        """
        Méthode permettant de valider si les valeurs de Caris Batch pour Base Editor sont valides.

        :param with_action: (bool) True pour avertir l'usager et ouvrir le fichier de configuration si une error
                                ValueError est attrapée, sinon False.
        """
        self._validate_wrapper(self.environment.BE.validate, with_action)

    def validate_setting_hips(self, with_action: bool = False) -> None:
        """
        Méthode permettant de valider si les valeurs de Caris Batch pour Hips and Sips sont valides.

        :param with_action: (bool) True pour avertir l'usager et ouvrir le fichier de configuration si une error
                                ValueError est attrapée, sinon False.
        """
        self._validate_wrapper(self.environment.HIPS.validate, with_action)

    def validate_settings(self, with_action: bool = False) -> None:
        """
        Méthode permettant de valider si les valeurs d'environnement sont valides.

        :param with_action: (bool) True pour avertir l'usager et ouvrir le fichier de configuration si une error
                                ValueError est attrapée, sinon False.
        """
        self._validate_wrapper(self.environment.validate, with_action)

    def validate_python_version(self, with_action: bool = False) -> None:
        """
        Méthode permettant de valider que la version de python utilisée correspond avec celle de l'API de Caris.

        :param with_action: (bool) True pour avertir l'usager et ouvrir le fichier de configuration si une error
                                ValueError est attrapée, sinon False.
        """
        self._validate_wrapper(self._validate_python_version, with_action)

    def _validate_python_version(self) -> None:
        """
        Méthode permettant de valider que la version de python utilisée correspond avec celle de l'API de Caris.

        :raise: VersionError si la version ne correspond pas.
        """
        sys_version = f'{str(sys.version_info.major)}.{str(sys.version_info.minor)}'
        if sys_version != self.environment.API.Python_version:
            raise VersionError("La version système de Python doit correspondre avec la version de l'API de Caris.")

    def _validate_wrapper(self, validation: Callable, with_action: bool) -> None:
        """
        Méthode permettant de sélection le validateur désiré et de l'exécuter.

        :param validation: (Callable) La fonction de validation à exécuter.
        :param with_action: (bool) True pour avertir l'usager et ouvrir le fichier de configuration si une error
                                ValueError est attrapée, sinon False.
        """
        validator = {
            True: partial(self._validate_with_action, validation=validation),
            False: validation
        }

        validator[with_action]()

    @staticmethod
    def _validate_with_action(validation: Callable) -> None:
        """
        Méthode permettant d'exécuter la fonction de validation et affichant un avertissement
        advenant un paramètre incorrect.

        :param validation: (Callable) La fonction de validation à exécuter.
        """
        try:
            validation()

        except (ValueError, VersionError) as error:
            action_setting(error)


def action_setting(error: Exception) -> None:
    """
    Méthode permettant d'afficher un avertissement et d'ouvrir le fichier de configuration.

    :param error: (Exception) L'erreur à afficher.
    """
    import tkinter as tk
    from tkinter import messagebox
    import sys

    root = tk.Tk()
    root.withdraw()
    messagebox.showinfo(
        "Avertissement",
        f"{error} Modifier les paramètres dans le fichier de configuration '{CONFIG_FILE_PATH}' "
        f"ou installer les dépendances nécessaires."
    )
    open_config_file(CONFIG_FILE_PATH)
    sys.exit(-1)


def open_config_file(file: str = CONFIG_FILE_PATH) -> None:
    """
    Méthode permettant d'ouvrir le fichier de configuration de l'usager.

    :param file: (str) Le chemin du fichier.
    """
    os.startfile(file)


def config_exist() -> bool:
    """
    Fonction permettant de vérifier si le fichier de configuration existe.

    :return: (bool) True si le fichier existe, False sinon.
    """
    return os.path.exists(CONFIG_FILE_PATH)


def create_config() -> None:
    """
    Fonction permettant de créer le fichier de configuration.
    """
    if not os.path.exists(CONFIG_PATH):
        os.mkdir(CONFIG_PATH)

    copyfile(SOURCE_FILE_PATH, CONFIG_FILE_PATH)


def load_user_config() -> Config:
    """
    Fonction permettant de charger le fichier de configuration.

    :return: (Config) Un objet Config contenant les informations de configuration.
    """
    return get_config_from_factories(CONFIG_FILE_PATH)


def load_source_config() -> Config:
    """
    Fonction permettant de charger le fichier de configuration source.

    :return: (Config) Un objet Config contenant les informations de configuration source.
    """
    return get_config_from_factories(SOURCE_FILE_PATH)


def get_global_config_manager() -> GlobalConfigManager:
    """
    Fonction permettant d'instancier un objet GlobalConfigManager.

    :return: (GlobalConfigManager) Un objet GlobalConfigManager.
    """
    return GlobalConfigManager(load_user_config(), load_source_config())


def init_global_settings(
        validate_setting_api: bool = False, validate_setting_be: bool = False,
        validate_setting_hips: bool = False, validate_setting_all: bool = False,
        validate_python_version: bool = False, validate_with_action: bool = False
) -> GlobalConfigManager:
    """
    Fonction permettant d'initialiser un gestionnaire de configuration. Ce dernier peut être créer
    ou mis à jour au besoin.

     :return: (GlobalConfigManager) Un objet GlobalConfigManager.
    """
    if not config_exist():
        create_config()

    config_manager = get_global_config_manager()

    validation = (
                     (
                         validate_setting_api,
                         partial(config_manager.validate_setting_api, with_action=validate_with_action)
                     ),
                     (
                         validate_setting_be,
                         partial(config_manager.validate_setting_be, with_action=validate_with_action)
                     ),
                     (
                         validate_setting_hips,
                         partial(config_manager.validate_setting_hips, with_action=validate_with_action)
                     ),
                     (
                         validate_setting_all,
                         partial(config_manager.validate_settings, with_action=validate_with_action)
                     ),
                     (
                         validate_python_version,
                         partial(config_manager.validate_python_version, with_action=validate_with_action)
                     )
    )

    for condition, validate in validation:
        if condition:
            validate()

    if config_manager.get_source_config_version() > config_manager.get_user_config_version():
        config_manager.update_user_config_from_source_config(CONFIG_FILE_PATH)

    return config_manager


if __name__ == "__main__":
    # from lib.config_adapter_utils.config_adapter import get_config_from_factories

    config = init_global_settings(validate_setting_all=True, validate_python_version=True, validate_with_action=True)

    print(config.environment)
