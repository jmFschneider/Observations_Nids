from django.conf import settings
from django.db import models


class Feedback(models.Model):
    CATEGORIES = [
        ("BUG", "Bug / Problème technique"),
        ("IDEA", "Suggestion / Idée"),
        ("DATA", "Donnée erronée"),
        ("QUESTION", "Question"),
        ("OTHER", "Autre"),
    ]

    STATUS = [
        ("NEW", "Nouveau"),
        ("READ", "Lu"),
        ("IN_PROGRESS", "En cours"),
        ("WAITING_USER", "En attente d'infos"),
        ("RESOLVED", "Résolu"),
        ("ARCHIVED", "Archivé"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Utilisateur",
    )
    content = models.TextField(verbose_name="Message")
    url_source = models.CharField(max_length=500, blank=True, verbose_name="URL d'origine")

    # Champs remplis par l'IA
    category = models.CharField(
        max_length=20,
        choices=CATEGORIES,
        default="OTHER",
        verbose_name="Catégorie (IA)",
    )
    urgency = models.IntegerField(default=1, verbose_name="Urgence (1-5)")
    sentiment = models.CharField(max_length=50, blank=True, verbose_name="Sentiment")
    ai_summary = models.CharField(max_length=200, blank=True, verbose_name="Résumé IA")

    status = models.CharField(max_length=20, choices=STATUS, default="NEW", verbose_name="Statut")

    # Champs de décision Administrateur
    admin_note = models.TextField(blank=True, verbose_name="Note / Décision Administrateur (Legacy)")
    is_public_response = models.BooleanField(default=False, verbose_name="Rendre la note publique")

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    updated_at = models.DateTimeField(auto_now=True)
    last_activity = models.DateTimeField(auto_now_add=True, verbose_name="Dernière activité")

    class Meta:
        verbose_name = "Feedback"
        verbose_name_plural = "Feedbacks"
        ordering = ["-last_activity"]

    def __str__(self):
        return f"{self.category} - {self.user} ({self.created_at.strftime('%d/%m/%Y')})"


class FeedbackMessage(models.Model):
    feedback = models.ForeignKey(
        Feedback, on_delete=models.CASCADE, related_name="messages", verbose_name="Feedback"
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Auteur",
    )
    content = models.TextField(verbose_name="Message")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")

    class Meta:
        verbose_name = "Message de feedback"
        verbose_name_plural = "Messages de feedback"
        ordering = ["created_at"]

    def __str__(self):
        return f"Message de {self.author} sur {self.feedback}"
