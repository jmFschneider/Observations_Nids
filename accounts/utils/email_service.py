"""
Service d'envoi d'emails pour les notifications utilisateurs.
Centralise la logique d'envoi d'emails avec templates HTML et texte.
"""

import logging

from django.conf import settings
from django.contrib.sites.models import Site
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags

logger = logging.getLogger(__name__)


class EmailService:
    """Service centralisé pour l'envoi d'emails"""

    @staticmethod
    def _get_site_url():
        """
        Récupère l'URL du site depuis la configuration Django Sites.

        Returns:
            str: Le domaine du site configuré (ex: 'pilote.observation-nids.meteo-poelley50.fr')
        """
        try:
            site = Site.objects.get_current()
            # Retirer le slash final si présent
            domain = site.domain.rstrip('/')
            return domain
        except Exception as e:
            logger.warning(f"Impossible de récupérer le site configuré : {e}")
            # Fallback sur ALLOWED_HOSTS
            return settings.ALLOWED_HOSTS[0] if settings.ALLOWED_HOSTS else 'localhost'

    @staticmethod
    def envoyer_email_demande_enregistree(utilisateur):
        """
        Envoie un email à l'utilisateur pour confirmer que sa demande est enregistrée.

        Args:
            utilisateur: L'utilisateur qui a fait la demande

        Returns:
            bool: True si l'email a été envoyé avec succès, False sinon
        """
        if not utilisateur.email:
            logger.warning(
                f"L'utilisateur {utilisateur.username} n'a pas d'email, email de confirmation non envoyé"
            )
            return False

        try:
            sujet = "[Observations Nids] Votre demande d'inscription a été enregistrée"

            contexte = {
                'utilisateur': utilisateur,
            }

            html_content = render_to_string(
                'accounts/emails/demande_enregistree_utilisateur.html', contexte
            )
            text_content = strip_tags(html_content)

            email = EmailMultiAlternatives(
                subject=sujet,
                body=text_content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[utilisateur.email],
            )
            email.attach_alternative(html_content, "text/html")
            email.send()

            logger.info(f"Email de confirmation de demande envoyé à {utilisateur.email}")
            return True

        except Exception as e:
            logger.error(
                f"Erreur lors de l'envoi de l'email de confirmation de demande pour {utilisateur.username}: {e}"
            )
            return False

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
                'site_url': EmailService._get_site_url(),
            }

            # Rendu des templates HTML et texte
            html_content = render_to_string('accounts/emails/nouvelle_demande_admin.html', contexte)
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
    def envoyer_email_compte_valide(utilisateur, message_personnalise=""):
        """
        Envoie un email à l'utilisateur quand son compte est validé par l'admin.

        Args:
            utilisateur: L'utilisateur dont le compte a été validé
            message_personnalise: Message personnalisé de l'admin (optionnel)

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
                'site_url': EmailService._get_site_url(),
                'message_personnalise': message_personnalise,
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
                'site_url': EmailService._get_site_url(),
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

    @staticmethod
    def envoyer_email_reinitialisation_mdp(utilisateur, uid, token):
        """
        Envoie un email à l'utilisateur avec un lien de réinitialisation de mot de passe.

        Args:
            utilisateur: L'utilisateur qui demande la réinitialisation
            uid: L'UID encodé de l'utilisateur
            token: Le token de réinitialisation

        Returns:
            bool: True si l'email a été envoyé avec succès, False sinon
        """
        if not utilisateur.email:
            logger.warning(f"L'utilisateur {utilisateur.username} n'a pas d'email")
            return False

        try:
            sujet = "[Observations Nids] Réinitialisation de votre mot de passe"

            # Construire l'URL de réinitialisation
            site_url = EmailService._get_site_url()
            # Ajouter http:// ou https:// selon la configuration
            protocole = 'https' if not settings.DEBUG else 'http'
            reset_url = (
                f"{protocole}://{site_url}/accounts/reinitialiser-mot-de-passe/{uid}/{token}/"
            )

            # Contexte pour le template
            contexte = {
                'utilisateur': utilisateur,
                'reset_url': reset_url,
                'site_url': site_url,
            }

            # Rendu des templates HTML et texte
            html_content = render_to_string(
                'accounts/emails/reinitialisation_mot_de_passe.html', contexte
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

            logger.info(f"Email de réinitialisation de mot de passe envoyé à {utilisateur.email}")
            return True

        except Exception as e:
            logger.error(
                f"Erreur lors de l'envoi de l'email de réinitialisation pour {utilisateur.username}: {e}"
            )
            return False

    @staticmethod
    def envoyer_email_rappel_compte(utilisateur, uid, token, message_personnalise=""):
        """
        Envoie un email à l'utilisateur avec un rappel des données de son compte
        et un lien optionnel de réinitialisation de mot de passe.

        Args:
            utilisateur: L'utilisateur à qui envoyer le rappel
            uid: L'UID encodé de l'utilisateur pour le lien de réinitialisation
            token: Le token de réinitialisation de mot de passe
            message_personnalise: Message optionnel de l'administrateur (défaut: "")

        Returns:
            bool: True si l'email a été envoyé avec succès, False sinon
        """
        if not utilisateur.email:
            logger.warning(f"L'utilisateur {utilisateur.username} n'a pas d'email")
            return False

        try:
            sujet = "[Observations Nids] Rappel des informations de votre compte"

            # Construire l'URL de réinitialisation de mot de passe
            site_url = EmailService._get_site_url()
            # Ajouter http:// ou https:// selon la configuration
            protocole = 'https' if not settings.DEBUG else 'http'
            reset_url = (
                f"{protocole}://{site_url}/accounts/reinitialiser-mot-de-passe/{uid}/{token}/"
            )

            # Contexte pour le template
            contexte = {
                'utilisateur': utilisateur,
                'reset_url': reset_url,
                'site_url': site_url,
                'message_personnalise': message_personnalise,
            }

            # Rendu des templates HTML et texte
            html_content = render_to_string(
                'accounts/emails/rappel_compte_utilisateur.html', contexte
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

            logger.info(f"Email de rappel de compte envoyé à {utilisateur.email}")
            return True

        except Exception as e:
            logger.error(
                f"Erreur lors de l'envoi de l'email de rappel pour {utilisateur.username}: {e}"
            )
            return False
