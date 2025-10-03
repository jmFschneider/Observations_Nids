
from django.contrib import admin

from .models import HistoriqueValidation, Validation

admin.site.register(Validation)
admin.site.register(HistoriqueValidation)
