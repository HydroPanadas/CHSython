import logging
from typing import Optional

from . base_editor_utils import BaseEditorUtils
from . batch.batch_processor import CarisBatchProcess, CarisBatchProcessRT

from chs_lib.environment_config_manager.global_config_manager import init_global_settings

config_manager = init_global_settings(
    validate_setting_be=True,
    validate_with_action=True
)


def get_base_editor_facade() -> BaseEditorUtils:
    """
    Méthode permettant d'instancier un objet BaseEditorUtils.

    :return: Un objet BaseEditorUtils instancié.
    """
    return BaseEditorUtils(get_batch_utility())


def get_base_editor_facade_rt(logger: Optional[logging.Logger] = None) -> BaseEditorUtils:
    """
    Méthode permettant d'instancier un objet BaseEditorUtils.

    :param logger: (logging.Logger) Un logger.
    :return: Un objet BaseEditorUtils instancié.
    """
    return BaseEditorUtils(get_batch_utility_rt(logger=logger))


def get_batch_utility() -> CarisBatchProcess:
    """
    Méthode permettant d'instancier un objet CarisBatchProcess pour BE.

    :return: Un objet CarisBatchProcess instancié.
    """
    return CarisBatchProcess(config_manager.get_caris_batch_be())


def get_batch_utility_rt(logger: Optional[logging.Logger] = None) -> CarisBatchProcessRT:
    """
    Méthode permettant d'instancier un objet CarisBatchProcess pour BE.
    :param logger: (logging.Logger) Un logger.

    :return: Un objet CarisBatchProcessRT instancié.
    """
    return CarisBatchProcessRT(config_manager.get_caris_batch_be(), logger=logger)
