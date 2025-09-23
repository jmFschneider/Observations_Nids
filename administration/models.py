# administration/models.py
from django.contrib.auth.models import AbstractUser
from django.db import models


class Utilisateur(AbstractUser):
    """Modèle utilisateur personnalisé pour l'application"""

    ROLES = [
        ('observateur', 'Observateur'),
        ('reviewer', 'Reviewer'),
        ('administrateur', 'Administrateur'),
    ]

    role = models.CharField(max_length=15, choices=ROLES, default='observateur')
    est_valide = models.BooleanField(default=False)  # Validation par l'administrateur
    est_transcription = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.get_role_display()})"

    class Meta:
        verbose_name = "Utilisateur"
        verbose_name_plural = "Utilisateurs"
