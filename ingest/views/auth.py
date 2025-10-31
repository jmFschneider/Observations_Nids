# importation/views/auth.py
import logging

logger = logging.getLogger(__name__)


def est_admin(user):
    """Vérifie si l'utilisateur est un administrateur"""
    return user.is_authenticated and user.role == 'administrateur'


def peut_transcrire(user):
    """
    Vérifie si l'utilisateur peut transcrire et importer des transcriptions.

    Autorisé si :
    - L'utilisateur a le champ est_transcription = True OU
    - L'utilisateur est administrateur
    """
    return user.is_authenticated and (user.est_transcription or user.role == 'administrateur')
