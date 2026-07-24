class BaseEditorError(Exception):
    """
    Classe de base pour les erreurs avec BE.
    """
    pass


class BandError(BaseEditorError):
    """
    Erreur levée lorsqu'il la couche est inexistante.
    """
    pass
