# Administration/apps.py
from django.apps import AppConfig


class AdministrationConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'Administration'
    verbose_name = "Administration des utilisateurs"