from abc import ABC, abstractmethod
from enum import Enum
from importlib import util, import_module
import os
import sys
from typing import Any

from . exceptions_config import VersionError
from . import ids_environment_config as ids
from . schema_importer import CarisAPIConfig


Module = Any


def import_lib_from_file(module_name: str, module_path: str) -> Module:
    """
    Méthode permettant d'importer un module à partir d'un fichier et de ses spécifications.

    :param module_name: (str) Le nom du module
    :param module_path: (str) Le chemin du module.
    :return: (Module) Un module chargé à partir d'un fichier.
    """
    try:
        spec = util.spec_from_file_location(module_name, module_path)
        module = util.module_from_spec(spec)
        spec.loader.exec_module(module)

        return import_module(module_name)

    except ImportError:
        raise sys.exit(f"Erreur à l'importation du module '{module_name}'.")


class CarisModule(Enum):
    CARIS: Module = 'caris'
    BATHY_DB: Module = 'caris.bathy.db'
    COVERAGE: Module = 'caris.coverage'


class CarisModuleImporterAbstract(ABC):
    @property
    @abstractmethod
    def configuration(self) -> CarisAPIConfig:
        ...

    @property
    @abstractmethod
    def caris(self) -> CarisModule:
        ...

    @property
    @abstractmethod
    def bathy_db(self) -> CarisModule:
        ...

    @property
    @abstractmethod
    def coverage(self) -> CarisModule:
        ...


class CarisModuleImporter(CarisModuleImporterAbstract):
    """
    Classe permettant d'importer les modules de lAPI de Caris.
    """
    def __init__(self, p_config: CarisAPIConfig) -> None:
        """
        Construteur de la classe.

        :param p_config: (CarisAPIConfig) Un objet CarisAPIConfig.
        """
        self._configuration = p_config
        self.validate_python_version()

        self._python_env = p_config.Python_path

        self._caris = self._import_caris()
        self._bathy_db = self._import_bathy_db()
        self._coverage = self._import_coverage()

    def validate_python_version(self) -> None:
        """
        Méthode permettant de valider que la version de python utilisée correspond avec celle de l'API de Caris.

        :raise: VersionError si la version ne correspond pas.
        """
        sys_version = f'{str(sys.version_info.major)}.{str(sys.version_info.minor)}'
        if sys_version != self._configuration.Python_version:
            raise VersionError("La version système de Python doit correspondre avec la version de l'API de Caris.")

    def _add_environment(self) -> None:
        """
        Méthode permettant d'ajouter self._python_env des chemins du système.
        """
        sys.path.insert(0, self._python_env)

    def _delete_environment(self) -> None:
        """
        Méthode permettant d'enlever self._python_env des chemins du système.
        """
        sys.path.remove(self._python_env)

    def _import_module_wrapper(self, p_module: CarisModule, p_module_path: str) -> Module:
        """
        Méthode permettant d'importer un module.

        :param p_module: (CarisModule) Un objet CarisModule.
        :param p_module_path: (str) Le chemin du fichier du module.
        :return: (CarisModule) Retourne le module importé.
        """
        self._add_environment()
        module = import_lib_from_file(p_module.value, p_module_path)
        self._delete_environment()

        return module

    def _import_caris(self) -> Module:
        """
        Méthode permettant d'importer le module caris.

        :return: (Module) Retourne le module caris.
        """
        return self._import_module_wrapper(
            CarisModule.CARIS,
            os.path.join(self._python_env, ids.CARIS, ids.INIT)
        )

    def _import_bathy_db(self) -> Module:
        """
        Méthode permettant d'importer le module caris.bathy.db.

        :return: (Module) Retourne le module caris.bathy.db.
        """
        return self._import_module_wrapper(
            CarisModule.BATHY_DB,
            os.path.join(self._python_env, ids.CARIS, ids.BATHY, ids.DB, ids.INIT)
        )

    def _import_coverage(self) -> Module:
        """
        Méthode permettant d'importer le module caris.coverage.

        :return: (Module) Retourne le module caris.coverage.
        """
        return self._import_module_wrapper(
            CarisModule.COVERAGE,
            os.path.join(self._python_env, ids.CARIS, ids.COVERAGE, ids.INIT)
        )

    @property
    def configuration(self) -> CarisAPIConfig:
        return self._configuration

    @property
    def caris(self) -> Module:
        return self._caris

    @property
    def bathy_db(self) -> Module:
        return self._bathy_db

    @property
    def coverage(self) -> Module:
        return self._coverage
