
from django.contrib.auth.models import AbstractUser
from django.db import models

from core.constants import ROLE_CHOICES


class Utilisateur(AbstractUser):

    role = models.CharField(max_length=15, choices=ROLE_CHOICES, default='observateur')
    est_valide = models.BooleanField(default=False)
    est_transcription = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.get_role_display()})"

    class Meta:
        verbose_name = "Utilisateur"
        verbose_name_plural = "Utilisateurs"
