"""Tests pour le module d'historique des modifications."""

import pytest
from django.utils import timezone

from audit.models import HistoriqueModification
from observations.models import FicheObservation, Remarque


@pytest.mark.django_db
class TestHistoriqueModification:
    """Tests pour le modèle HistoriqueModification."""

    def test_creation_historique(self, fiche_observation, user):
        """Test de création d'une entrée d'historique."""
        historique = HistoriqueModification.objects.create(
            fiche=fiche_observation,
            champ_modifie='commune',
            ancienne_valeur='Ancienne commune',
            nouvelle_valeur='Nouvelle commune',
            categorie='localisation',
            modifie_par=user
        )

        assert historique.id is not None
        assert historique.fiche == fiche_observation
        assert historique.champ_modifie == 'commune'
        assert historique.categorie == 'localisation'
        assert historique.modifie_par == user
        assert historique.date_modification is not None

    def test_str_representation(self, fiche_observation, user):
        """Test de la représentation string."""
        historique = HistoriqueModification.objects.create(
            fiche=fiche_observation,
            champ_modifie='commune',
            ancienne_valeur='Paris',
            nouvelle_valeur='Lyon',
            categorie='localisation',
            modifie_par=user
        )

        # Le format est: "Modification {champ} ({date}) par {user}"
        expected_prefix = f"Modification commune"
        expected_suffix = f"par {user.username}"
        result = str(historique)

        assert expected_prefix in result
        assert expected_suffix in result

    def test_historique_par_fiche(self, user, espece):
        """Test de récupération de l'historique d'une fiche spécifique."""
        # Créer deux fiches
        fiche1 = FicheObservation.objects.create(
            observateur=user,
            espece=espece,
            annee=2024,
            transcription=False
        )
        fiche2 = FicheObservation.objects.create(
            observateur=user,
            espece=espece,
            annee=2024,
            transcription=False
        )

        # Créer des entrées d'historique pour chaque fiche
        HistoriqueModification.objects.create(
            fiche=fiche1,
            champ_modifie='commune',
            ancienne_valeur='A',
            nouvelle_valeur='B',
            categorie='localisation',
            modifie_par=user
        )
        HistoriqueModification.objects.create(
            fiche=fiche2,
            champ_modifie='commune',
            ancienne_valeur='C',
            nouvelle_valeur='D',
            categorie='localisation',
            modifie_par=user
        )

        # Vérifier que chaque fiche a son propre historique
        historique_fiche1 = HistoriqueModification.objects.filter(fiche=fiche1)
        historique_fiche2 = HistoriqueModification.objects.filter(fiche=fiche2)

        assert historique_fiche1.count() == 1
        assert historique_fiche2.count() == 1
        assert historique_fiche1.first().nouvelle_valeur == 'B'
        assert historique_fiche2.first().nouvelle_valeur == 'D'

    def test_ordre_chronologique_historique(self, fiche_observation, user):
        """Test que l'historique est ordonné par date décroissante."""
        # Créer plusieurs entrées d'historique
        HistoriqueModification.objects.create(
            fiche=fiche_observation,
            champ_modifie='commune',
            ancienne_valeur='A',
            nouvelle_valeur='B',
            categorie='localisation',
            modifie_par=user
        )

        # Attendre un peu
        import time
        time.sleep(0.1)

        HistoriqueModification.objects.create(
            fiche=fiche_observation,
            champ_modifie='departement',
            ancienne_valeur='01',
            nouvelle_valeur='02',
            categorie='localisation',
            modifie_par=user
        )

        # Récupérer l'historique
        historique = HistoriqueModification.objects.filter(
            fiche=fiche_observation
        ).order_by('-date_modification')

        # Vérifier l'ordre
        assert historique.count() == 2
        assert historique.first().champ_modifie == 'departement'  # Plus récent
        assert historique.last().champ_modifie == 'commune'  # Plus ancien


@pytest.mark.django_db
class TestCategories:
    """Tests pour les différentes catégories d'historique."""

    def test_categorie_remarque_valide(self, fiche_observation, user):
        """Test que la catégorie 'remarque' est valide."""
        historique = HistoriqueModification.objects.create(
            fiche=fiche_observation,
            champ_modifie='remarque_ajoutee',
            ancienne_valeur='',
            nouvelle_valeur='Test remarque',
            categorie='remarque',
            modifie_par=user
        )

        assert historique.categorie == 'remarque'

    def test_filtre_par_categorie(self, fiche_observation, user):
        """Test de filtrage de l'historique par catégorie."""
        # Créer des entrées de différentes catégories
        HistoriqueModification.objects.create(
            fiche=fiche_observation,
            champ_modifie='commune',
            ancienne_valeur='A',
            nouvelle_valeur='B',
            categorie='localisation',
            modifie_par=user
        )

        HistoriqueModification.objects.create(
            fiche=fiche_observation,
            champ_modifie='remarque_ajoutee',
            ancienne_valeur='',
            nouvelle_valeur='Test',
            categorie='remarque',
            modifie_par=user
        )

        HistoriqueModification.objects.create(
            fiche=fiche_observation,
            champ_modifie='date_observation',
            ancienne_valeur='2024-01-01',
            nouvelle_valeur='2024-01-02',
            categorie='observation',
            modifie_par=user
        )

        # Filtrer par catégorie
        historique_localisation = HistoriqueModification.objects.filter(
            fiche=fiche_observation,
            categorie='localisation'
        )
        historique_remarques = HistoriqueModification.objects.filter(
            fiche=fiche_observation,
            categorie='remarque'
        )
        historique_observations = HistoriqueModification.objects.filter(
            fiche=fiche_observation,
            categorie='observation'
        )

        assert historique_localisation.count() == 1
        assert historique_remarques.count() == 1
        assert historique_observations.count() == 1


@pytest.mark.django_db
class TestSuppressionEnCascade:
    """Tests pour la suppression en cascade de l'historique."""

    def test_suppression_fiche_supprime_historique(self, fiche_observation, user):
        """Test que la suppression d'une fiche supprime son historique."""
        # Créer des entrées d'historique
        HistoriqueModification.objects.create(
            fiche=fiche_observation,
            champ_modifie='commune',
            ancienne_valeur='A',
            nouvelle_valeur='B',
            categorie='localisation',
            modifie_par=user
        )

        fiche_id = fiche_observation.num_fiche

        # Vérifier que l'historique existe
        assert HistoriqueModification.objects.filter(fiche__num_fiche=fiche_id).exists()

        # Supprimer la fiche
        fiche_observation.delete()

        # Vérifier que l'historique a été supprimé
        assert not HistoriqueModification.objects.filter(fiche__num_fiche=fiche_id).exists()
