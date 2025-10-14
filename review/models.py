from django.db import models

from accounts.models import Utilisateur
from core.constants import STATUT_VALIDATION_CHOICES


class Validation(models.Model):
    fiche = models.ForeignKey(
        'observations.FicheObservation', on_delete=models.CASCADE, related_name="validations"
    )
    reviewer = models.ForeignKey(
        Utilisateur, on_delete=models.CASCADE, limit_choices_to={'role': 'reviewer'}
    )
    statut = models.CharField(max_length=10, choices=STATUT_VALIDATION_CHOICES, default='en_cours')
    date_modification = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date_modification']

    def __str__(self):
        return f"Validation Fiche {self.fiche.num_fiche} par {self.reviewer.username}"

    def save(self, *args, **kwargs):
        if self.pk:
            ancienne_instance = Validation.objects.filter(pk=self.pk).first()
            if ancienne_instance and ancienne_instance.statut != self.statut:
                HistoriqueValidation.objects.create(
                    validation=self,
                    ancien_statut=ancienne_instance.statut,
                    nouveau_statut=self.statut,
                    modifie_par=self.reviewer,
                )

        super().save(*args, **kwargs)


class HistoriqueValidation(models.Model):
    validation = models.ForeignKey(Validation, on_delete=models.CASCADE, related_name="historique")
    ancien_statut = models.CharField(max_length=10, choices=STATUT_VALIDATION_CHOICES)
    nouveau_statut = models.CharField(max_length=10, choices=STATUT_VALIDATION_CHOICES)
    date_modification = models.DateTimeField(auto_now_add=True)
    modifie_par = models.ForeignKey(Utilisateur, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        ordering = ['-date_modification']

    def __str__(self):
        return f"Changement de {self.ancien_statut} à {self.nouveau_statut} (Fiche {self.validation.fiche.num_fiche})"
