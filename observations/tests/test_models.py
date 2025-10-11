"""Tests des modèles du module observations."""
import pytest
from django.core.exceptions import ValidationError
from django.db.utils import IntegrityError
from django.utils import timezone

from observations.models import (
    FicheObservation,
    Observation,
)


@pytest.mark.django_db
class TestFicheObservation:
    """Tests pour le modèle FicheObservation."""

    def test_creation_fiche(self, user, espece):
        """Test de création d'une fiche d'observation."""
        fiche = FicheObservation.objects.create(
            observateur=user, espece=espece, annee=2024, transcription=False
        )

        assert fiche.num_fiche is not None
        assert fiche.observateur == user
        assert fiche.espece == espece
        assert fiche.annee == 2024
        assert fiche.transcription is False

    def test_creation_objets_lies(self, fiche_observation):
        """Test que les objets liés sont créés automatiquement."""
        # Vérifier que save() crée les objets liés
        assert hasattr(fiche_observation, 'localisation')
        assert hasattr(fiche_observation, 'nid')
        assert hasattr(fiche_observation, 'resume')
        assert hasattr(fiche_observation, 'causes_echec')

        # Vérifier les valeurs par défaut
        assert fiche_observation.localisation.commune == 'Non spécifiée'
        assert fiche_observation.nid.hauteur_nid == 0
        assert fiche_observation.resume.nombre_oeufs_pondus is None
        assert fiche_observation.causes_echec.description == 'Aucune cause identifiée'

    def test_str_representation(self, fiche_observation):
        """Test de la représentation string."""
        expected = f"Fiche {fiche_observation.num_fiche} - {fiche_observation.annee} ({fiche_observation.espece.nom})"
        assert str(fiche_observation) == expected


@pytest.mark.django_db
class TestObservation:
    """Tests pour le modèle Observation."""

    def test_creation_observation(self, fiche_observation):
        """Test de création d'une observation."""

        date_obs = timezone.now()
        observation = Observation.objects.create(
            fiche=fiche_observation,
            date_observation=date_obs,
            nombre_oeufs=3,
            nombre_poussins=0,
            observations="Test observation",
        )

        assert observation.fiche == fiche_observation
        assert observation.nombre_oeufs == 3
        assert observation.nombre_poussins == 0

    def test_validation_nombres_negatifs(self, fiche_observation):
        """Test que les nombres négatifs sont rejetés."""

        with pytest.raises(ValidationError):
            obs = Observation(
                fiche=fiche_observation,
                date_observation=timezone.now(),
                nombre_oeufs=-1,
            )
            obs.full_clean()


@pytest.mark.django_db
class TestResumeObservation:
    """Tests pour le modèle ResumeObservation."""

    def test_contrainte_oeufs_eclos_le_pondus(self, fiche_observation):
        """Test que nombre_oeufs_eclos <= nombre_oeufs_pondus."""
        resume = fiche_observation.resume
        resume.nombre_oeufs_pondus = 5
        resume.nombre_oeufs_eclos = 3
        resume.save()  # Devrait passer

        # Test violation de contrainte

        with pytest.raises(IntegrityError):
            resume.nombre_oeufs_eclos = 10
            resume.save()

    def test_contrainte_jour_mois_together(self, fiche_observation):
        """Test que jour et mois sont renseignés ensemble ou pas du tout."""

        resume = fiche_observation.resume

        # Valide: les deux NULL
        resume.premier_oeuf_pondu_jour = None
        resume.premier_oeuf_pondu_mois = None
        resume.save()

        # Valide: les deux renseignés
        resume.premier_oeuf_pondu_jour = 15
        resume.premier_oeuf_pondu_mois = 4
        resume.save()

        # Invalide: jour sans mois
        with pytest.raises(IntegrityError):
            resume.premier_oeuf_pondu_jour = 15
            resume.premier_oeuf_pondu_mois = None
            resume.save()


@pytest.mark.django_db
class TestLocalisation:
    """Tests pour le modèle Localisation."""

    def test_valeurs_par_defaut(self, fiche_observation):
        """Test des valeurs par défaut de localisation."""
        loc = fiche_observation.localisation

        assert loc.commune == 'Non spécifiée'
        assert loc.departement == '00'
        assert loc.altitude == '0'

    def test_mise_a_jour_localisation(self, fiche_observation):
        """Test de mise à jour de la localisation."""
        loc = fiche_observation.localisation
        loc.commune = 'Paris'
        loc.departement = '75'
        loc.altitude = '35'
        loc.save()

        loc.refresh_from_db()
        assert loc.commune == 'Paris'
        assert loc.departement == '75'