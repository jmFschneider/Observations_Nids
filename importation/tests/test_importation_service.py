"""Tests du service d'importation."""
import pytest
from importation.importation_service import ImportationService
from importation.models import EspeceCandidate, ImportationEnCours, TranscriptionBrute


@pytest.mark.django_db
class TestImportationService:
    """Tests du service d'importation."""

    def test_creer_ou_recuperer_utilisateur_nouveau(self):
        """Test de création d'un nouvel utilisateur."""
        service = ImportationService()
        utilisateur = service.creer_ou_recuperer_utilisateur("Jean Dupont")

        assert utilisateur is not None
        assert utilisateur.first_name == "Jean"
        assert utilisateur.last_name == "Dupont"
        assert utilisateur.est_transcription is True
        assert utilisateur.est_valide is True

    def test_creer_ou_recuperer_utilisateur_existant(self):
        """Test de récupération d'un utilisateur existant."""
        service = ImportationService()

        # Créer une première fois
        user1 = service.creer_ou_recuperer_utilisateur("Jean Dupont")

        # Récupérer (ne doit pas créer de doublon)
        user2 = service.creer_ou_recuperer_utilisateur("Jean Dupont")

        assert user1.id == user2.id

    def test_extraire_candidats_espece(self, transcription_brute):
        """Test d'extraction des espèces candidates."""
        service = ImportationService()
        resultats = service.extraire_candidats([transcription_brute])

        assert resultats['especes_ajoutees'] == 1
        assert EspeceCandidate.objects.filter(nom_transcrit="Buse variable").exists()

    def test_extraire_candidats_utilisateur(self, transcription_brute):
        """Test d'extraction des utilisateurs depuis transcription."""
        service = ImportationService()
        resultats = service.extraire_candidats([transcription_brute])

        assert resultats['utilisateurs_crees'] >= 1

        from administration.models import Utilisateur

        assert Utilisateur.objects.filter(
            first_name="Jean", last_name="Dupont", est_transcription=True
        ).exists()

    def test_preparer_importations(self, transcription_brute, espece, espece_candidate):
        """Test de préparation des importations."""
        # Lier l'espèce candidate à une espèce validée
        espece_candidate.espece_validee = espece
        espece_candidate.save()

        service = ImportationService()
        count = service.preparer_importations([transcription_brute])

        assert count == 1
        assert ImportationEnCours.objects.filter(transcription=transcription_brute).exists()


@pytest.mark.django_db
@pytest.mark.integration
class TestWorkflowImportationComplet:
    """Tests du workflow complet d'importation."""

    def test_workflow_complet(self, transcription_brute, espece):
        """Test du workflow complet: extraction -> préparation -> finalisation."""
        service = ImportationService()

        # 1. Extraire les candidats
        resultats_extraction = service.extraire_candidats([transcription_brute])
        assert resultats_extraction['especes_ajoutees'] >= 1

        # 2. Valider l'espèce candidate
        espece_candidate = EspeceCandidate.objects.get(nom_transcrit="Buse variable")
        espece_candidate.espece_validee = espece
        espece_candidate.save()

        # 3. Préparer les importations
        count = service.preparer_importations([transcription_brute])
        assert count == 1

        # 4. Finaliser l'importation
        importation = ImportationEnCours.objects.get(transcription=transcription_brute)
        success, message = service.finaliser_importation(importation.id)

        assert success is True
        assert "créée avec succès" in message

        # Vérifier que la fiche a été créée
        from observations.models import FicheObservation

        assert FicheObservation.objects.filter(transcription=True).exists()

    def test_reinitialiser_importation(self, transcription_brute, espece):
        """Test de réinitialisation d'une importation."""
        service = ImportationService()

        # Créer une importation complète
        service.extraire_candidats([transcription_brute])
        espece_candidate = EspeceCandidate.objects.get(nom_transcrit="Buse variable")
        espece_candidate.espece_validee = espece
        espece_candidate.save()
        service.preparer_importations([transcription_brute])
        importation = ImportationEnCours.objects.get(transcription=transcription_brute)
        service.finaliser_importation(importation.id)

        # Réinitialiser
        result = service.reinitialiser_importation(importation_id=importation.id)

        assert result['success'] is True
        assert not ImportationEnCours.objects.filter(id=importation.id).exists()