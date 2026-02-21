"""
Modèles pour le suivi des transcriptions OCR en production.
"""

from django.core.validators import MinValueValidator
from django.db import models

from observations.models import FicheObservation


class TranscriptionOCR(models.Model):
    """
    Stocke les métadonnées des transcriptions OCR effectuées.
    """

    # ========================================
    # LIEN VERS LA FICHE (Optionnel si pas encore importée)
    # ========================================
    fiche = models.ForeignKey(
        FicheObservation,
        on_delete=models.CASCADE,
        related_name="transcriptions_ocr",
        verbose_name="Fiche de référence",
        null=True,
        blank=True,
    )

    # ========================================
    # MÉTADONNÉES DE LA TRANSCRIPTION
    # ========================================
    chemin_json = models.CharField(
        max_length=255,
        verbose_name="Chemin du fichier JSON",
        help_text="Chemin vers le fichier JSON de la transcription OCR",
    )

    chemin_image = models.CharField(
        max_length=255,
        verbose_name="Chemin de l'image source",
        help_text="Chemin de l'image utilisée pour cette transcription",
    )

    repertoire = models.CharField(
        max_length=255,
        blank=True,
        default='',
        db_index=True,
        verbose_name="Répertoire de l'image",
        help_text="Répertoire parent (dirname de chemin_image) pour agrégations par dossier",
    )

    modele_ocr = models.CharField(
        max_length=50,
        default='gemini_3_flash',
        verbose_name="Modèle OCR",
    )

    date_transcription = models.DateTimeField(
        auto_now_add=True, verbose_name="Date de transcription"
    )

    statut = models.CharField(
        max_length=20,
        choices=[
            ('succes', 'Succès'),
            ('erreur', 'Erreur'),
            ('en_cours', 'En cours'),
        ],
        default='en_cours',
        verbose_name="Statut du traitement",
    )

    # Performance du traitement
    temps_traitement_secondes = models.FloatField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0.0)],
        verbose_name="Temps de traitement (s)",
    )

    erreur_message = models.TextField(
        blank=True,
        verbose_name="Message d'erreur",
        help_text="Détails de l'erreur le cas échéant",
    )

    class Meta:
        db_table = 'ocr_transcription_ocr'
        verbose_name = 'Transcription OCR'
        verbose_name_plural = 'Transcriptions OCR'
        ordering = ['-date_transcription']
        indexes = [
            models.Index(fields=['fiche']),
            models.Index(fields=['statut']),
            models.Index(fields=['statut', 'repertoire'], name='ocr_statut_repertoire_idx'),
        ]

    def __str__(self):
        fiche_num = self.fiche.num_fiche if self.fiche else 'N/A'
        return f"OCR {self.modele_ocr} (Fiche #{fiche_num}) - {self.statut}"
