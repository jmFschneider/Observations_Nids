from django.contrib import admin
from django.utils.html import format_html

from .models import (
    CausesEchec,
    ConfigurationVerrouillage,
    EtatCorrection,
    FicheObservation,
    HistoriqueVerrouillage,
    ImageSource,
    Nid,
    Observation,
    Remarque,
    ResumeObservation,
)


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
    list_display = (
        "id",
        "image_thumbnail",
        "observateur",
        "est_transcrite",
        "date_televersement",
        "fiche_liee",
    )
    list_filter = ("est_transcrite", "date_televersement", "observateur")
    search_fields = (
        "observateur__username",
        "observateur__first_name",
        "observateur__last_name",
        "id",
    )
    readonly_fields = ("date_televersement", "image_preview")
    raw_id_fields = ("fiche_observation",)

    @admin.display(description="Aperçu")
    def image_thumbnail(self, obj):
        """Affiche une miniature de l'image dans la liste"""
        if obj.image:
            return format_html(
                '<img src="{}" width="50" height="50" style="object-fit: cover; border-radius: 4px;" />',
                obj.image.url,
            )
        return "Pas d'image"

    @admin.display(description="Prévisualisation de l'image")
    def image_preview(self, obj):
        """Affiche une prévisualisation plus grande dans le détail"""
        if obj.image:
            return format_html(
                '<img src="{}" style="max-width: 500px; max-height: 500px; border: 1px solid #ddd; border-radius: 4px;" />',
                obj.image.url,
            )
        return "Pas d'image"

    @admin.display(description="Fiche associée")
    def fiche_liee(self, obj):
        """Lien vers la fiche d'observation associée"""
        if obj.fiche_observation:
            return format_html(
                '<a href="/admin/observations/ficheobservation/{}/change/">Fiche #{}</a>',
                obj.fiche_observation.num_fiche,
                obj.fiche_observation.num_fiche,
            )
        return "Aucune fiche"


@admin.register(ConfigurationVerrouillage)
class ConfigurationVerrouillageAdmin(admin.ModelAdmin):
    """
    Administration de la configuration du verrouillage (Singleton).
    Seul un enregistrement peut exister.
    """

    list_display = ('duree_verrouillage_jours', 'date_modification')
    fieldsets = (
        (
            'Configuration du verrouillage',
            {
                'fields': ('duree_verrouillage_jours',),
                'description': 'Définit la durée après laquelle une fiche verrouillée sera automatiquement débloquée.',
            },
        ),
    )

    def has_add_permission(self, request):
        """Empêche la création de multiples instances (singleton)"""
        return not ConfigurationVerrouillage.objects.exists()

    def has_delete_permission(self, request, obj=None):
        """Empêche la suppression de la configuration"""
        return False


@admin.register(EtatCorrection)
class EtatCorrectionAdmin(admin.ModelAdmin):
    """Administration des états de correction des fiches"""

    list_display = (
        'fiche',
        'statut',
        'pourcentage_completion',
        'en_correction_par',
        'date_debut_correction',
        'date_derniere_modification',
    )
    list_filter = ('statut', 'en_correction_par')
    search_fields = ('fiche__num_fiche', 'en_correction_par__username')
    readonly_fields = ('date_derniere_modification', 'date_debut_correction')
    actions = ['liberer_verrous']

    @admin.action(description='Libérer les verrous des fiches sélectionnées')
    def liberer_verrous(self, request, queryset):
        """Action pour libérer les verrous de plusieurs fiches à la fois"""
        nb_liberes = 0
        for etat in queryset:
            if etat.est_verrouillee():
                etat.liberer_verrou()
                nb_liberes += 1

        if nb_liberes > 0:
            self.message_user(request, f"{nb_liberes} verrou(s) libéré(s) avec succès.")
        else:
            self.message_user(
                request, "Aucune fiche n'était verrouillée parmi la sélection.", level='WARNING'
            )


@admin.register(HistoriqueVerrouillage)
class HistoriqueVerrouillageAdmin(admin.ModelAdmin):
    list_display = (
        "fiche",
        "correcteur",
        "date_debut",
        "date_fin",
        "motif_liberation",
        "duree_affichage",
    )
    list_filter = ("motif_liberation", "date_debut", "date_fin")
    search_fields = (
        "fiche__num_fiche",
        "correcteur__first_name",
        "correcteur__last_name",
    )
    readonly_fields = ("date_debut", "date_fin", "duree_affichage")
    ordering = ("-date_debut",)

    @admin.display(description="Durée")
    def duree_affichage(self, obj):
        """Affiche la durée de correction de manière lisible"""
        if not obj.date_fin:
            return "En cours"
        duree = obj.date_fin - obj.date_debut
        jours = duree.days
        heures = duree.seconds // 3600
        minutes = (duree.seconds % 3600) // 60
        return f"{jours}j {heures}h {minutes}min"

admin.site.register(Nid)
admin.site.register(ResumeObservation)
admin.site.register(CausesEchec)
