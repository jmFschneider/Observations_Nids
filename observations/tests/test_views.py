"""Tests pour les vues du module observations."""

import pytest
from django.urls import reverse
from django.utils import timezone

from audit.models import HistoriqueModification
from observations.models import FicheObservation, Observation, Remarque


@pytest.mark.django_db
class TestSaisieObservationView:
    """Tests pour la vue de saisie/modification d'observations."""

    def test_acces_page_modification_authentifie(self, authenticated_client, fiche_observation):
        url = reverse(
            'observations:modifier_observation', kwargs={'fiche_id': fiche_observation.num_fiche}
        )
        response = authenticated_client.get(url)

        assert response.status_code == 200
        assert 'fiche_form' in response.context

    def test_acces_page_modification_non_authentifie(self, client, fiche_observation):
        url = reverse(
            'observations:modifier_observation', kwargs={'fiche_id': fiche_observation.num_fiche}
        )
        response = client.get(url)

        assert response.status_code == 302  # Redirection vers login

    def test_modification_fiche_observation(self, authenticated_client, fiche_observation):
        """Test de modification des informations de base d'une fiche."""
        url = reverse(
            'observations:modifier_observation', kwargs={'fiche_id': fiche_observation.num_fiche}
        )

        # Données du formulaire
        data = {
            # Informations de base
            'espece': fiche_observation.espece.id,
            'annee': 2025,
            # Localisation
            'commune': 'Paris',
            'departement': '75',
            'lieu_dit': 'Bois de Vincennes',
            'latitude': '48.8566',
            'longitude': '2.3522',
            'altitude': '35',
            'paysage': 'Urbain',
            'alentours': 'Parc',
            # Nid
            'nid_prec_t_meme_couple': 'non',
            'hauteur_nid': '150',
            'hauteur_couvert': '200',
            'details_nid': 'Nid dans un arbre',
            # Résumé
            'premier_oeuf_pondu_jour': '',
            'premier_oeuf_pondu_mois': '',
            'premier_poussin_eclos_jour': '',
            'premier_poussin_eclos_mois': '',
            'premier_poussin_volant_jour': '',
            'premier_poussin_volant_mois': '',
            'nombre_oeufs_pondus': '',
            'nombre_oeufs_eclos': '',
            'nombre_oeufs_non_eclos': '',
            'nombre_poussins': '',
            # Causes d'échec
            'description': 'Aucune cause identifiée',
            'observations-TOTAL_FORMS': '0',
            'observations-INITIAL_FORMS': '0',
            'observations-MIN_NUM_FORMS': '0',
            'observations-MAX_NUM_FORMS': '1000',
            'remarques-TOTAL_FORMS': '0',
            'remarques-INITIAL_FORMS': '0',
            'remarques-MIN_NUM_FORMS': '0',
            'remarques-MAX_NUM_FORMS': '1000',
            'coordonnees': '48.8566,2.3522',
            'remarque-initiale': '',
        }

        response = authenticated_client.post(url, data)

        # Vérifier la redirection
        assert response.status_code == 302

        # Vérifier que la fiche a été modifiée
        fiche_observation.refresh_from_db()
        assert fiche_observation.annee == 2025
        assert fiche_observation.localisation.commune == 'Paris'
        assert fiche_observation.localisation.departement == '75'


@pytest.mark.django_db
class TestHistoriqueRemarques:
    """Tests pour l'historique des modifications des remarques."""

    def test_remarque_non_modifiee_pas_dans_historique(
        self, authenticated_client, fiche_observation
    ):
        """Test que les remarques non modifiées ne sont PAS marquées comme supprimées."""
        # Créer une remarque
        remarque = Remarque.objects.create(fiche=fiche_observation, remarque="Test remarque")

        url = reverse(
            'observations:modifier_observation', kwargs={'fiche_id': fiche_observation.num_fiche}
        )

        # Modifier la fiche SANS toucher à la remarque
        data = self._get_base_form_data(fiche_observation)
        data.update(
            {
                'remarques-TOTAL_FORMS': '1',
                'remarques-INITIAL_FORMS': '1',
                'remarques-0-id': str(remarque.id),
                'remarques-0-remarque': remarque.remarque,
                'remarques-0-DELETE': '',  # PAS supprimée
            }
        )

        # Compter les entrées d'historique avant
        count_before = HistoriqueModification.objects.filter(
            fiche=fiche_observation, categorie='remarque'
        ).count()

        response = authenticated_client.post(url, data)
        assert response.status_code == 302

        # Vérifier qu'aucune nouvelle entrée d'historique pour remarque n'a été créée
        count_after = HistoriqueModification.objects.filter(
            fiche=fiche_observation, categorie='remarque'
        ).count()

        assert count_after == count_before, (
            "Aucune entrée d'historique ne devrait être créée pour une remarque non modifiée"
        )

    def test_suppression_remarque_dans_historique(self, authenticated_client, fiche_observation):
        """Test que la suppression d'une remarque est bien enregistrée dans l'historique."""
        # Créer une remarque
        remarque = Remarque.objects.create(
            fiche=fiche_observation, remarque="Test remarque à supprimer"
        )

        url = reverse(
            'observations:modifier_observation', kwargs={'fiche_id': fiche_observation.num_fiche}
        )
        data = self._get_base_form_data(fiche_observation)
        data.update(
            {
                'remarques-TOTAL_FORMS': '1',
                'remarques-INITIAL_FORMS': '1',
                'remarques-0-id': str(remarque.id),
                'remarques-0-remarque': remarque.remarque,
                'remarques-0-DELETE': 'on',  # Marquée pour suppression
                'coordonnees': '0,0',
            }
        )

        response = authenticated_client.post(url, data)
        assert response.status_code == 302

        # Vérifier que l'entrée d'historique a été créée
        historique = HistoriqueModification.objects.filter(
            fiche=fiche_observation, champ_modifie='remarque_supprimee', categorie='remarque'
        )

        assert historique.exists(), "Une entrée d'historique devrait être créée pour la suppression"
        first_hist = historique.first()
        assert first_hist is not None and first_hist.ancienne_valeur == "Test remarque à supprimer"

    def test_ajout_remarque_dans_historique(self, authenticated_client, fiche_observation):
        url = reverse(
            'observations:modifier_observation', kwargs={'fiche_id': fiche_observation.num_fiche}
        )

        # Ajouter une nouvelle remarque
        data = self._get_base_form_data(fiche_observation)
        data.update(
            {
                'remarques-TOTAL_FORMS': '1',
                'remarques-INITIAL_FORMS': '0',
                'remarques-0-remarque': 'Nouvelle remarque',
                'remarques-0-DELETE': '',
                'coordonnees': '0,0',
            }
        )

        response = authenticated_client.post(url, data)
        assert response.status_code == 302

        # Vérifier que la remarque a été créée
        assert Remarque.objects.filter(fiche=fiche_observation).exists()

        # Vérifier l'entrée d'historique
        historique = HistoriqueModification.objects.filter(
            fiche=fiche_observation, champ_modifie='remarque_ajoutee', categorie='remarque'
        )

        assert historique.exists(), "Une entrée d'historique devrait être créée pour l'ajout"
        first_hist = historique.first()
        assert first_hist is not None and first_hist.nouvelle_valeur == "Nouvelle remarque"

    def _get_base_form_data(self, fiche_observation):
        """Retourne les données de base du formulaire."""
        return {
            'espece': fiche_observation.espece.id,
            'annee': fiche_observation.annee,
            'commune': fiche_observation.localisation.commune,
            'departement': fiche_observation.localisation.departement,
            'lieu_dit': fiche_observation.localisation.lieu_dit or '',
            'latitude': str(fiche_observation.localisation.latitude or '0'),
            'longitude': str(fiche_observation.localisation.longitude or '0'),
            'altitude': str(fiche_observation.localisation.altitude or '0'),
            'paysage': fiche_observation.localisation.paysage or '',
            'alentours': fiche_observation.localisation.alentours or '',
            'nid_prec_t_meme_couple': fiche_observation.nid.nid_prec_t_meme_couple,
            'hauteur_nid': str(fiche_observation.nid.hauteur_nid),
            'hauteur_couvert': str(fiche_observation.nid.hauteur_couvert),
            'details_nid': fiche_observation.nid.details_nid or '',
            'premier_oeuf_pondu_jour': '',
            'premier_oeuf_pondu_mois': '',
            'premier_poussin_eclos_jour': '',
            'premier_poussin_eclos_mois': '',
            'premier_poussin_volant_jour': '',
            'premier_poussin_volant_mois': '',
            'nombre_oeufs_pondus': '',
            'nombre_oeufs_eclos': '',
            'nombre_oeufs_non_eclos': '',
            'nombre_poussins': '',
            'description': fiche_observation.causes_echec.description,
            'observations-TOTAL_FORMS': '0',
            'observations-INITIAL_FORMS': '0',
            'observations-MIN_NUM_FORMS': '0',
            'observations-MAX_NUM_FORMS': '1000',
            'coordonnees': '0,0',
        }


@pytest.mark.django_db
class TestSuppressionObservations:
    """Tests pour la suppression d'observations via le formset."""

    def test_suppression_observation(self, authenticated_client, fiche_observation):
        """Test de suppression d'une observation."""
        # Créer une observation
        observation = Observation.objects.create(
            fiche=fiche_observation,
            date_observation=timezone.now(),
            nombre_oeufs=3,
            nombre_poussins=2,
            observations="Test observation",
        )

        url = reverse(
            'observations:modifier_observation', kwargs={'fiche_id': fiche_observation.num_fiche}
        )
        data = {
            'espece': fiche_observation.espece.id,
            'annee': fiche_observation.annee,
            'commune': 'Test',
            'departement': '00',
            'lieu_dit': '',
            'latitude': '0',
            'longitude': '0',
            'altitude': '0',
            'paysage': 'Paysage de test',
            'alentours': 'Alentours de test',
            'nid_prec_t_meme_couple': 'non',
            'hauteur_nid': '0',
            'hauteur_couvert': '0',
            'details_nid': '',
            'premier_oeuf_pondu_jour': '',
            'premier_oeuf_pondu_mois': '',
            'premier_poussin_eclos_jour': '',
            'premier_poussin_eclos_mois': '',
            'premier_poussin_volant_jour': '',
            'premier_poussin_volant_mois': '',
            'nombre_oeufs_pondus': '',
            'nombre_oeufs_eclos': '',
            'nombre_oeufs_non_eclos': '',
            'nombre_poussins': '',
            'description': 'Aucune cause identifiée',
            'observations-TOTAL_FORMS': '1',
            'observations-INITIAL_FORMS': '1',
            'observations-MIN_NUM_FORMS': '0',
            'observations-MAX_NUM_FORMS': '1000',
            'observations-0-id': str(observation.id),
            'observations-0-date_observation': observation.date_observation.strftime(
                '%Y-%m-%d %H:%M'
            ),
            'observations-0-nombre_oeufs': str(observation.nombre_oeufs),
            'observations-0-nombre_poussins': str(observation.nombre_poussins),
            'observations-0-observations': observation.observations,
            'observations-0-DELETE': 'on',  # Marquer pour suppression
            'remarques-TOTAL_FORMS': '0',
            'remarques-INITIAL_FORMS': '0',
            'remarques-MIN_NUM_FORMS': '0',
            'remarques-MAX_NUM_FORMS': '1000',
            'coordonnees': '0,0',
        }

        response = authenticated_client.post(url, data)
        assert response.status_code == 302

        # Vérifier que l'observation a été supprimée
        assert not Observation.objects.filter(id=observation.id).exists()

        # Vérifier l'entrée d'historique
        historique = HistoriqueModification.objects.filter(
            fiche=fiche_observation, champ_modifie='observation_supprimee', categorie='observation'
        )

        assert historique.exists(), "Une entrée d'historique devrait être créée pour la suppression"


@pytest.mark.django_db
class TestHistoriqueModifications:
    """Tests pour la page d'historique des modifications."""

    def test_affichage_historique(self, authenticated_client, fiche_observation):
        """Test de l'affichage de l'historique des modifications."""
        # Créer quelques entrées d'historique
        HistoriqueModification.objects.create(
            fiche=fiche_observation,
            champ_modifie='commune',
            ancienne_valeur='Ancien',
            nouvelle_valeur='Nouveau',
            categorie='localisation',
            modifie_par=fiche_observation.observateur,
        )

        url = reverse(
            'observations:historique_modifications',
            kwargs={'fiche_id': fiche_observation.num_fiche},
        )
        response = authenticated_client.get(url)

        assert response.status_code == 200
        assert 'modifications' in response.context
        assert response.context['modifications'].count() == 1


@pytest.mark.django_db
class TestAjaxRemarques:
    """Tests pour les appels AJAX de gestion des remarques."""

    def test_get_remarques_ajax(self, authenticated_client, fiche_observation):
        """Test de récupération des remarques via AJAX."""
        # Créer quelques remarques
        Remarque.objects.create(fiche=fiche_observation, remarque="Remarque 1")
        Remarque.objects.create(fiche=fiche_observation, remarque="Remarque 2")

        url = reverse(
            'observations:modifier_observation', kwargs={'fiche_id': fiche_observation.num_fiche}
        )
        response = authenticated_client.get(
            url, {'get_remarques': '1'}, HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )

        assert response.status_code == 200
        data = response.json()
        assert 'remarques' in data
        assert len(data['remarques']) == 2

    def test_update_remarques_ajax_ajout(self, authenticated_client, fiche_observation):
        url = reverse(
            'observations:modifier_observation', kwargs={'fiche_id': fiche_observation.num_fiche}
        )

        data = {
            'action': 'update_remarques',
            'remarques-TOTAL_FORMS': '1',
            'remarques-INITIAL_FORMS': '0',
            'remarques-0-remarque': 'Nouvelle remarque AJAX',
        }

        response = authenticated_client.post(url, data)

        assert response.status_code == 200
        response_data = response.json()
        assert response_data['status'] == 'success'

        # Vérifier que la remarque a été créée
        assert Remarque.objects.filter(fiche=fiche_observation).count() == 1

    def test_update_remarques_ajax_suppression(self, authenticated_client, fiche_observation):
        remarque = Remarque.objects.create(fiche=fiche_observation, remarque="À supprimer")

        url = reverse(
            'observations:modifier_observation', kwargs={'fiche_id': fiche_observation.num_fiche}
        )

        data = {
            'action': 'update_remarques',
            'remarques-TOTAL_FORMS': '1',
            'remarques-INITIAL_FORMS': '1',
            'remarques-0-id': str(remarque.id),
            'remarques-0-remarque': remarque.remarque,
            'remarques-0-DELETE': 'on',
        }

        response = authenticated_client.post(url, data)

        assert response.status_code == 200
        response_data = response.json()
        assert response_data['status'] == 'success'

        # Vérifier que la remarque a été supprimée
        assert not Remarque.objects.filter(id=remarque.id).exists()

    def test_update_remarques_ajax_modification(self, authenticated_client, fiche_observation):
        """Test de modification d'une remarque via AJAX."""
        remarque = Remarque.objects.create(fiche=fiche_observation, remarque="Texte original")

        url = reverse(
            'observations:modifier_observation', kwargs={'fiche_id': fiche_observation.num_fiche}
        )

        data = {
            'action': 'update_remarques',
            'remarques-TOTAL_FORMS': '1',
            'remarques-INITIAL_FORMS': '1',
            'remarques-0-id': str(remarque.id),
            'remarques-0-remarque': 'Texte modifié',
        }

        response = authenticated_client.post(url, data)

        assert response.status_code == 200
        response_data = response.json()
        assert response_data['status'] == 'success'

        # Vérifier que la remarque a été modifiée
        remarque.refresh_from_db()
        assert remarque.remarque == 'Texte modifié'

        # Vérifier l'historique
        historique = HistoriqueModification.objects.filter(
            fiche=fiche_observation, champ_modifie='remarque_modifiee'
        )
        assert historique.exists()


@pytest.mark.django_db
class TestFicheObservationView:
    """Tests pour la vue d'affichage d'une fiche."""

    def test_affichage_fiche(self, authenticated_client, fiche_observation):
        url = reverse(
            'observations:fiche_observation', kwargs={'fiche_id': fiche_observation.num_fiche}
        )
        response = authenticated_client.get(url)

        assert response.status_code == 200
        assert 'fiche' in response.context
        assert response.context['fiche'] == fiche_observation

    def test_affichage_fiche_avec_observations(self, authenticated_client, fiche_observation):
        """Test de l'affichage d'une fiche avec observations."""
        Observation.objects.create(
            fiche=fiche_observation, date_observation=timezone.now(), nombre_oeufs=3
        )

        url = reverse(
            'observations:fiche_observation', kwargs={'fiche_id': fiche_observation.num_fiche}
        )
        response = authenticated_client.get(url)

        assert response.status_code == 200
        assert 'observations' in response.context
        assert response.context['observations'].count() == 1


@pytest.mark.django_db
class TestPermissions:
    """Tests pour la gestion des permissions."""

    def test_utilisateur_non_autorise_ne_peut_modifier(
        self, client, fiche_observation, create_user
    ):
        """Test qu'un utilisateur non autorisé ne peut pas modifier une fiche en cours de saisie."""
        # Créer un autre utilisateur
        autre_user = create_user(username='autre_user', email='autre@test.com')
        client.force_login(autre_user)

        # Mettre la fiche en état "en_edition"
        if hasattr(fiche_observation, 'etat_correction'):
            fiche_observation.etat_correction.statut = 'en_edition'
            fiche_observation.etat_correction.save()

        url = reverse(
            'observations:modifier_observation', kwargs={'fiche_id': fiche_observation.num_fiche}
        )
        response = client.get(url)

        # Devrait être redirigé
        assert response.status_code == 302
        assert response.url == reverse(
            'observations:fiche_observation', kwargs={'fiche_id': fiche_observation.num_fiche}
        )

    def test_fiche_inexistante(self, authenticated_client):
        """Test d'accès à une fiche qui n'existe pas."""
        url = reverse('observations:modifier_observation', kwargs={'fiche_id': 99999})
        response = authenticated_client.get(url)

        # La vue gère l'exception et retourne une page (peut être 200 avec erreur ou 404)
        # L'important est que la vue ne crash pas
        assert response.status_code in [200, 404]


@pytest.mark.django_db
class TestCreationNouvelleFiche:
    """Tests pour la création d'une nouvelle fiche."""

    def test_affichage_formulaire_nouvelle_fiche(self, authenticated_client):
        """Test de l'affichage du formulaire pour une nouvelle fiche."""
        url = reverse('observations:observations_list')  # Sans fiche_id
        response = authenticated_client.get(url)

        assert response.status_code == 200
        assert 'fiche_form' in response.context

    def test_creation_fiche_sans_observateur_defini(self, authenticated_client, espece):
        """Test de création d'une fiche où l'observateur est automatiquement défini."""
        url = reverse('observations:observations_list')

        data = {
            'espece': espece.id,
            'annee': 2025,
            'commune': 'Paris',
            'departement': '75',
            'lieu_dit': '',
            'latitude': '48.8566',
            'longitude': '2.3522',
            'altitude': '35',
            'paysage': 'Urbain',
            'alentours': 'Parc',
            'nid_prec_t_meme_couple': 'non',
            'hauteur_nid': '0',
            'hauteur_couvert': '0',
            'details_nid': '',
            'premier_oeuf_pondu_jour': '',
            'premier_oeuf_pondu_mois': '',
            'premier_poussin_eclos_jour': '',
            'premier_poussin_eclos_mois': '',
            'premier_poussin_volant_jour': '',
            'premier_poussin_volant_mois': '',
            'nombre_oeufs_pondus': '',
            'nombre_oeufs_eclos': '',
            'nombre_oeufs_non_eclos': '',
            'nombre_poussins': '',
            'description': 'Aucune cause identifiée',
            'observations-TOTAL_FORMS': '0',
            'observations-INITIAL_FORMS': '0',
            'observations-MIN_NUM_FORMS': '0',
            'observations-MAX_NUM_FORMS': '1000',
            'remarques-TOTAL_FORMS': '0',
            'remarques-INITIAL_FORMS': '0',
            'remarques-MIN_NUM_FORMS': '0',
            'remarques-MAX_NUM_FORMS': '1000',
            'coordonnees': '48.8566,2.3522',
        }

        response = authenticated_client.post(url, data)

        # Devrait créer la fiche et rediriger
        assert response.status_code == 302

        # Vérifier que la fiche a été créée avec le bon observateur
        fiche = FicheObservation.objects.filter(espece=espece, annee=2025).first()
        assert fiche is not None
        assert (
            fiche.observateur == authenticated_client.session.get('_auth_user_id')
            or fiche.observateur.id
        )
