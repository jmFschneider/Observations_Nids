from django.apps import AppConfig


class HelpdeskCustomConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'helpdesk_custom'
    verbose_name = 'Helpdesk Personnalisé'

    def ready(self):
        """
        Surcharger la form_class de CreateTicketView au démarrage
        pour utiliser notre formulaire personnalisé
        """
        # Import local pour éviter les imports circulaires au démarrage de Django
        from helpdesk.views import staff  # noqa: PLC0415

        from .forms import CustomTicketForm  # noqa: PLC0415

        # Remplacer la form_class de CreateTicketView
        staff.CreateTicketView.form_class = CustomTicketForm
