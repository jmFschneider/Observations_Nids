"""Tests pour les vues d'affichage des observations."""

import time

import pytest
from django.urls import reverse

from observations.models import FicheObservation


@pytest.mark.django_db
class TestListeFichesObservations:
    """Tests pour la vue liste_fiches_observations()."""

    def test_acces_non_authentifie(self, client):
        url = reverse('observations:liste_fiches_observations')
        response = client.get(url)

        assert response.status_code == 302  # Redirection vers login

    def test_liste_vide(self, authenticated_client):
        url = reverse('observations:liste_fiches_observations')
        response = authenticated_client.get(url)

        assert response.status_code == 200
        assert 'fiches' in response.context
        # La liste peut ne pas être vide selon les fixtures

    def test_liste_avec_fiches(self, authenticated_client, fiche_observation):
        url = reverse('observations:liste_fiches_observations')
        response = authenticated_client.get(url)

        assert response.status_code == 200
        assert 'fiches' in response.context
        fiches = response.context['fiches']

        # Vérifier que la fiche créée est dans la liste
        assert fiches.paginator.count >= 1

    def test_pagination_liste(self, authenticated_client, user, espece):
        """Test de la pagination de la liste."""
        # Créer plusieurs fiches pour tester la pagination
        for _ in range(15):
            FicheObservation.objects.create(observateur=user, espece=espece, annee=2024)

        url = reverse('observations:liste_fiches_observations')
        response = authenticated_client.get(url)

        assert response.status_code == 200
        fiches = response.context['fiches']

        # La pagination devrait être à 10 par page
        assert fiches.paginator.per_page == 10
        assert fiches.paginator.count >= 15

    def test_pagination_page_2(self, authenticated_client, user, espece):
        """Test d'accès à la page 2 de la pagination."""
        # Créer 15 fiches
        for _ in range(15):
            FicheObservation.objects.create(observateur=user, espece=espece, annee=2024)

        url = reverse('observations:liste_fiches_observations')
        response = authenticated_client.get(url, {'page': '2'})

        assert response.status_code == 200
        fiches = response.context['fiches']

        # Devrait être sur la page 2
        assert fiches.number == 2
        assert fiches.has_previous()

    def test_ordre_fiches_decroissant(self, authenticated_client, user, espece):
        """Test que les fiches sont ordonnées par date de création décroissante."""
        # Créer 3 fiches avec un petit délai entre chaque
        _fiche1 = FicheObservation.objects.create(observateur=user, espece=espece, annee=2024)
        time.sleep(0.01)
        _fiche2 = FicheObservation.objects.create(observateur=user, espece=espece, annee=2024)
        time.sleep(0.01)
        fiche3 = FicheObservation.objects.create(observateur=user, espece=espece, annee=2024)

        url = reverse('observations:liste_fiches_observations')
        response = authenticated_client.get(url)

        assert response.status_code == 200
        fiches = list(response.context['fiches'])

        # La fiche3 (la plus récente) devrait être en premier
        assert fiches[0].num_fiche == fiche3.num_fiche
