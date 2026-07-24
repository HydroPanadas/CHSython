from dataclasses import dataclass, field
import os
from typing import Union

from . exceptions_config import SchemaInfoSchemaError
from . import ids_environment_config as ids


@dataclass(frozen=True)
class CarisAPIConfig:
    Base_path: str
    Software: str
    Version: str
    Python_version: str
    Python_path: str = field(init=False)

    def __post_init__(self):
        object.__setattr__(
            self,
            ids.PYTHON_PATH,
            os.path.join(
                self.Base_path,
                self.Software,
                self.Version,
                ids.PYTHON,
                self.Python_version
            )
        )  # todo valider post_init ?

    def validate(self) -> None:
        if not os.path.exists(self.Python_path):
            raise ValueError(f"Le répertoire '{self.Python_path}' n'existe pas.")


@dataclass(frozen=True)
class CarisBatchConfig:
    Base_path: str
    Software: str
    Version: str
    Caris_batch: str = field(init=False)

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            ids.CARIS_BATCH,
            os.path.join(
                self.Base_path,
                self.Software,
                self.Version,
                ids.BIN,
                ids.CARIS_BATCH_EXE
            )
        )  # todo valider post_init ?

    def validate(self) -> None:
        if not os.path.exists(self.Caris_batch):
            raise ValueError(f"Le fichier '{self.Caris_batch}' n'existe pas.")


@dataclass(frozen=True)
class SchemaInfo:
    Version: Union[str, int]

    def __post_init__(self) -> None:
        try:
            if isinstance(self.Version, str):
                object.__setattr__(
                    self,
                    ids.VERSION,
                    int(self.Version)
                )

        except ValueError as error:
            raise SchemaInfoSchemaError(
                "Le schéma suivant doit être respecté : {Version' : str|int}."
            )


@dataclass(frozen=True)
class GUIConfig:
    Theme: str
    Style: str


@dataclass(frozen=True)
class EnvironmentConfig:
    SCHEMA: SchemaInfo
    API: CarisAPIConfig
    BE: CarisBatchConfig
    HIPS: CarisBatchConfig
    GUI: GUIConfig

    def validate(self) -> None:
        self.API.validate()
        self.BE.validate()
        self.HIPS.validate()
