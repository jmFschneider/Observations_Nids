# observations/admin.py
from django.contrib import admin

from .models import (
    CausesEchec,
    Espece,
    FicheObservation,
    HistoriqueModification,
    HistoriqueValidation,
    Localisation,
    Nid,
    Observation,
    Remarque,
    ResumeObservation,
    Validation,
)


@admin.register(Espece)
class EspeceAdmin(admin.ModelAdmin):
    list_display = ("nom", "valide_par_admin")
    list_filter = ("valide_par_admin",)
    search_fields = ("nom",)


@admin.register(FicheObservation)
class FicheObservationAdmin(admin.ModelAdmin):
    list_display = ("num_fiche", "observateur", "espece", "annee")
    list_filter = ("annee", "espece")
    search_fields = (
        "num_fiche",
        "observateur__first_name",
        "observateur__last_name",
        "espece__nom",
    )  # Correction ici


@admin.register(Observation)
class ObservationAdmin(admin.ModelAdmin):
    list_display = ("fiche", "date_observation", "nombre_oeufs", "nombre_poussins")
    list_filter = ("date_observation",)
    search_fields = ("fiche__num_fiche",)


@admin.register(Validation)
class ValidationAdmin(admin.ModelAdmin):
    list_display = ("fiche", "reviewer", "date_modification", "statut")
    list_filter = ("statut", "date_modification")
    search_fields = (
        "fiche__num_fiche",
        "reviewer__first_name",
        "reviewer__last_name",
    )  # Correction ici
    ordering = ("-date_modification",)


@admin.register(HistoriqueValidation)
class HistoriqueValidationAdmin(admin.ModelAdmin):
    list_display = (
        'validation',
        'ancien_statut',
        'nouveau_statut',
        'date_modification',
        'modifie_par',
    )
    list_filter = ('nouveau_statut', 'date_modification')
    ordering = ('-date_modification',)


@admin.register(HistoriqueModification)
class HistoriqueModificationAdmin(admin.ModelAdmin):
    list_display = ("fiche", "champ_modifie", "categorie", "date_modification")
    search_fields = ("fiche__num_fiche", "champ_modifie")
    list_filter = ("categorie", "date_modification")
    ordering = ('-date_modification',)


@admin.register(Remarque)
class RemarqueAdmin(admin.ModelAdmin):
    list_display = ("fiche", "date_remarque", "remarque")
    list_filter = ("date_remarque",)
    search_fields = ("fiche__num_fiche", "remarque")


# Enregistrement des autres modèles
admin.site.register(Localisation)
admin.site.register(Nid)
admin.site.register(ResumeObservation)
admin.site.register(CausesEchec)
