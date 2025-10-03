from django.contrib import admin

from .models import CausesEchec, FicheObservation, Nid, Observation, Remarque, ResumeObservation


@admin.register(FicheObservation)
class FicheObservationAdmin(admin.ModelAdmin):
    list_display = ("num_fiche", "observateur", "espece", "annee")
    list_filter = ("annee", "espece")
    search_fields = (
        "num_fiche",
        "observateur__first_name",
        "observateur__last_name",
        "espece__nom",
    )


@admin.register(Observation)
class ObservationAdmin(admin.ModelAdmin):
    list_display = ("fiche", "date_observation", "nombre_oeufs", "nombre_poussins")
    list_filter = ("date_observation",)
    search_fields = ("fiche__num_fiche",)


@admin.register(Remarque)
class RemarqueAdmin(admin.ModelAdmin):
    list_display = ("fiche", "date_remarque", "remarque")
    list_filter = ("date_remarque",)
    search_fields = ("fiche__num_fiche", "remarque")


admin.site.register(Nid)
admin.site.register(ResumeObservation)
admin.site.register(CausesEchec)
