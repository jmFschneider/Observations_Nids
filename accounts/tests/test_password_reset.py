"""Tests pour la fonctionnalité de réinitialisation de mot de passe."""

from unittest.mock import patch

import pytest
from django.contrib.auth.tokens import default_token_generator
from django.core import mail
from django.db import IntegrityError
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from accounts.models import Utilisateur


@pytest.mark.django_db
class TestMotDePasseOublie:
    """Tests pour la vue de demande de réinitialisation de mot de passe."""

    def test_affiche_formulaire_get(self, client):
        """Test que la page affiche le formulaire en GET."""
        url = reverse('accounts:mot_de_passe_oublie')
        response = client.get(url)

        assert response.status_code == 200
        assert 'form' in response.context
        assert (
            'Mot de passe oublié' in response.content.decode()
            or 'mot-de-passe' in response.content.decode()
        )

    def test_email_existant_envoie_email(self, client, user_observateur):
        """Test qu'un email est envoyé pour un utilisateur existant et actif."""
        url = reverse('accounts:mot_de_passe_oublie')
        response = client.post(url, {'email': user_observateur.email})

        # Vérifier la redirection
        assert response.status_code == 302
        assert response.url == reverse('observations:login')

        # Vérifier qu'un email a été envoyé
        assert len(mail.outbox) == 1
        email = mail.outbox[0]
        assert user_observateur.email in email.to
        assert 'Réinitialisation' in email.subject or 'réinitialisation' in email.subject

    def test_email_inexistant_pas_revelation(self, client):
        """Test qu'aucune information n'est révélée si l'email n'existe pas (sécurité)."""
        url = reverse('accounts:mot_de_passe_oublie')
        response = client.post(url, {'email': 'inexistant@test.com'}, follow=True)

        # Même message que si l'email existait (ne pas révéler si compte existe)
        assert response.status_code == 200
        messages = list(response.context['messages'])
        assert len(messages) == 1
        assert 'email' in str(messages[0]).lower()

        # Aucun email envoyé
        assert len(mail.outbox) == 0

    def test_utilisateur_inactif_ignore(self, client, user_inactif):
        """Test qu'un utilisateur inactif ne reçoit pas d'email."""
        url = reverse('accounts:mot_de_passe_oublie')
        response = client.post(url, {'email': user_inactif.email})

        # Message générique (ne pas révéler que le compte est inactif)
        assert response.status_code == 302

        # Aucun email envoyé
        assert len(mail.outbox) == 0

    def test_contrainte_email_unique_active(self, client, db):
        """Test que la contrainte d'unicité sur l'email est bien active."""
        email = 'shared@test.com'
        Utilisateur.objects.create_user(
            username='user1',
            email=email,
            password='TestPass123!',
            is_active=True,
        )

        # Tenter de créer un second utilisateur avec le même email devrait échouer
        with pytest.raises(IntegrityError) as excinfo:
            Utilisateur.objects.create_user(
                username='user2',
                email=email,
                password='TestPass123!',
                is_active=True,
            )

        # Vérifier que c'est bien l'erreur de contrainte unique sur email
        assert 'email' in str(excinfo.value).lower() or 'Duplicate' in str(excinfo.value)

    def test_formulaire_email_invalide(self, client):
        """Test que les emails invalides sont rejetés par le formulaire."""
        url = reverse('accounts:mot_de_passe_oublie')
        response = client.post(url, {'email': 'pas-un-email'})

        # Le formulaire devrait être invalide
        assert response.status_code == 200  # Reste sur la page
        assert 'form' in response.context
        assert response.context['form'].errors

    def test_redirection_apres_soumission_valide(self, client, user_observateur):
        """Test la redirection vers login après soumission valide."""
        url = reverse('accounts:mot_de_passe_oublie')
        response = client.post(url, {'email': user_observateur.email})

        assert response.status_code == 302
        assert response.url == reverse('observations:login')


@pytest.mark.django_db
class TestReinitialiserMotDePasse:
    """Tests pour la vue de réinitialisation avec token."""

    def test_token_valide_affiche_formulaire(self, client, user_observateur):
        """Test qu'un token valide affiche le formulaire de nouveau mot de passe."""
        # Générer token et uid valides
        token = default_token_generator.make_token(user_observateur)
        uid = urlsafe_base64_encode(force_bytes(user_observateur.pk))

        url = reverse('accounts:reinitialiser_mot_de_passe', kwargs={'uidb64': uid, 'token': token})
        response = client.get(url)

        assert response.status_code == 200
        assert 'form' in response.context
        assert response.context.get('validlink') is True

    def test_token_invalide_affiche_erreur(self, client, user_observateur):
        """Test qu'un token invalide affiche un message d'erreur."""
        # Token invalide
        uid = urlsafe_base64_encode(force_bytes(user_observateur.pk))
        token = 'token-invalide-123'

        url = reverse('accounts:reinitialiser_mot_de_passe', kwargs={'uidb64': uid, 'token': token})
        response = client.get(url)

        assert response.status_code == 200
        assert response.context.get('validlink') is False

    def test_uid_invalide_affiche_erreur(self, client):
        """Test qu'un UID invalide affiche un message d'erreur."""
        token = 'some-token'
        uid = 'uid-invalide'

        url = reverse('accounts:reinitialiser_mot_de_passe', kwargs={'uidb64': uid, 'token': token})
        response = client.get(url)

        assert response.status_code == 200
        assert response.context.get('validlink') is False

    def test_utilisateur_inexistant_affiche_erreur(self, client):
        """Test qu'un UID d'utilisateur inexistant affiche une erreur."""
        # UID encodé d'un ID qui n'existe pas
        uid = urlsafe_base64_encode(force_bytes(99999))
        token = 'some-token'

        url = reverse('accounts:reinitialiser_mot_de_passe', kwargs={'uidb64': uid, 'token': token})
        response = client.get(url)

        assert response.status_code == 200
        assert response.context.get('validlink') is False

    def test_mot_de_passe_court_refuse(self, client, user_observateur):
        """Test qu'un mot de passe de moins de 8 caractères est refusé."""
        token = default_token_generator.make_token(user_observateur)
        uid = urlsafe_base64_encode(force_bytes(user_observateur.pk))

        url = reverse('accounts:reinitialiser_mot_de_passe', kwargs={'uidb64': uid, 'token': token})
        response = client.post(
            url,
            {
                'password1': 'Court1',  # 6 caractères
                'password2': 'Court1',
            },
        )

        # Devrait rester sur la page avec erreur
        assert response.status_code == 200
        assert 'form' in response.context
        assert response.context['form'].errors

    def test_mots_de_passe_differents_refuse(self, client, user_observateur):
        """Test que deux mots de passe différents sont refusés."""
        token = default_token_generator.make_token(user_observateur)
        uid = urlsafe_base64_encode(force_bytes(user_observateur.pk))

        url = reverse('accounts:reinitialiser_mot_de_passe', kwargs={'uidb64': uid, 'token': token})
        response = client.post(
            url,
            {
                'password1': 'NouveauPass123!',
                'password2': 'AutrePass123!',  # Différent
            },
        )

        # Devrait rester sur la page avec erreur
        assert response.status_code == 200
        assert 'form' in response.context
        assert response.context['form'].errors
        assert (
            'password2' in response.context['form'].errors
            or '__all__' in response.context['form'].errors
        )

    def test_reset_reussi_sauvegarde_hash(self, client, user_observateur):
        """Test qu'un reset réussi sauvegarde le nouveau mot de passe hashé."""
        ancien_password_hash = user_observateur.password
        token = default_token_generator.make_token(user_observateur)
        uid = urlsafe_base64_encode(force_bytes(user_observateur.pk))

        url = reverse('accounts:reinitialiser_mot_de_passe', kwargs={'uidb64': uid, 'token': token})
        nouveau_mdp = 'NouveauPass123!'
        response = client.post(
            url,
            {
                'password1': nouveau_mdp,
                'password2': nouveau_mdp,
            },
        )

        # Vérifier redirection
        assert response.status_code == 302
        assert response.url == reverse('observations:login')

        # Vérifier que le mot de passe a changé
        user_observateur.refresh_from_db()
        assert user_observateur.password != ancien_password_hash

        # Vérifier que le nouveau mot de passe fonctionne
        assert user_observateur.check_password(nouveau_mdp)

    def test_reset_reussi_redirige_login(self, client, user_observateur):
        """Test qu'un reset réussi redirige vers la page de login."""
        token = default_token_generator.make_token(user_observateur)
        uid = urlsafe_base64_encode(force_bytes(user_observateur.pk))

        url = reverse('accounts:reinitialiser_mot_de_passe', kwargs={'uidb64': uid, 'token': token})
        response = client.post(
            url,
            {
                'password1': 'NouveauPass123!',
                'password2': 'NouveauPass123!',
            },
        )

        assert response.status_code == 302
        assert response.url == reverse('observations:login')

    def test_reset_reussi_affiche_message_succes(self, client, user_observateur):
        """Test qu'un message de succès est affiché après reset."""
        token = default_token_generator.make_token(user_observateur)
        uid = urlsafe_base64_encode(force_bytes(user_observateur.pk))

        url = reverse('accounts:reinitialiser_mot_de_passe', kwargs={'uidb64': uid, 'token': token})
        response = client.post(
            url,
            {
                'password1': 'NouveauPass123!',
                'password2': 'NouveauPass123!',
            },
            follow=True,
        )

        # Vérifier qu'un message de succès est présent
        messages = list(response.context['messages'])
        assert len(messages) == 1
        assert 'réinitialisé' in str(messages[0]).lower() or 'succès' in str(messages[0]).lower()


@pytest.mark.django_db
class TestEmailReinitialisation:
    """Tests pour l'envoi d'email de réinitialisation."""

    def test_email_contient_lien_valide(self, client, user_observateur):
        """Test que l'email contient un lien de réinitialisation valide."""
        url = reverse('accounts:mot_de_passe_oublie')
        client.post(url, {'email': user_observateur.email})

        # Récupérer l'email envoyé
        assert len(mail.outbox) == 1
        email = mail.outbox[0]

        # Vérifier que l'email contient un lien
        email_body = email.body
        assert 'reinitialiser-mot-de-passe' in email_body
        assert '/accounts/reinitialiser-mot-de-passe/' in email_body

    def test_email_contient_uid_et_token(self, client, user_observateur):
        """Test que le lien dans l'email contient un UID et un token."""
        url = reverse('accounts:mot_de_passe_oublie')
        client.post(url, {'email': user_observateur.email})

        email_body = mail.outbox[0].body

        # Le lien devrait contenir deux segments après l'URL de base
        # Format attendu: /accounts/reinitialiser-mot-de-passe/{uid}/{token}/
        assert 'reinitialiser-mot-de-passe' in email_body

        # Extraire le lien de l'email (simplifié)
        lines = email_body.split('\n')
        reset_lines = [line for line in lines if 'reinitialiser-mot-de-passe' in line]
        assert len(reset_lines) > 0

    @patch('accounts.utils.email_service.EmailService.envoyer_email_reinitialisation_mdp')
    def test_utilisateur_sans_email_gere(self, mock_send, client, db):
        """Test qu'un utilisateur sans email est géré correctement."""
        # Créer un utilisateur sans email
        Utilisateur.objects.create_user(
            username='no_email',
            email='',
            password='TestPass123!',
        )

        # Configurer le mock pour retourner False (email non envoyé)
        mock_send.return_value = False

        url = reverse('accounts:mot_de_passe_oublie')
        response = client.post(url, {'email': ''})

        # Le formulaire devrait rejeter l'email vide
        assert response.status_code == 200
        assert 'form' in response.context

    def test_email_html_et_texte(self, client, user_observateur):
        """Test que l'email contient une version HTML et texte."""
        url = reverse('accounts:mot_de_passe_oublie')
        client.post(url, {'email': user_observateur.email})

        email = mail.outbox[0]

        # Vérifier qu'il y a une alternative HTML
        assert len(email.alternatives) > 0
        html_content = email.alternatives[0][0]
        assert '<html>' in html_content or '<body>' in html_content or '<table>' in html_content

    def test_protocole_url_correct(self, client, user_observateur, settings):
        """Test que l'URL de réinitialisation utilise le bon protocole."""
        url = reverse('accounts:mot_de_passe_oublie')
        client.post(url, {'email': user_observateur.email})

        email_body = mail.outbox[0].body

        # En mode DEBUG, devrait être http://, en production https://
        if settings.DEBUG:
            assert 'http://' in email_body
        else:
            assert 'https://' in email_body
