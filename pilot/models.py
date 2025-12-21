"""
⚠️ ATTENTION: App de PILOTE uniquement - NE PAS déployer en production

Cette app contient les modèles pour l'expérimentation et l'évaluation
des modèles OCR. Elle doit être retirée de INSTALLED_APPS en production.
"""

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from observations.models import FicheObservation


class TranscriptionOCR(models.Model):
    """
    Stocke les métadonnées des transcriptions OCR pour comparaison avec
    les transcriptions de référence corrigées manuellement.

    Cette table permet d'évaluer la qualité de différents modèles OCR
    et configurations d'images (brute vs optimisée).
    """

    # ========================================
    # LIEN VERS LA FICHE DE RÉFÉRENCE
    # ========================================
    fiche = models.ForeignKey(
        FicheObservation,
        on_delete=models.CASCADE,
        related_name="transcriptions_ocr_pilot",
        verbose_name="Fiche de référence",
        help_text="Fiche d'observation corrigée manuellement (vérité terrain)",
        null=True,
        blank=True,
    )

    # ========================================
    # MÉTADONNÉES DE LA TRANSCRIPTION
    # ========================================
    chemin_json = models.CharField(
        max_length=255,
        verbose_name="Chemin du fichier JSON",
        help_text="Chemin vers le fichier JSON brut de la transcription OCR",
    )

    chemin_image = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="Chemin de l'image source",
        help_text="Chemin de l'image utilisée pour cette transcription",
    )

    type_image = models.CharField(
        max_length=20,
        choices=[
            ('brute', 'Image brute'),
            ('optimisee', 'Image optimisée pour OCR'),
        ],
        verbose_name="Type d'image",
        help_text="Type de traitement appliqué à l'image",
    )

    modele_ocr = models.CharField(
        max_length=50,
        choices=[
            ('gemini_3_flash', 'Gemini 3 Flash'),
            ('gemini_3_pro', 'Gemini 3 Pro'),
            ('gemini_2.5_pro', 'Gemini 2.5 Pro'),
            ('gemini_2.5_flash_lite', 'Gemini 2.5 Flash-Lite'),
        ],
        verbose_name="Modèle OCR",
        help_text="Modèle d'IA utilisé pour la transcription",
    )

    date_transcription = models.DateTimeField(
        auto_now_add=True, verbose_name="Date de transcription"
    )

    # ========================================
    # ÉVALUATION DE LA QUALITÉ
    # ========================================
    statut_evaluation = models.CharField(
        max_length=20,
        choices=[
            ('non_evaluee', 'Non évaluée'),
            ('en_cours', 'Évaluation en cours'),
            ('evaluee', 'Évaluée'),
            ('erreur', "Erreur lors de l'évaluation"),
        ],
        default='non_evaluee',
        verbose_name="Statut de l'évaluation",
    )

    date_evaluation = models.DateTimeField(
        null=True, blank=True, verbose_name="Date de l'évaluation"
    )

    # Score global de similarité (0-100%)
    score_global = models.FloatField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0.0), MaxValueValidator(100.0)],
        verbose_name="Score global (%)",
        help_text="Score de similarité global entre OCR et vérité terrain (0-100%)",
    )

    # Compteurs de précision
    nombre_champs_corrects = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        verbose_name="Nombre de champs corrects",
    )

    nombre_champs_total = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        verbose_name="Nombre de champs total",
    )

    # Compteurs d'erreurs par type
    nombre_erreurs_dates = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name="Erreurs sur les dates",
    )

    nombre_erreurs_nombres = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name="Erreurs sur les nombres",
    )

    nombre_erreurs_texte = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name="Erreurs sur le texte",
    )

    nombre_erreurs_especes = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name="Erreurs sur les espèces",
    )

    nombre_erreurs_lieux = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name="Erreurs sur les lieux",
    )

    # Détails de comparaison (format JSON pour flexibilité)
    details_comparaison = models.JSONField(
        null=True,
        blank=True,
        verbose_name="Détails de comparaison",
        help_text="Détails des différences champ par champ au format JSON",
    )

    # Performance du traitement
    temps_traitement_secondes = models.FloatField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0.0)],
        verbose_name="Temps de traitement (s)",
        help_text="Durée du traitement OCR en secondes",
    )

    # Notes manuelles
    notes_evaluation = models.TextField(
        blank=True, verbose_name="Notes d'évaluation", help_text="Notes et observations manuelles"
    )

    class Meta:
        db_table = 'pilot_transcription_ocr'
        verbose_name = '[PILOTE] Transcription OCR'
        verbose_name_plural = '[PILOTE] Transcriptions OCR'
        ordering = ['-date_transcription']
        indexes = [
            models.Index(fields=['fiche', 'modele_ocr']),
            models.Index(fields=['statut_evaluation']),
            models.Index(fields=['score_global']),
        ]

    def __str__(self):
        fiche_num = self.fiche.num_fiche if self.fiche else 'N/A'
        return f"[PILOTE] OCR {self.modele_ocr} - {self.type_image} (Fiche #{fiche_num})"

    @property
    def taux_precision(self):
        """Calcule le taux de précision (champs corrects / total)"""
        if (
            self.nombre_champs_total
            and self.nombre_champs_total > 0
            and self.nombre_champs_corrects is not None
        ):
            return (self.nombre_champs_corrects / self.nombre_champs_total) * 100
        return None

    @property
    def nombre_erreurs_total(self):
        """Calcule le nombre total d'erreurs"""
        return (
            self.nombre_erreurs_dates
            + self.nombre_erreurs_nombres
            + self.nombre_erreurs_texte
            + self.nombre_erreurs_especes
            + self.nombre_erreurs_lieux
        )
