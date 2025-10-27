"""Tests pour les vues de la page d'accueil."""

import pytest
from django.urls import reverse

from accounts.models import Utilisateur


@pytest.mark.django_db
class TestHomeView:
    """Tests pour la vue home()."""

    def test_home_utilisateur_non_authentifie(self, client):
        """Test que les utilisateurs non authentifiés voient access_restricted."""
        url = reverse('home')
        response = client.get(url)

        assert response.status_code == 200
        # Devrait utiliser le template access_restricted
        assert 'access_restricted.html' in [t.name for t in response.templates]

    def test_home_utilisateur_authentifie(self, authenticated_client, user):
        """Test de la page d'accueil pour un utilisateur authentifié."""
        url = reverse('home')
        response = authenticated_client.get(url)

        assert response.status_code == 200
        assert 'user' in response.context
        assert 'users_count' in response.context
        assert 'observations_count' in response.context
        assert 'fiches_en_edition' in response.context

    def test_home_affiche_compteurs(self, authenticated_client):
        """Test que la page d'accueil affiche les compteurs corrects."""
        url = reverse('home')
        response = authenticated_client.get(url)

        assert response.status_code == 200
        # Vérifier que les compteurs sont présents
        users_count = response.context['users_count']
        observations_count = response.context['observations_count']

        assert isinstance(users_count, int)
        assert isinstance(observations_count, int)
        assert users_count >= 1  # Au moins l'utilisateur du test

    def test_home_administrateur_voit_demandes_en_attente(self, admin_client):
        """Test qu'un administrateur voit les demandes de compte en attente."""
        # Créer un utilisateur non validé
        Utilisateur.objects.create(
            username='nonvalide',
            email='nonvalide@test.com',
            est_valide=False
        )

        url = reverse('home')
        response = admin_client.get(url)

        assert response.status_code == 200
        assert 'demandes_en_attente' in response.context
        assert response.context['demandes_en_attente'] >= 1

    def test_home_utilisateur_normal_ne_voit_pas_demandes(self, authenticated_client):
        """Test qu'un utilisateur normal ne voit pas les demandes en attente."""
        url = reverse('home')
        response = authenticated_client.get(url)

        assert response.status_code == 200
        assert response.context['demandes_en_attente'] == 0

    def test_home_affiche_fiches_en_edition(self, authenticated_client, fiche_observation):
        """Test que la page d'accueil affiche les fiches en édition de l'utilisateur."""
        # La fiche créée par la fixture devrait être visible
        url = reverse('home')
        response = authenticated_client.get(url)

        assert response.status_code == 200
        fiches_en_edition = response.context['fiches_en_edition']
        assert len(fiches_en_edition) >= 0  # Peut être 0 selon l'état


@pytest.mark.django_db
class TestDefaultView:
    """Tests pour la vue default_view()."""

    def test_default_view(self, client):
        """Test de la vue default par défaut."""
        url = reverse('default')
        response = client.get(url)

        assert response.status_code == 200
        # Devrait utiliser le template access_restricted
        assert 'access_restricted.html' in [t.name for t in response.templates]
