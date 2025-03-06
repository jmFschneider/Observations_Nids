from django.contrib import admin
from .models import (
    Utilisateur, Espece, FicheObservation, Localisation, Nid,
    Observation, ResumeObservation, CausesEchec, Validation,
    HistoriqueModification, HistoriqueValidation
)

@admin.register(Utilisateur)
class UtilisateurAdmin(admin.ModelAdmin):
    list_display = ("prenom", "nom", "email", "role", "est_valide")
    list_filter = ("role", "est_valide")
    search_fields = ("prenom", "nom", "email")

@admin.register(Espece)
class EspeceAdmin(admin.ModelAdmin):
    list_display = ("nom", "valide_par_admin")
    list_filter = ("valide_par_admin",)
    search_fields = ("nom",)

@admin.register(FicheObservation)
class FicheObservationAdmin(admin.ModelAdmin):
    list_display = ("num_fiche", "observateur", "espece", "annee")
    list_filter = ("annee", "espece")
    search_fields = ("num_fiche", "observateur__nom", "espece__nom")

@admin.register(Observation)
class ObservationAdmin(admin.ModelAdmin):
    list_display = ("fiche", "date_observation", "nombre_oeufs", "nombre_poussins")
    list_filter = ("date_observation",)
    search_fields = ("fiche__num_fiche",)

@admin.register(Validation)
class ValidationAdmin(admin.ModelAdmin):
    list_display = ("observation", "reviewer", "date_validation")
    list_filter = ("date_validation",)

@admin.register(HistoriqueValidation)
class HistoriqueValidationAdmin(admin.ModelAdmin):
    list_display = ('validation', 'ancien_statut', 'nouveau_statut', 'date_modification', 'modifie_par')
    list_filter = ('nouveau_statut', 'date_modification')
    ordering = ('-date_modification',)

@admin.register(HistoriqueModification)
class HistoriqueModificationAdmin(admin.ModelAdmin):
    list_display = ("observation", "champ_modifie", "date_modification")
    search_fields = ("observation__fiche__num_fiche", "champ_modifie")

# Enregistrement simple des autres modèles
admin.site.register(Localisation)
admin.site.register(Nid)
admin.site.register(ResumeObservation)
admin.site.register(CausesEchec)
