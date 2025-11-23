from django.db import models

from accounts.models import Utilisateur
from core.constants import STATUT_IMPORTATION_CHOICES
from taxonomy.models import Espece


class PreparationImage(models.Model):
    """
    Stocke l'historique de préparation des images avant OCR.
    Permet de tracer les opérations effectuées sur les scans bruts
    (fusion recto/verso, rotation, prétraitements, etc.).
    """

    # Fichiers sources (scans bruts)
    fichier_brut_recto = models.CharField(max_length=255, help_text="Chemin du scan brut recto")
    fichier_brut_verso = models.CharField(
        max_length=255,
        blank=True,
        help_text="Chemin du scan brut verso (optionnel si fiche recto seulement)",
    )

    # Fichier résultat (fusionné et prétraité)
    fichier_fusionne = models.ImageField(
        upload_to='prepared_images/%Y/',
        unique=True,
        help_text="Image fusionnée recto+verso optimisée pour OCR",
    )

    # Métadonnées de traitement
    operations_effectuees = models.JSONField(
        default=dict,
        help_text="Liste des opérations de traitement (rotation, crop, contraste, etc.)",
    )

    # Traçabilité
    operateur = models.ForeignKey(
        Utilisateur,
        on_delete=models.SET_NULL,
        null=True,
        related_name='preparations_images',
        help_text="Utilisateur ayant effectué la préparation",
    )
    date_preparation = models.DateTimeField(
        auto_now_add=True, help_text="Date et heure de la préparation"
    )
    notes = models.TextField(blank=True, help_text="Notes ou remarques sur cette préparation")

    class Meta:
        verbose_name = "Préparation d'image"
        verbose_name_plural = "Préparations d'images"
        ordering = ['-date_preparation']
        indexes = [
            models.Index(fields=['date_preparation']),
            models.Index(fields=['operateur']),
        ]

    def __str__(self):
        return f"Préparation #{self.id} - {self.date_preparation.strftime('%Y-%m-%d %H:%M')}"


class TranscriptionBrute(models.Model):
    fichier_source = models.CharField(max_length=255, unique=True)
    json_brut = models.JSONField()
    date_importation = models.DateTimeField(auto_now_add=True)
    traite = models.BooleanField(default=False)

    def __str__(self):
        return f"Transcription {self.fichier_source}"


class EspeceCandidate(models.Model):
    nom_transcrit = models.CharField(max_length=100, unique=True)
    espece_validee = models.ForeignKey(Espece, on_delete=models.SET_NULL, null=True, blank=True)
    validation_manuelle = models.BooleanField(default=False)
    score_similarite = models.FloatField(
        default=0.0, help_text="Score de similarité en pourcentage (0-100%)"
    )

    def __str__(self):
        return self.nom_transcrit


class ImportationEnCours(models.Model):
    transcription = models.OneToOneField(TranscriptionBrute, on_delete=models.CASCADE)
    fiche_observation = models.OneToOneField(
        'observations.FicheObservation', on_delete=models.SET_NULL, null=True, blank=True
    )
    espece_candidate = models.ForeignKey(
        EspeceCandidate, on_delete=models.SET_NULL, null=True, blank=True
    )
    observateur = models.ForeignKey(Utilisateur, on_delete=models.SET_NULL, null=True, blank=True)
    statut = models.CharField(
        max_length=20,
        choices=STATUT_IMPORTATION_CHOICES,
        default='en_attente',
    )
    date_creation = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Import {self.transcription.fichier_source} - {self.statut}"
