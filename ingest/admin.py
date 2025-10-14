from django.contrib import admin

from .models import EspeceCandidate, ImportationEnCours, TranscriptionBrute

admin.site.register(TranscriptionBrute)
admin.site.register(EspeceCandidate)
admin.site.register(ImportationEnCours)
