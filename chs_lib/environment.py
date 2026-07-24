import configparser
import os
import sys


def get_global_environment() -> configparser.ConfigParser:
    # Initialisation du répertoire de l'exécutable.
    _APPLICATION_PATH = None
    if getattr(sys, 'frozen', False):
        _APPLICATION_PATH = os.path.dirname(sys.executable)
    elif __file__:
        _APPLICATION_PATH = os.path.dirname(__file__)

    # param_ini = os.path.join(_APPLICATION_PATH, '..', 'global.ini')
    param_ini = os.path.join(os.path.dirname(_APPLICATION_PATH), 'global.ini')

    if not os.path.exists(param_ini):
        raise FileNotFoundError(
            f"Le fichier 'global.ini' n'est pas présent dans "
            f"le répertoire f'{os.path.dirname(param_ini)}'.".replace('/', '\\')
        )

    config = configparser.ConfigParser()
    config.read(param_ini, encoding="UTF-8")

    return config


if __name__ == "__main__":
    env = get_global_environment()
    for k, v in env.items():
        print(k, v)

    print(env['DEFAULT BASE Editor']['Python'])
