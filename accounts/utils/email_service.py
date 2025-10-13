"""
Service d'envoi d'emails pour les notifications utilisateurs.
Centralise la logique d'envoi d'emails avec templates HTML et texte.
"""

import logging
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags

logger = logging.getLogger(__name__)


class EmailService:
    """Service centralisé pour l'envoi d'emails"""

    @staticmethod
    def envoyer_email_nouvelle_demande_compte(utilisateur):
        """
        Envoie un email à l'administrateur quand une nouvelle demande de compte est reçue.

        Args:
            utilisateur: L'utilisateur qui a fait la demande

        Returns:
            bool: True si l'email a été envoyé avec succès, False sinon
        """
        if not settings.ADMIN_EMAIL:
            logger.warning("ADMIN_EMAIL n'est pas configuré, email non envoyé")
            return False

        try:
            sujet = f"[Observations Nids] Nouvelle demande de compte - {utilisateur.username}"

            # Contexte pour le template
            contexte = {
                'utilisateur': utilisateur,
                'site_url': settings.ALLOWED_HOSTS[0] if settings.ALLOWED_HOSTS else 'localhost',
            }

            # Rendu des templates HTML et texte
            html_content = render_to_string(
                'accounts/emails/nouvelle_demande_admin.html', contexte
            )
            text_content = strip_tags(html_content)

            # Création et envoi de l'email
            email = EmailMultiAlternatives(
                subject=sujet,
                body=text_content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[settings.ADMIN_EMAIL],
            )
            email.attach_alternative(html_content, "text/html")
            email.send()

            logger.info(
                f"Email de demande de compte envoyé à {settings.ADMIN_EMAIL} pour {utilisateur.username}"
            )
            return True

        except Exception as e:
            logger.error(
                f"Erreur lors de l'envoi de l'email de demande de compte pour {utilisateur.username}: {e}"
            )
            return False

    @staticmethod
    def envoyer_email_compte_valide(utilisateur):
        """
        Envoie un email à l'utilisateur quand son compte est validé par l'admin.

        Args:
            utilisateur: L'utilisateur dont le compte a été validé

        Returns:
            bool: True si l'email a été envoyé avec succès, False sinon
        """
        if not utilisateur.email:
            logger.warning(f"L'utilisateur {utilisateur.username} n'a pas d'email")
            return False

        try:
            sujet = "[Observations Nids] Votre compte a été validé"

            # Contexte pour le template
            contexte = {
                'utilisateur': utilisateur,
                'site_url': settings.ALLOWED_HOSTS[0] if settings.ALLOWED_HOSTS else 'localhost',
            }

            # Rendu des templates HTML et texte
            html_content = render_to_string(
                'accounts/emails/compte_valide_utilisateur.html', contexte
            )
            text_content = strip_tags(html_content)

            # Création et envoi de l'email
            email = EmailMultiAlternatives(
                subject=sujet,
                body=text_content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[utilisateur.email],
            )
            email.attach_alternative(html_content, "text/html")
            email.send()

            logger.info(f"Email de validation envoyé à {utilisateur.email}")
            return True

        except Exception as e:
            logger.error(
                f"Erreur lors de l'envoi de l'email de validation pour {utilisateur.username}: {e}"
            )
            return False

    @staticmethod
    def envoyer_email_compte_refuse(utilisateur, raison=""):
        """
        Envoie un email à l'utilisateur quand son compte est refusé par l'admin.

        Args:
            utilisateur: L'utilisateur dont le compte a été refusé
            raison: Raison du refus (optionnel)

        Returns:
            bool: True si l'email a été envoyé avec succès, False sinon
        """
        if not utilisateur.email:
            logger.warning(f"L'utilisateur {utilisateur.username} n'a pas d'email")
            return False

        try:
            sujet = "[Observations Nids] Votre demande de compte"

            # Contexte pour le template
            contexte = {
                'utilisateur': utilisateur,
                'raison': raison,
                'site_url': settings.ALLOWED_HOSTS[0] if settings.ALLOWED_HOSTS else 'localhost',
            }

            # Rendu des templates HTML et texte
            html_content = render_to_string(
                'accounts/emails/compte_refuse_utilisateur.html', contexte
            )
            text_content = strip_tags(html_content)

            # Création et envoi de l'email
            email = EmailMultiAlternatives(
                subject=sujet,
                body=text_content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[utilisateur.email],
            )
            email.attach_alternative(html_content, "text/html")
            email.send()

            logger.info(f"Email de refus envoyé à {utilisateur.email}")
            return True

        except Exception as e:
            logger.error(
                f"Erreur lors de l'envoi de l'email de refus pour {utilisateur.username}: {e}"
            )
            return False
