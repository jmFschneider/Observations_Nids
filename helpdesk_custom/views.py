from helpdesk.views.staff import CreateTicketView

from .forms import CustomTicketForm


class CustomCreateTicketView(CreateTicketView):
    form_class = CustomTicketForm
