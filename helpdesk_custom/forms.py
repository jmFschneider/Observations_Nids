from django.utils.translation import gettext_lazy as _
from helpdesk.forms import PublicTicketForm, TicketForm


class CustomPublicTicketForm(PublicTicketForm):
    """Formulaire personnalisé pour la création de tickets publics"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Changer le label du champ queue en "Catégorie"
        if 'queue' in self.fields:
            self.fields['queue'].label = _('Catégorie')


class CustomTicketForm(TicketForm):
    """Formulaire personnalisé pour la création de tickets (utilisateurs connectés)"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Changer le label du champ queue en "Catégorie"
        if 'queue' in self.fields:
            self.fields['queue'].label = _('Catégorie')
