from chs_lib.environment_config_manager.global_config_manager import init_global_settings

config_manager = init_global_settings(
    validate_setting_api=True,
    validate_python_version=True,
    validate_with_action=True
)
caris_module = config_manager.get_caris_module()
bathy_db = caris_module.bathy_db
caris = caris_module.caris
cov = caris_module.coverage
