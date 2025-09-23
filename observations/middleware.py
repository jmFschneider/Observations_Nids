from django.conf import settings
from django.contrib import messages


class SessionExpiryMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if (
            request.path == settings.LOGIN_URL
            and 'next' in request.GET
            and request.session.get('_auth_user_id')
        ):
            messages.warning(request, "Votre session a expiré, veuillez vous reconnecter.")
        return self.get_response(request)
