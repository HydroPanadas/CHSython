class SchemaError(Exception):
    ...


class SchemaInfoSchemaError(SchemaError):
    ...


class ConfigAPISchemaError(SchemaError):
    ...


class ConfigCarisBatchSchemaError(SchemaError):
    ...


class ConfigGUISchemaError(SchemaError):
    ...


class ConfigEnvironmentSchemaError(SchemaError):
    ...


class VersionError(Exception):
    ...
