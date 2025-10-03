
from django.db import models


class Localisation(models.Model):
    fiche = models.OneToOneField(
        'observations.FicheObservation', on_delete=models.CASCADE, related_name="localisation"
    )
    commune = models.CharField(max_length=30, default='Non spécifiée')
    lieu_dit = models.CharField(max_length=30, default='Non spécifiée')
    departement = models.CharField(max_length=5, default='00')
    coordonnees = models.CharField(max_length=30, default='0,0')
    latitude = models.CharField(max_length=15, default='0.0')
    longitude = models.CharField(max_length=15, default='0.0')
    altitude = models.CharField(max_length=10, default='0')
    paysage = models.TextField(default='Non spécifié')
    alentours = models.TextField(default='Non spécifié')

    def __str__(self):
        return f"Localisation {self.commune} ({self.departement})"
