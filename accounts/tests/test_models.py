"""
Tests pour l'application accounts
"""

import time
from unittest.mock import patch

import pytest
from django.core import mail
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import Notification, Utilisateur
from accounts.utils.email_service import EmailService


@pytest.mark.django_db
class TestNotificationModel(TestCase):
    """Tests pour le modèle Notification"""

    def setUp(self):
        """Préparer les données de test"""
        # Créer un administrateur
        self.admin = Utilisateur.objects.create_user(
            username='admin_test',
            email='admin@test.com',
            password='testpass123',
            role='administrateur',
            est_valide=True,
            is_active=True,
        )

        # Créer un utilisateur en attente
        self.user_pending = Utilisateur.objects.create_user(
            username='user_pending',
            email='pending@test.com',
            password='testpass123',
            role='observateur',
            est_valide=False,
            is_active=False,
        )

    def test_notification_creation(self):
        """Test de création d'une notification"""
        notification = Notification.objects.create(
            destinataire=self.admin,
            type_notification='demande_compte',
            titre='Test notification',
            message='Message de test',
            utilisateur_concerne=self.user_pending,
        )

        self.assertEqual(notification.destinataire, self.admin)
        self.assertEqual(notification.type_notification, 'demande_compte')
        self.assertFalse(notification.est_lue)
        self.assertIsNone(notification.date_lecture)

    def test_notification_mark_as_read(self):
        """Test du marquage d'une notification comme lue"""
        notification = Notification.objects.create(
            destinataire=self.admin,
            type_notification='demande_compte',
            titre='Test notification',
            message='Message de test',
        )

        # Marquer comme lue
        notification.est_lue = True
        notification.date_lecture = timezone.now()
        notification.save()

        notification.refresh_from_db()
        self.assertTrue(notification.est_lue)
        self.assertIsNotNone(notification.date_lecture)

    def test_notification_str_method(self):
        """Test de la méthode __str__"""
        notification = Notification.objects.create(
            destinataire=self.admin,
            type_notification='demande_compte',
            titre='Test notification',
            message='Message de test',
        )

        expected = f"Demande de compte - Test notification ({self.admin.username})"
        self.assertEqual(str(notification), expected)

    def test_notification_ordering(self):
        """Test de l'ordre des notifications (plus récentes en premier)"""
        _ = Notification.objects.create(
            destinataire=self.admin, titre='Notification 1', message='Message 1'
        )

        # Attendre un peu pour s'assurer que les timestamps sont différents
        time.sleep(0.01)

        _ = Notification.objects.create(
            destinataire=self.admin, titre='Notification 2', message='Message 2'
        )

        notifications = Notification.objects.all()
        # notif2 devrait être en premier car plus récente
        self.assertEqual(notifications[0].titre, 'Notification 2')
        self.assertEqual(notifications[1].titre, 'Notification 1')


@pytest.mark.django_db
class TestEmailService(TestCase):
    """Tests pour le service d'envoi d'emails"""

    def setUp(self):
        """Préparer les données de test"""
        self.user = Utilisateur.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User',
            role='observateur',
            est_valide=False,
        )

    def test_envoyer_email_nouvelle_demande_compte(self):
        """Test d'envoi d'email pour nouvelle demande de compte"""
        # Appeler la méthode
        EmailService.envoyer_email_nouvelle_demande_compte(self.user)

        # Vérifier qu'un email a été envoyé
        self.assertEqual(len(mail.outbox), 1)

        # Vérifier le contenu de l'email
        email = mail.outbox[0]
        self.assertIn('Nouvelle demande de compte', email.subject)
        self.assertIn(self.user.username, email.body)
        self.assertIn(self.user.email, email.body)

    def test_envoyer_email_compte_valide(self):
        """Test d'envoi d'email de validation de compte"""
        EmailService.envoyer_email_compte_valide(self.user)

        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        self.assertIn('validé', email.subject.lower())
        self.assertEqual(email.to[0], self.user.email)

    def test_envoyer_email_compte_refuse(self):
        """Test d'envoi d'email de refus de compte"""
        raison = "Informations incomplètes"
        EmailService.envoyer_email_compte_refuse(self.user, raison)

        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        # Vérifier que le sujet contient "demande de compte" ou similaire
        self.assertIn('demande', email.subject.lower())
        self.assertIn(raison, email.body)
        self.assertEqual(email.to[0], self.user.email)

    def test_email_service_with_missing_admin_email(self):
        """Test du service d'email quand ADMIN_EMAIL n'est pas configuré"""
        with patch('accounts.utils.email_service.settings.ADMIN_EMAIL', ''):
            # Ne devrait pas lever d'exception
            EmailService.envoyer_email_nouvelle_demande_compte(self.user)
            # Aucun email ne devrait être envoyé
            self.assertEqual(len(mail.outbox), 0)


@pytest.mark.django_db
class TestInscriptionPubliqueView(TestCase):
    """Tests pour la vue d'inscription publique"""

    def setUp(self):
        """Préparer le client de test"""
        self.client = Client()
        self.url = reverse('accounts:inscription_publique')

    def test_inscription_publique_get(self):
        """Test d'accès à la page d'inscription"""
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'accounts/inscription_publique.html')
        self.assertContains(response, 'Demande d\'inscription')

    def test_inscription_publique_post_valid(self):
        """Test de soumission d'une demande d'inscription valide"""
        data = {
            'username': 'newuser',
            'email': 'newuser@test.com',
            'first_name': 'New',
            'last_name': 'User',
            'password1': 'TestPass123!',
            'password2': 'TestPass123!',
        }

        response = self.client.post(self.url, data)

        # Vérifier la redirection
        self.assertEqual(response.status_code, 302)

        # Vérifier que l'utilisateur a été créé
        user = Utilisateur.objects.get(username='newuser')
        self.assertEqual(user.email, 'newuser@test.com')
        self.assertFalse(user.est_valide)
        self.assertFalse(user.is_active)

        # Vérifier qu'un email a été envoyé
        self.assertEqual(len(mail.outbox), 1)

    def test_inscription_publique_creates_notifications(self):
        """Test que l'inscription crée des notifications pour les admins"""
        # Créer deux administrateurs
        admin1 = Utilisateur.objects.create_user(
            username='admin1',
            email='admin1@test.com',
            password='testpass123',
            role='administrateur',
            est_valide=True,
            is_active=True,
        )

        admin2 = Utilisateur.objects.create_user(
            username='admin2',
            email='admin2@test.com',
            password='testpass123',
            role='administrateur',
            est_valide=True,
            is_active=True,
        )

        data = {
            'username': 'newuser',
            'email': 'newuser@test.com',
            'first_name': 'New',
            'last_name': 'User',
            'password1': 'TestPass123!',
            'password2': 'TestPass123!',
        }

        self.client.post(self.url, data)

        # Vérifier qu'une notification a été créée pour chaque admin
        notifications = Notification.objects.filter(type_notification='demande_compte')
        self.assertEqual(notifications.count(), 2)

        # Vérifier que les deux admins ont reçu une notification
        destinataires = [notif.destinataire for notif in notifications]
        self.assertIn(admin1, destinataires)
        self.assertIn(admin2, destinataires)

    def test_inscription_publique_post_invalid_passwords_dont_match(self):
        """Test avec des mots de passe qui ne correspondent pas"""
        data = {
            'username': 'newuser',
            'email': 'newuser@test.com',
            'first_name': 'New',
            'last_name': 'User',
            'password1': 'TestPass123!',
            'password2': 'DifferentPass123!',
        }

        response = self.client.post(self.url, data)

        # Devrait rester sur la même page avec des erreurs
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'password')

        # L'utilisateur ne devrait pas avoir été créé
        self.assertFalse(Utilisateur.objects.filter(username='newuser').exists())


@pytest.mark.django_db
class TestValiderUtilisateurView(TestCase):
    """Tests pour la vue de validation d'utilisateur"""

    def setUp(self):
        """Préparer les données de test"""
        self.client = Client()

        # Créer un administrateur
        self.admin = Utilisateur.objects.create_user(
            username='admin',
            email='admin@test.com',
            password='testpass123',
            role='administrateur',
            est_valide=True,
            is_active=True,
        )

        # Créer un utilisateur en attente
        self.user_pending = Utilisateur.objects.create_user(
            username='pending_user',
            email='pending@test.com',
            password='testpass123',
            role='observateur',
            est_valide=False,
            is_active=False,
        )

        # Créer une notification pour cet utilisateur
        self.notification = Notification.objects.create(
            destinataire=self.admin,
            type_notification='demande_compte',
            titre=f'Nouvelle demande : {self.user_pending.username}',
            message='Demande de compte',
            utilisateur_concerne=self.user_pending,
        )

    def test_valider_utilisateur_requires_admin(self):
        """Test que seuls les admins peuvent valider"""
        # Créer un observateur normal
        _ = Utilisateur.objects.create_user(
            username='observateur',
            email='obs@test.com',
            password='testpass123',
            role='observateur',
            est_valide=True,
            is_active=True,
        )

        self.client.login(username='observateur', password='testpass123')
        url = reverse('accounts:valider_utilisateur', kwargs={'user_id': self.user_pending.id})
        response = self.client.post(url)

        # Devrait être redirigé ou refusé
        self.assertNotEqual(response.status_code, 200)

    def test_valider_utilisateur_success(self):
        """Test de validation réussie d'un utilisateur"""
        self.client.login(username='admin', password='testpass123')
        url = reverse('accounts:valider_utilisateur', kwargs={'user_id': self.user_pending.id})

        response = self.client.post(url)

        # Vérifier la redirection
        self.assertEqual(response.status_code, 302)

        # Vérifier que l'utilisateur est maintenant validé
        self.user_pending.refresh_from_db()
        self.assertTrue(self.user_pending.est_valide)
        self.assertTrue(self.user_pending.is_active)

        # Vérifier qu'un email a été envoyé
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to[0], self.user_pending.email)

        # Vérifier que la notification a été marquée comme lue
        self.notification.refresh_from_db()
        self.assertTrue(self.notification.est_lue)


@pytest.mark.django_db
class TestHomePageNotifications(TestCase):
    """Tests pour les notifications sur la page d'accueil"""

    def setUp(self):
        """Préparer les données de test"""
        self.client = Client()

        # Créer un administrateur
        self.admin = Utilisateur.objects.create_user(
            username='admin',
            email='admin@test.com',
            password='testpass123',
            role='administrateur',
            est_valide=True,
            is_active=True,
        )

        # Créer un observateur
        self.observateur = Utilisateur.objects.create_user(
            username='observateur',
            email='obs@test.com',
            password='testpass123',
            role='observateur',
            est_valide=True,
            is_active=True,
        )

    def test_home_page_shows_notification_banner_for_admin(self):
        """Test que le bandeau de notification apparaît pour les admins"""
        # Créer quelques demandes en attente
        for i in range(3):
            Utilisateur.objects.create_user(
                username=f'pending{i}',
                email=f'pending{i}@test.com',
                password='testpass123',
                est_valide=False,
                is_active=False,
            )

        self.client.login(username='admin', password='testpass123')
        response = self.client.get(reverse('observations:home'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '3 demande(s) de compte en attente')
        self.assertContains(response, 'Voir les demandes')
        # Vérifier que le bandeau est présent avec la bonne couleur
        self.assertContains(response, 'background-color: #fff3cd')

    def test_home_page_no_notification_banner_for_non_admin(self):
        """Test que le bandeau n'apparaît pas pour les non-admins"""
        # Créer quelques demandes en attente
        for i in range(3):
            Utilisateur.objects.create_user(
                username=f'pending{i}',
                email=f'pending{i}@test.com',
                password='testpass123',
                est_valide=False,
                is_active=False,
            )

        self.client.login(username='observateur', password='testpass123')
        response = self.client.get(reverse('observations:home'))

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'demande(s) de compte en attente')

    def test_home_page_no_banner_when_no_pending_requests(self):
        """Test que le bandeau n'apparaît pas s'il n'y a pas de demandes"""
        self.client.login(username='admin', password='testpass123')
        response = self.client.get(reverse('observations:home'))

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'demande(s) de compte en attente')

    def test_home_page_context_includes_demandes_count(self):
        """Test que le contexte inclut le compteur de demandes"""
        # Créer 2 demandes en attente
        for i in range(2):
            Utilisateur.objects.create_user(
                username=f'pending{i}',
                email=f'pending{i}@test.com',
                password='testpass123',
                est_valide=False,
                is_active=False,
            )

        self.client.login(username='admin', password='testpass123')
        response = self.client.get(reverse('observations:home'))

        self.assertEqual(response.context['demandes_en_attente'], 2)


@pytest.mark.django_db
class TestListeUtilisateursView(TestCase):
    """Tests pour la liste des utilisateurs avec filtre"""

    def setUp(self):
        """Préparer les données de test"""
        self.client = Client()

        # Créer un administrateur
        self.admin = Utilisateur.objects.create_user(
            username='admin',
            email='admin@test.com',
            password='testpass123',
            role='administrateur',
            est_valide=True,
            is_active=True,
        )

        # Créer des utilisateurs validés
        for i in range(3):
            Utilisateur.objects.create_user(
                username=f'validated{i}',
                email=f'validated{i}@test.com',
                password='testpass123',
                est_valide=True,
                is_active=True,
            )

        # Créer des utilisateurs en attente
        for i in range(2):
            Utilisateur.objects.create_user(
                username=f'pending{i}',
                email=f'pending{i}@test.com',
                password='testpass123',
                est_valide=False,
                is_active=False,
            )

    def test_liste_utilisateurs_filter_pending(self):
        """Test du filtre pour afficher seulement les utilisateurs en attente"""
        self.client.login(username='admin', password='testpass123')
        url = reverse('accounts:liste_utilisateurs') + '?valide=non'
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

        # Devrait afficher seulement les 2 utilisateurs en attente
        utilisateurs = response.context['utilisateurs']
        self.assertEqual(len(utilisateurs), 2)

        # Tous devraient être non validés
        for user in utilisateurs:
            self.assertFalse(user.est_valide)

    def test_liste_utilisateurs_shows_badge_count(self):
        """Test que le badge affiche le bon nombre de demandes"""
        self.client.login(username='admin', password='testpass123')
        response = self.client.get(reverse('accounts:liste_utilisateurs'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['demandes_en_attente'], 2)
        # Vérifier que le badge contient le nombre 2 et le texte "demande(s) en attente"
        self.assertContains(response, 'badge badge-warning')
        self.assertContains(response, '2 demande(s) en attente')
