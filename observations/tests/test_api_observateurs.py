"""Tests pour l'API de gestion des observateurs."""

import pytest
from django.urls import reverse

from accounts.models import Utilisateur
from audit.models import HistoriqueModification
from observations.models import FicheObservation
from observations.views.api_observateurs import calculer_similarite


@pytest.mark.django_db
class TestCalculerSimilarite:
    """Tests pour la fonction de fuzzy matching."""

    def test_noms_identiques(self):
        """Deux noms identiques doivent avoir un score de 1.0."""
        score = calculer_similarite("Jean Dupont", "Jean Dupont")
        assert score == 1.0

    def test_noms_identiques_casse_differente(self):
        """La comparaison doit être insensible à la casse."""
        score = calculer_similarite("Jean Dupont", "JEAN DUPONT")
        assert score == 1.0

    def test_noms_similaires(self):
        """Noms avec une faute de frappe doivent avoir un score > 0.8."""
        score = calculer_similarite("Jean Dupot", "Jean Dupont")
        assert score > 0.8

    def test_noms_differents(self):
        """Noms complètement différents doivent avoir un score faible."""
        score = calculer_similarite("Pierre Martin", "Jean Dupont")
        assert score < 0.5

    def test_chaine_vide(self):
        """Une chaîne vide doit retourner 0.0."""
        assert calculer_similarite("", "Jean") == 0.0
        assert calculer_similarite("Jean", "") == 0.0
        assert calculer_similarite("", "") == 0.0

    def test_none(self):
        """None doit retourner 0.0."""
        assert calculer_similarite(None, "Jean") == 0.0
        assert calculer_similarite("Jean", None) == 0.0


@pytest.fixture
def observateur_transcrit(create_user):
    """Observateur créé par transcription OCR."""
    return create_user(
        username='jean.dupot',
        email='jean.dupot@transcription.trans',
        first_name='Jean',
        last_name='Dupot',
        est_transcription=True,
        est_valide=True,
    )


@pytest.fixture
def observateur_valide(create_user):
    """Observateur validé manuellement."""
    return create_user(
        username='jean.dupont',
        email='jean.dupont@example.com',
        first_name='Jean',
        last_name='Dupont',
        est_transcription=False,
        est_valide=True,
    )


@pytest.fixture
def reviewer_user(create_user):
    """Utilisateur avec rôle reviewer."""
    return create_user(
        username='reviewer',
        email='reviewer@example.com',
        role='reviewer',
        est_valide=True,
    )


@pytest.fixture
def reviewer_client(client, reviewer_user):
    """Client authentifié en tant que reviewer."""
    client.force_login(reviewer_user)
    return client


@pytest.mark.django_db
class TestRechercherObservateursSimilaires:
    """Tests pour l'endpoint de recherche de similarité."""

    def test_suggestions_similarite(self, admin_client, observateur_transcrit, observateur_valide):
        """Doit retourner des suggestions pour un observateur transcrit."""
        url = reverse('observations:api_observateurs_similaires')
        response = admin_client.get(
            url,
            {'observateur_id': observateur_transcrit.id, 'seuil': '0.8'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )

        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert data['observateur_actuel']['est_transcription'] is True
        assert data['observateur_actuel']['nom_complet'] == 'Jean Dupot'
        assert len(data['suggestions']) > 0

        # Vérifier que Jean Dupont est suggéré
        noms_suggeres = [s['nom_complet'] for s in data['suggestions']]
        assert 'Jean Dupont' in noms_suggeres

    def test_requete_non_ajax(self, admin_client, observateur_transcrit):
        """Une requête non-AJAX doit être rejetée."""
        url = reverse('observations:api_observateurs_similaires')
        response = admin_client.get(url, {'observateur_id': observateur_transcrit.id})

        assert response.status_code == 400

    def test_observateur_inexistant(self, admin_client):
        """Un ID d'observateur inexistant doit retourner 404."""
        url = reverse('observations:api_observateurs_similaires')
        response = admin_client.get(
            url,
            {'observateur_id': 99999},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )

        assert response.status_code == 404

    def test_parametre_manquant(self, admin_client):
        """L'absence du paramètre observateur_id doit retourner 400."""
        url = reverse('observations:api_observateurs_similaires')
        response = admin_client.get(
            url,
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )

        assert response.status_code == 400


@pytest.mark.django_db
class TestRechercherObservateurs:
    """Tests pour l'endpoint de recherche par nom."""

    def test_recherche_par_nom(self, admin_client, observateur_valide):
        """Doit retourner les observateurs correspondant au terme de recherche."""
        url = reverse('observations:api_rechercher_observateurs')
        response = admin_client.get(
            url,
            {'q': 'Jean'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data['observateurs']) > 0

    def test_recherche_terme_court(self, admin_client):
        """Un terme de recherche trop court doit retourner une liste vide."""
        url = reverse('observations:api_rechercher_observateurs')
        response = admin_client.get(
            url,
            {'q': 'J'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )

        assert response.status_code == 200
        data = response.json()
        assert data['observateurs'] == []

    def test_requete_non_ajax(self, admin_client):
        """Une requête non-AJAX doit être rejetée."""
        url = reverse('observations:api_rechercher_observateurs')
        response = admin_client.get(url, {'q': 'Jean'})

        assert response.status_code == 400


@pytest.mark.django_db
class TestFusionnerObservateurs:
    """Tests pour l'endpoint de fusion d'observateurs."""

    def test_fusion_permission_admin(
        self, admin_client, observateur_transcrit, observateur_valide, espece
    ):
        """Un admin doit pouvoir fusionner des observateurs."""
        # Créer une fiche pour l'observateur transcrit
        fiche = FicheObservation.objects.create(
            observateur=observateur_transcrit,
            espece=espece,
            annee=2024,
        )

        url = reverse('observations:api_fusionner_observateurs')
        response = admin_client.post(
            url,
            {
                'ancien_observateur_id': observateur_transcrit.id,
                'nouvel_observateur_id': observateur_valide.id,
                'fusionner_toutes': 'true',
            },
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )

        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert data['fiches_transferees'] == 1

        # Vérifier que la fiche a été transférée
        fiche.refresh_from_db()
        assert fiche.observateur == observateur_valide

    def test_fusion_permission_reviewer(
        self, reviewer_client, observateur_transcrit, observateur_valide, espece
    ):
        """Un reviewer doit pouvoir fusionner des observateurs."""
        fiche = FicheObservation.objects.create(
            observateur=observateur_transcrit,
            espece=espece,
            annee=2024,
        )

        url = reverse('observations:api_fusionner_observateurs')
        response = reviewer_client.post(
            url,
            {
                'ancien_observateur_id': observateur_transcrit.id,
                'nouvel_observateur_id': observateur_valide.id,
                'fiche_id': fiche.num_fiche,
                'fusionner_toutes': 'false',
            },
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )

        assert response.status_code == 200

    def test_fusion_permission_refusee_observateur(
        self, authenticated_client, observateur_transcrit, observateur_valide
    ):
        """Un simple observateur ne doit pas pouvoir fusionner."""
        url = reverse('observations:api_fusionner_observateurs')
        response = authenticated_client.post(
            url,
            {
                'ancien_observateur_id': observateur_transcrit.id,
                'nouvel_observateur_id': observateur_valide.id,
                'fusionner_toutes': 'true',
            },
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )

        assert response.status_code == 403

    def test_fusion_meme_observateur(self, admin_client, observateur_transcrit):
        """Fusionner un observateur avec lui-même doit être refusé."""
        url = reverse('observations:api_fusionner_observateurs')
        response = admin_client.post(
            url,
            {
                'ancien_observateur_id': observateur_transcrit.id,
                'nouvel_observateur_id': observateur_transcrit.id,
                'fusionner_toutes': 'true',
            },
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )

        assert response.status_code == 400

    def test_historique_modification_cree(
        self, admin_client, observateur_transcrit, observateur_valide, espece
    ):
        """La fusion doit créer un enregistrement dans l'historique."""
        fiche = FicheObservation.objects.create(
            observateur=observateur_transcrit,
            espece=espece,
            annee=2024,
        )

        url = reverse('observations:api_fusionner_observateurs')
        admin_client.post(
            url,
            {
                'ancien_observateur_id': observateur_transcrit.id,
                'nouvel_observateur_id': observateur_valide.id,
                'fusionner_toutes': 'true',
            },
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )

        # Vérifier que l'historique a été créé
        historique = HistoriqueModification.objects.filter(
            fiche=fiche,
            champ_modifie='observateur',
        )
        assert historique.count() == 1
        assert 'Jean Dupot' in historique.first().ancienne_valeur
        assert 'Jean Dupont' in historique.first().nouvelle_valeur

    def test_ancien_supprime_apres_fusion_complete_si_transcription(
        self, admin_client, observateur_transcrit, observateur_valide, espece
    ):
        """L'ancien observateur OCR doit être SUPPRIMÉ après fusion complète."""
        FicheObservation.objects.create(
            observateur=observateur_transcrit,
            espece=espece,
            annee=2024,
        )

        ancien_id = observateur_transcrit.id

        url = reverse('observations:api_fusionner_observateurs')
        response = admin_client.post(
            url,
            {
                'ancien_observateur_id': observateur_transcrit.id,
                'nouvel_observateur_id': observateur_valide.id,
                'fusionner_toutes': 'true',
            },
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )

        data = response.json()
        assert data['ancien_observateur_supprime'] is True
        assert data['ancien_observateur_desactive'] is False

        # Vérifier que l'observateur n'existe plus dans la base
        assert not Utilisateur.objects.filter(pk=ancien_id).exists()

    def test_ancien_supprime_si_email_observateur_local(
        self, admin_client, observateur_valide, espece, create_user
    ):
        """Un observateur créé via la modale (@observateur.local) doit être SUPPRIMÉ."""
        # Créer un observateur avec email @observateur.local (créé via modale)
        observateur_modale = create_user(
            username='test.correction',
            email='test.correction@observateur.local',
            first_name='Test',
            last_name='Correction',
            est_transcription=False,
            est_valide=True,
        )

        FicheObservation.objects.create(
            observateur=observateur_modale,
            espece=espece,
            annee=2024,
        )

        ancien_id = observateur_modale.id

        url = reverse('observations:api_fusionner_observateurs')
        response = admin_client.post(
            url,
            {
                'ancien_observateur_id': observateur_modale.id,
                'nouvel_observateur_id': observateur_valide.id,
                'fusionner_toutes': 'true',
            },
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )

        data = response.json()
        assert data['ancien_observateur_supprime'] is True

        # Vérifier que l'observateur n'existe plus dans la base
        assert not Utilisateur.objects.filter(pk=ancien_id).exists()

    def test_ancien_desactive_apres_fusion_complete_si_non_transcription(
        self, admin_client, observateur_valide, espece, create_user
    ):
        """Un observateur réel (non-OCR, email normal) doit être DÉSACTIVÉ (pas supprimé)."""
        # Créer un observateur réel (non-transcription, email normal)
        observateur_reel = create_user(
            username='pierre.martin',
            email='pierre.martin@example.com',
            first_name='Pierre',
            last_name='Martin',
            est_transcription=False,
            est_valide=True,
        )

        FicheObservation.objects.create(
            observateur=observateur_reel,
            espece=espece,
            annee=2024,
        )

        url = reverse('observations:api_fusionner_observateurs')
        response = admin_client.post(
            url,
            {
                'ancien_observateur_id': observateur_reel.id,
                'nouvel_observateur_id': observateur_valide.id,
                'fusionner_toutes': 'true',
            },
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )

        data = response.json()
        assert data['ancien_observateur_supprime'] is False
        assert data['ancien_observateur_desactive'] is True

        # Vérifier que l'observateur existe toujours mais est désactivé
        observateur_reel.refresh_from_db()
        assert observateur_reel.is_active is False

    def test_requete_non_ajax(self, admin_client, observateur_transcrit, observateur_valide):
        """Une requête non-AJAX doit être rejetée."""
        url = reverse('observations:api_fusionner_observateurs')
        response = admin_client.post(
            url,
            {
                'ancien_observateur_id': observateur_transcrit.id,
                'nouvel_observateur_id': observateur_valide.id,
                'fusionner_toutes': 'true',
            },
        )

        assert response.status_code == 400


@pytest.mark.django_db
class TestObtenirNomOcrJson:
    """Tests pour l'endpoint de lecture du nom OCR depuis le JSON."""

    def test_fiche_sans_json(self, admin_client, observateur_valide, espece):
        """Une fiche sans chemin JSON doit retourner nom_ocr=null."""
        fiche = FicheObservation.objects.create(
            observateur=observateur_valide,
            espece=espece,
            annee=2024,
            chemin_json='',
        )

        url = reverse('observations:api_nom_ocr_json')
        response = admin_client.get(
            url,
            {'fiche_id': fiche.num_fiche},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )

        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert data['nom_ocr'] is None

    def test_fiche_inexistante(self, admin_client):
        """Une fiche inexistante doit retourner 404."""
        url = reverse('observations:api_nom_ocr_json')
        response = admin_client.get(
            url,
            {'fiche_id': 99999},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )

        assert response.status_code == 404

    def test_parametre_manquant(self, admin_client):
        """L'absence du paramètre fiche_id doit retourner 400."""
        url = reverse('observations:api_nom_ocr_json')
        response = admin_client.get(
            url,
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )

        assert response.status_code == 400

    def test_requete_non_ajax(self, admin_client, observateur_valide, espece):
        """Une requête non-AJAX doit être rejetée."""
        fiche = FicheObservation.objects.create(
            observateur=observateur_valide,
            espece=espece,
            annee=2024,
        )

        url = reverse('observations:api_nom_ocr_json')
        response = admin_client.get(url, {'fiche_id': fiche.num_fiche})

        assert response.status_code == 400


@pytest.mark.django_db
class TestCreerObservateur:
    """Tests pour l'endpoint de création d'observateur."""

    def test_creation_observateur_admin(self, admin_client):
        """Un admin doit pouvoir créer un observateur."""
        url = reverse('observations:api_creer_observateur')
        response = admin_client.post(
            url,
            {'nom': 'Marie Martin'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )

        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert data['observateur']['nom_complet'] == 'Marie Martin'
        assert data['observateur']['est_transcription'] is False

        # Vérifier que l'utilisateur a été créé
        assert Utilisateur.objects.filter(
            first_name='Marie',
            last_name='Martin',
        ).exists()

    def test_creation_observateur_reviewer(self, reviewer_client):
        """Un reviewer doit pouvoir créer un observateur."""
        url = reverse('observations:api_creer_observateur')
        response = reviewer_client.post(
            url,
            {'nom': 'Pierre Durand'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )

        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True

    def test_creation_permission_refusee_observateur(self, authenticated_client):
        """Un simple observateur ne doit pas pouvoir créer."""
        url = reverse('observations:api_creer_observateur')
        response = authenticated_client.post(
            url,
            {'nom': 'Test Test'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )

        assert response.status_code == 403

    def test_creation_nom_trop_court(self, admin_client):
        """Un nom trop court doit être refusé."""
        url = reverse('observations:api_creer_observateur')
        response = admin_client.post(
            url,
            {'nom': 'A'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )

        assert response.status_code == 400
        data = response.json()
        assert data['error'] == 'invalid_name'

    def test_creation_nom_simple(self, admin_client):
        """Un nom sans prénom doit fonctionner."""
        url = reverse('observations:api_creer_observateur')
        response = admin_client.post(
            url,
            {'nom': 'Durand'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )

        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True

        # Vérifier que seul le nom a été défini
        obs = Utilisateur.objects.get(pk=data['observateur']['id'])
        assert obs.last_name == 'Durand'
        assert obs.first_name == ''

    def test_creation_username_unique(self, admin_client):
        """Deux observateurs avec le même nom doivent avoir des usernames différents."""
        url = reverse('observations:api_creer_observateur')

        # Premier observateur
        response1 = admin_client.post(
            url,
            {'nom': 'Jean Test'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )
        assert response1.status_code == 200

        # Second observateur avec le même nom
        response2 = admin_client.post(
            url,
            {'nom': 'Jean Test'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )
        assert response2.status_code == 200

        # Vérifier que les IDs sont différents
        data1 = response1.json()
        data2 = response2.json()
        assert data1['observateur']['id'] != data2['observateur']['id']

    def test_requete_non_ajax(self, admin_client):
        """Une requête non-AJAX doit être rejetée."""
        url = reverse('observations:api_creer_observateur')
        response = admin_client.post(url, {'nom': 'Test Test'})

        assert response.status_code == 400
