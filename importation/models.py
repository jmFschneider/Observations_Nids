# importation/models.py
from django.db import models

# Importer Utilisateur depuis administration au lieu de observations
from administration.models import Utilisateur
from observations.models import Espece, FicheObservation


class TranscriptionBrute(models.Model):
    """Modèle pour stocker les données brutes transcrites avant réconciliation"""
    fichier_source = models.CharField(max_length=255, unique=True)
    json_brut = models.JSONField()
    date_importation = models.DateTimeField(auto_now_add=True)
    traite = models.BooleanField(default=False)

    def __str__(self):
        return f"Transcription {self.fichier_source}"


class EspeceCandidate(models.Model):
    """Modèle pour stocker les noms d'espèces à réconcilier"""
    nom_transcrit = models.CharField(max_length=100, unique=True)
    espece_validee = models.ForeignKey(Espece, on_delete=models.SET_NULL, null=True, blank=True)
    validation_manuelle = models.BooleanField(default=False)
    score_similarite = models.FloatField(default=0.0, help_text="Score de similarité en pourcentage (0-100%)")

    def __str__(self):
        return self.nom_transcrit


class ImportationEnCours(models.Model):
    """Modèle pour suivre les importations en cours"""
    transcription = models.OneToOneField(TranscriptionBrute, on_delete=models.CASCADE)
    fiche_observation = models.OneToOneField(FicheObservation, on_delete=models.SET_NULL, null=True, blank=True)
    espece_candidate = models.ForeignKey(EspeceCandidate, on_delete=models.SET_NULL, null=True, blank=True)
    observateur = models.ForeignKey(Utilisateur, on_delete=models.SET_NULL, null=True, blank=True)
    statut = models.CharField(max_length=20, choices=[
        ('en_attente', 'En attente de validation'),
        ('erreur', 'Erreur détectée'),
        ('complete', 'importation complétée')
    ], default='en_attente')
    date_creation = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Import {self.transcription.fichier_source} - {self.statut}"