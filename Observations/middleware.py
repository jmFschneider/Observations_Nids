from django.contrib import messages
from django.shortcuts import redirect
from django.conf import settings

class SessionExpiryMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path == settings.LOGIN_URL and 'next' in request.GET:
            messages.warning(request, "Votre session a expiré, veuillez vous reconnecter.")
        return self.get_response(request)
