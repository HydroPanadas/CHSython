from abc import ABC, abstractmethod
import collections.abc
from configparser import ConfigParser
from copy import deepcopy
import json
import os
from typing import Dict, Any, Union, Type
import yaml

from . ids import (
    INI, JSON, YAML
)

ConfigDict = Dict[str, Any]


class Config(ABC):
    def __init__(self, config: Union[str, dict]):
        """
       Constructeur de la classe Config.

       :param config: (Union[str, dict]) Le chemin du fichier de configuration ou un
                           dictionnaire de configuration.
       """
        self.config: dict

        if isinstance(config, dict):
            self.config = config
        elif isinstance(config, str):
            self.load_config_from_file(config)

    @abstractmethod
    def load_config_from_file(self, file: str) -> None:
        """
        Méthode permettant de charger la configuration à partir d'un fichier.

        :param file: (str) Le chemin du fichier de configuration.
        :raise: ConfigFileNotFoundError si le fichier de configuration est inexistant.
        """
        ...

    @abstractmethod
    def write_config_to_file(self, out_config_file: str) -> None:
        """
       Méthode permettant d'écrire la configuration dans un fichier.

       :param out_config_file: (str) Le fichier à écrire.
       """
        ...

    def update_config(self, new_config_dict: ConfigDict) -> None:
        """
        Méthode permettant de mettre à jour la configuration à partir d'un dictionnaire. Les nouvelles clés sont
        ajoutées et les anciennes valeurs pour les clés existantes sont conservées.

        :param new_config_dict: (ConfigDict) La nouvelle configuration sous forme de dictionnaire.
        """
        def update(old_dict, new_dict):
            for key, value in new_dict.items():
                if isinstance(value, collections.abc.Mapping):
                    old_dict[key] = update(old_dict.get(key, {}), value)
                else:
                    old_dict[key] = value

            return old_dict

        config = deepcopy(new_config_dict)
        update(config, self.config)
        self.config = config

    def export_to(self, out_config_file: str) -> None:
        """
        Méthode permettant d'exporter une configration dans un format supporté.

        :param out_config_file: (str) Le fichier à écrire.
        """
        get_adapter_from_factories(out_config_file)(self.config).write_config_to_file(out_config_file)

    @property
    def configuration(self) -> ConfigDict:
        """
        Méthode permettant de récupérer la configuration sous forme de dictionnaire.

        :return: (dict) Le dictionnaire contenant la configuration.
        """
        return self.config


class INIAdapter(Config):
    """
    Classe permettant de récupérer une configuration à partir d'un fichier *.ini.
    """
    def __init__(self, config: Union[str, dict]):
        """
        Constructeur de la classe Config.

        :param config: (Union[str, dict]) Le chemin du fichier de configuration *.ini ou un
                           dictionnaire de configuration.
        """
        super().__init__(config)

    def load_config_from_file(self, ini_file: str) -> None:
        """
        Méthode permettant de charger la configuration à partir d'un fichier.

        :param ini_file: (str) Le chemin du fichier de configuration.
        :raise: ConfigFileNotFoundError si le fichier de configuration est inexistant.
        """
        if not os.path.exists(ini_file):
            raise ConfigFileNotFoundError(f"Le fichier '{ini_file}' n'existe pas.")

        parser = ConfigParser()
        parser.optionxform = str
        parser.read(ini_file)
        self.config = {section: dict(parser.items(section)) for section in parser.sections()}

    def write_config_to_file(self, out_config_file: str) -> None:
        """
       Méthode permettant d'écrire la configuration dans un fichier.

       :param out_config_file: (str) Le fichier à écrire.
       """
        parser = ConfigParser()
        parser.optionxform = str
        parser.read_dict(self.config)

        with open(out_config_file, 'w') as file:
            parser.write(file)


class JSONAdapter(Config):
    """
    Classe permettant de récupérer une configuration à partir d'un fichier *.json.
    """
    def __init__(self, config: Union[str, dict]):
        """
        Constructeur de la classe Config.

        :param config: (Union[str, dict]) Le chemin du fichier de configuration *.json ou un
                           dictionnaire de configuration.
        """
        super().__init__(config)

    def load_config_from_file(self, json_file: str) -> None:
        """
        Méthode permettant de charger la configuration à partir d'un fichier.

        :param json_file: (str) Le chemin du fichier de configuration.
        :raise: ConfigFileNotFoundError si le fichier de configuration est inexistant.
        """
        if not os.path.exists(json_file):
            raise ConfigFileNotFoundError(f"Le fichier '{json_file}' n'existe pas.")

        with open(json_file, 'r') as file:
            self.config = json.load(file)

    def write_config_to_file(self, out_config_file: str) -> None:
        """
       Méthode permettant d'écrire la configuration dans un fichier.

       :param out_config_file: (str) Le fichier à écrire.
       """
        with open(out_config_file, 'w') as file:
            json.dump(self.config, file, indent=4)


class YAMLAdapter(Config):
    """
    Classe permettant de récupérer une configuration à partir d'un fichier *.yaml.
    """
    def __init__(self, config: Union[str, dict]):
        """
        Constructeur de la classe Config.

        :param config: (Union[str, dict]) Le chemin du fichier de configuration *.yaml ou un
                           dictionnaire de configuration.
        """
        super().__init__(config)

    def load_config_from_file(self, yaml_file: str) -> None:
        """
        Méthode permettant de charger la configuration à partir d'un fichier.

        :param yaml_file: (str) Le chemin du fichier de configuration.
        :raise: ConfigFileNotFoundError si le fichier de configuration est inexistant.
        """
        if not os.path.exists(yaml_file):
            raise ConfigFileNotFoundError(f"Le fichier '{yaml_file}' n'existe pas.")

        with open(yaml_file, 'r') as file:
            self.config = yaml.safe_load(file)

    def write_config_to_file(self, out_config_file: str) -> None:
        """
       Méthode permettant d'écrire la configuration dans un fichier.

       :param out_config_file: (str) Le fichier à écrire.
       """
        with open(out_config_file, 'w') as config_file:
            yaml.dump(self.configuration, config_file, sort_keys=False, indent=4)


class ConfigFileNotFoundError(Exception):
    ...


FACTORIES_ADAPTER = {
    INI: INIAdapter,
    JSON: JSONAdapter,
    YAML: YAMLAdapter
}

# todo ajouter toml


def get_config_from_factories(config_file: str) -> Config:
    """
    Méthode permettant de récupérer un objet adapter convenant au format de fichier de configuration.

    :param config_file: (str) Le chemin du fichier de configuration.
    :return: (Config) Un objet Config.
    """
    return get_adapter_from_factories(config_file)(config_file)


def get_adapter_from_factories(config_file: str) -> Type[Config]:
    """
    Méthode permettant de récupérer l'adapter convenant au format de fichier de configuration.

    :param config_file: (str) Le chemin du fichier de configuration.
    :return: (Config) Une classe Config.
    :raise: NotImplementedError si le format de fichier de configuration n'est pas supporté.
    """
    file_type = os.path.splitext(config_file)[-1]

    if file_type not in FACTORIES_ADAPTER.keys():
        raise NotImplementedError(
            f"Les fichiers de configuration au format '*{file_type}' ne sont pas supportés."
        )

    return FACTORIES_ADAPTER[file_type]
