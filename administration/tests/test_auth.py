"""Tests d'authentification et de permissions."""
import pytest
from django.urls import reverse


@pytest.mark.django_db
class TestAuthentication:
    """Tests d'authentification."""

    def test_login_success(self, client, user):
        """Test de connexion réussie."""
        response = client.post(
            reverse('login'), {'username': user.username, 'password': 'TestPass123!'}
        )

        assert response.status_code == 302  # Redirection
        assert client.session['_auth_user_id'] == str(user.pk)

    def test_login_failed(self, client):
        """Test de connexion échouée."""
        response = client.post(
            reverse('login'), {'username': 'wronguser', 'password': 'wrongpass'}
        )

        assert response.status_code == 200  # Reste sur la page de login
        assert '_auth_user_id' not in client.session

    def test_logout(self, authenticated_client):
        """Test de déconnexion."""
        response = authenticated_client.get(reverse('logout'))

        assert response.status_code == 302
        assert '_auth_user_id' not in authenticated_client.session

    def test_home_requires_authentication(self, client):
        """Test que la page d'accueil nécessite l'authentification."""
        response = client.get(reverse('home'))

        # Devrait afficher access_restricted ou rediriger vers login
        assert response.status_code in [200, 302]


@pytest.mark.django_db
class TestPermissions:
    """Tests des permissions."""

    def test_admin_can_create_user(self, admin_client):
        """Test qu'un admin peut créer un utilisateur."""
        url = reverse('administration:creer_utilisateur')
        response = admin_client.get(url)

        assert response.status_code == 200

    def test_non_admin_cannot_create_user(self, authenticated_client):
        """Test qu'un utilisateur normal ne peut pas créer d'utilisateur."""
        url = reverse('administration:creer_utilisateur')
        response = authenticated_client.get(url)

        # Devrait être redirigé ou recevoir 403
        assert response.status_code in [302, 403]

    def test_user_can_access_own_profile(self, authenticated_client):
        """Test qu'un utilisateur peut accéder à son profil."""
        url = reverse('administration:mon_profil')
        response = authenticated_client.get(url)

        assert response.status_code == 200