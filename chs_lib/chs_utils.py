import datetime
import time


def replace_string(data_string, replaced: tuple):
    """
    Méthode permettant de modifier une chaine de caractères.

    :param data_string: (str) Une chaîne de caractères.
    :param replaced: (tuple) un tuple comprenant des tuples de chaines de caractères à remplacer
                     et les nouveaux caractères.
    :return: (str) Une string avec les chaines de caractères modifiés.
    """
    for r in replaced:
        data_string = data_string.replace(*r)
    return data_string


def get_jd_utc() -> int:
    """
    Fonction qui retourne le jour julien UTC.

    :return: (int) Retourne le jour julien UTC.
    """
    return datetime.datetime.utcnow().timetuple().tm_yday


def get_jd_format_utc() -> str:
    """
    Fonction qui retourne le jour julien formaté UTC (000).

    :return: (str) Retourne le jour julien formaté UTC (000).
       """
    jd = get_jd_utc()
    if jd < 10:
        jd_format = "00{}".format(jd)
    elif jd < 100:
        jd_format = "0{}".format(jd)
    else:
        jd_format = jd

    return jd_format


def get_year_utc() -> str:
    """
    Fonction qui retourne l'année UTC.

    return: (str) Retourne l'année UTC.
    """
    return str(datetime.datetime.utcnow())[0:4]


def get_date_utc() -> str:
    """
    Fonction qui retourne la date UTC (yyyy-mm-dd).

    :return: (str) La date locale.
    """
    return str(datetime.datetime.utcnow()).split()[0]


def get_time_utc(p_ob: str = 'str'):
    """
    Fonction qui retourne l'heure UTC (hh:mm:ss).

    :param p_ob: (str) 'str' pour le temps en chaine de caractère, 'datetime' pour un objet datetime.
    :return: (str|datettime) L'heure en utc.
    """
    if p_ob == 'str':
        return str(datetime.datetime.utcnow()).split()[1][:8]
    elif p_ob == 'datetime':
        return datetime.datetime.utcnow()


def get_date_local() -> str:
    """
    Fonction qui retourne la date locale (yyyy-mm-dd).

    :return: (str) La date locale.
    """
    date = time.localtime(time.time())
    return "{}-{}-{}".format(date.tm_year, '0' + str(date.tm_mon) if date.tm_mon < 10 else date.tm_mon,
                             '0' + str(date.tm_mday) if date.tm_mday < 10 else date.tm_mday)


def get_time_local() -> str:
    """
    Fonction qui retourne l'heure locale (hh:mm:ss).
    :return: (str) L'heure locale.
    """
    date = time.localtime(time.time())
    return "{}:{}:{}".format('0' + str(date.tm_hour) if date.tm_hour < 10 else date.tm_hour,
                             '0' + str(date.tm_min) if date.tm_min < 10 else date.tm_min,
                             '0' + str(date.tm_sec) if date.tm_sec < 10 else date.tm_sec)


def jd_formate(jd: int) -> str:
    """
    Fonction qui formate le jour julien afin d'avoir 3 charactères.

    :param jd: (int): le jour julien.
    :return: (str): Le jour julien formaté.
    """
    if jd < 10:
        jd_format = "00{}".format(jd)
    elif jd < 100:
        jd_format = "0{}".format(jd)
    else:
        jd_format = jd

    return jd_format


def convert_jd_2_date(p_year: int, p_day: int) -> datetime:
    """
    Fonction qui convertie l'année et le jour de l'année en date

    :param p_year: (int)
    :param p_day: (int)

    :return: La date convertie.
    """
    return datetime.datetime(p_year, 1, 1) + datetime.timedelta(p_day - 1)


def listed(p_input: list, p_join: str = 'et') -> str:
    """
    Fonction qui formate une liste d'éléments pour afficher correctement une énumération.

    :param p_input: (list) Une liste de chaîne de caractères.
    :param p_join: (str) Le mot utilisé comme coordonnant.
    :return: (str) Une chaîne de caractère avec un format adéquat pour une énumération.
    """
    if len(p_input) == 0:
        string = ''
    elif len(p_input) == 1:
        string = p_input[0]
    elif len(p_input) == 2:
        string = p_input[0] + ' {} '.format(p_join) + p_input[1]
    else:
        string = ', '.join(p_input[:-1]) + ', {} '.format(p_join) + p_input[-1]

    return string
