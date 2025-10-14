
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone

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


class Notification(models.Model):
    """
    Modèle pour gérer les notifications internes de l'application.
    Utilisé principalement pour notifier les administrateurs des demandes de compte.
    """

    TYPE_CHOICES = [
        ('demande_compte', 'Demande de compte'),
        ('compte_valide', 'Compte validé'),
        ('compte_refuse', 'Compte refusé'),
        ('info', 'Information'),
        ('warning', 'Avertissement'),
    ]

    destinataire = models.ForeignKey(
        Utilisateur,
        on_delete=models.CASCADE,
        related_name='notifications',
        verbose_name="Destinataire",
    )
    type_notification = models.CharField(
        max_length=20, choices=TYPE_CHOICES, default='info', verbose_name="Type"
    )
    titre = models.CharField(max_length=255, verbose_name="Titre")
    message = models.TextField(verbose_name="Message")
    lien = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="Lien",
        help_text="URL relative vers la ressource concernée",
    )
    est_lue = models.BooleanField(default=False, verbose_name="Lue")
    date_creation = models.DateTimeField(default=timezone.now, verbose_name="Date de création")
    date_lecture = models.DateTimeField(
        blank=True, null=True, verbose_name="Date de lecture"
    )

    # Référence optionnelle vers l'utilisateur concerné par la notification
    utilisateur_concerne = models.ForeignKey(
        Utilisateur,
        on_delete=models.CASCADE,
        related_name='notifications_le_concernant',
        blank=True,
        null=True,
        verbose_name="Utilisateur concerné",
    )

    class Meta:
        verbose_name = "Notification"
        verbose_name_plural = "Notifications"
        ordering = ['-date_creation']
        indexes = [
            models.Index(fields=['destinataire', 'est_lue']),
            models.Index(fields=['type_notification']),
        ]

    def __str__(self):
        return f"{self.get_type_notification_display()} - {self.titre} ({self.destinataire.username})"

    def marquer_comme_lue(self):
        """Marque la notification comme lue"""
        if not self.est_lue:
            self.est_lue = True
            self.date_lecture = timezone.now()
            self.save()
