from django.contrib import admin
from django.utils.html import format_html

<<<<<<< HEAD
from .models import (
    CausesEchec,
    FicheObservation,
    ImageSource,
    Nid,
    Observation,
    Remarque,
    ResumeObservation,
)
=======
from .models import CausesEchec, FicheObservation, ImageSource, Nid, Observation, Remarque, ResumeObservation
>>>>>>> 6644a86754379bab052412bd23b4e43ee718b299


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


@admin.register(ImageSource)
class ImageSourceAdmin(admin.ModelAdmin):
    list_display = ("id", "image_thumbnail", "observateur", "est_transcrite", "date_televersement", "fiche_liee")
    list_filter = ("est_transcrite", "date_televersement", "observateur")
    search_fields = ("observateur__username", "observateur__first_name", "observateur__last_name", "id")
    readonly_fields = ("date_televersement", "image_preview")
    raw_id_fields = ("fiche_observation",)

    def image_thumbnail(self, obj):
        """Affiche une miniature de l'image dans la liste"""
        if obj.image:
            return format_html(
                '<img src="{}" width="50" height="50" style="object-fit: cover; border-radius: 4px;" />',
                obj.image.url
            )
        return "Pas d'image"
    image_thumbnail.short_description = "Aperçu"

    def image_preview(self, obj):
        """Affiche une prévisualisation plus grande dans le détail"""
        if obj.image:
            return format_html(
                '<img src="{}" style="max-width: 500px; max-height: 500px; border: 1px solid #ddd; border-radius: 4px;" />',
                obj.image.url
            )
        return "Pas d'image"
    image_preview.short_description = "Prévisualisation de l'image"

    def fiche_liee(self, obj):
        """Lien vers la fiche d'observation associée"""
        if obj.fiche_observation:
            return format_html(
                '<a href="/admin/observations/ficheobservation/{}/change/">Fiche #{}</a>',
                obj.fiche_observation.num_fiche,
                obj.fiche_observation.num_fiche
            )
        return "Aucune fiche"
    fiche_liee.short_description = "Fiche associée"


admin.site.register(Nid)
admin.site.register(ResumeObservation)
admin.site.register(CausesEchec)
