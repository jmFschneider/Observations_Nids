
from django.db import models

from accounts.models import Utilisateur
from core.constants import CATEGORIE_MODIFICATION_CHOICES


class HistoriqueModification(models.Model):
    fiche = models.ForeignKey(
        'observations.FicheObservation', on_delete=models.CASCADE, related_name="modifications"
    )
    champ_modifie = models.CharField(max_length=100)
    ancienne_valeur = models.TextField()
    nouvelle_valeur = models.TextField()
    date_modification = models.DateTimeField(auto_now_add=True)
    modifie_par = models.ForeignKey(Utilisateur, on_delete=models.SET_NULL, null=True, blank=True)
    categorie = models.CharField(
        max_length=20, choices=CATEGORIE_MODIFICATION_CHOICES, default='fiche', db_index=True
    )

    class Meta:
        verbose_name = "Historique de modification"
        verbose_name_plural = "Historiques des modifications"
        ordering = ['-date_modification']

    def __str__(self):
        modifie_par_str = f" par {self.modifie_par.username}" if self.modifie_par else ""
        return f"Modification {self.champ_modifie} ({self.date_modification}){modifie_par_str}"
