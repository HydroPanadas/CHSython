from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class URI:
    username: str
    password: str
    host_name: str
    bathy_database_name: str
    feature_id: str
    uri: str = field(init=False)

    def __post_init__(self):
        object.__setattr__(
            self,
            'uri',
            f'bdb://{self.username}:{self.password}@{self.host_name}/{self.bathy_database_name}/{self.feature_id}'
        )

    def __str__(self) -> str:
        return self.uri


def is_uri(p_uri: Any) -> bool:
    """
    Fonction permettant de déterminer s'il s'agit d'un objet URI représentant
    'bdb://username:password@hostmane/bathydatabasename/featureId'.

    :param p_uri: (Any) Un objet.
    :return: (bool) True si l'objet est une instance de la classe URI, False sinon.
    """
    return isinstance(p_uri, URI)
