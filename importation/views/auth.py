# importation/views/auth.py
import logging

logger = logging.getLogger(__name__)


def est_admin(user):
    """Vérifie si l'utilisateur est un administrateur"""
    return user.is_authenticated and user.role == 'administrateur'
