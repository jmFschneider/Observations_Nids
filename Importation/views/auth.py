# Importation/views/auth.py
import logging

from django.contrib.auth.decorators import login_required, user_passes_test

logger = logging.getLogger(__name__)


def est_admin(user):
    """Vérifie si l'utilisateur est un administrateur"""
    return user.is_authenticated and user.role == 'administrateur'