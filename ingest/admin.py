from django.contrib import admin

from .models import EspeceCandidate, ImportationEnCours, PreparationImage, TranscriptionBrute


@admin.register(PreparationImage)
class PreparationImageAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'date_preparation',
        'operateur',
        'fichier_brut_recto',
        'fichier_brut_verso',
    ]
    list_filter = ['date_preparation', 'operateur']
    search_fields = ['fichier_brut_recto', 'fichier_brut_verso', 'notes']
    readonly_fields = ['date_preparation']
    date_hierarchy = 'date_preparation'

    fieldsets = (
        ('Fichiers sources', {'fields': ('fichier_brut_recto', 'fichier_brut_verso')}),
        ('Fichier résultat', {'fields': ('fichier_fusionne',)}),
        ('Métadonnées de traitement', {'fields': ('operations_effectuees', 'notes')}),
        ('Traçabilité', {'fields': ('operateur', 'date_preparation')}),
    )


admin.site.register(TranscriptionBrute)
admin.site.register(EspeceCandidate)
admin.site.register(ImportationEnCours)
