from django.apps import AppConfig


class HelpdeskCustomConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'helpdesk_custom'
    verbose_name = 'Helpdesk Personnalisé'

    def ready(self):
        """
        Configuration au démarrage de l'application.
        Le monkey-patching de CreateTicketView a été remplacé par une surcharge d'URL
        dans observations_nids/urls.py pour plus de stabilité.
        """
        pass
