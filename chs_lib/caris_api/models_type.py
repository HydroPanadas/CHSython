from enum import Enum


class AttributeType(Enum):
    ITEMS = 'items'
    VALUES = 'values'
    KEYS = 'keys'
    XML = 'xml'

    def __str__(self) -> str:
        return self.value


class FeatureType(Enum):
    SURFAC = 'surfac'
    SURVEY = 'survey'

    def __str__(self) -> str:
        return self.value


class CRSType(Enum):
    EPSG = 'epsg'
    WKT = 'wkt'

    def __str__(self) -> str:
        return self.value
