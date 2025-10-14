"""
Tests pour l'API de recherche et géocodage des communes

Ces tests vérifient les fonctionnalités critiques qui ont causé une régression :
- Autocomplétion des communes via /geo/rechercher-communes/
- Auto-remplissage des coordonnées GPS et altitude après sélection
"""

from decimal import Decimal

import pytest
from django.urls import reverse

from accounts.models import Utilisateur
from geo.models import CommuneFrance
from observations.models import FicheObservation
from taxonomy.models import Espece, Famille, Ordre


@pytest.fixture
def utilisateur(db):
    """Créer un utilisateur de test"""
    return Utilisateur.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='testpass123',
        first_name='Test',
        last_name='User',
    )


@pytest.fixture
def communes_test(db):
    """Créer des communes de test pour l'autocomplétion"""
    communes = [
        {
            'nom': 'Saint-Denis',
            'departement': 'Seine-Saint-Denis',
            'code_departement': '93',
            'code_postal': '93200',
            'code_insee': '93066',
            'latitude': Decimal('48.936'),
            'longitude': Decimal('2.354'),
            'altitude': 33,
        },
        {
            'nom': 'Saint-Denis-en-Val',
            'departement': 'Loiret',
            'code_departement': '45',
            'code_postal': '45560',
            'code_insee': '45272',
            'latitude': Decimal('47.876'),
            'longitude': Decimal('1.962'),
            'altitude': 105,
        },
        {
            'nom': 'Saint-Ouen',
            'departement': 'Seine-Saint-Denis',
            'code_departement': '93',
            'code_postal': '93400',
            'code_insee': '93070',
            'latitude': Decimal('48.912'),
            'longitude': Decimal('2.334'),
            'altitude': 39,
        },
    ]

    created_communes = []
    for data in communes:
        commune = CommuneFrance.objects.create(**data)
        created_communes.append(commune)

    return created_communes


@pytest.fixture
def fiche_test(db, utilisateur):
    """Créer une fiche d'observation de test"""
    # Créer l'espèce
    ordre = Ordre.objects.create(nom='Passeriformes')
    famille = Famille.objects.create(nom='Turdidae', ordre=ordre)
    espece = Espece.objects.create(
        nom='Merle noir', nom_scientifique='Turdus merula', famille=famille
    )

    # Créer la fiche
    fiche = FicheObservation.objects.create(observateur=utilisateur, espece=espece, annee=2025)

    return fiche


@pytest.mark.django_db
class TestRechercherCommunes:
    """Tests pour l'API de recherche de communes /geo/rechercher-communes/"""

    def test_recherche_commune_simple(self, client, utilisateur, communes_test):
        """Test de recherche basique par nom de commune"""
        client.force_login(utilisateur)

        url = reverse('geo:rechercher_communes')
        response = client.get(url, {'q': 'saint-denis'})

        assert response.status_code == 200
        data = response.json()
        assert 'communes' in data
        assert len(data['communes']) == 2  # Saint-Denis et Saint-Denis-en-Val

        # Vérifier que les données essentielles sont présentes
        for commune in data['communes']:
            assert 'nom' in commune
            assert 'departement' in commune
            assert 'code_departement' in commune
            assert 'code_postal' in commune
            assert 'code_insee' in commune
            assert 'latitude' in commune
            assert 'longitude' in commune
            assert 'altitude' in commune
            assert 'label' in commune

    def test_recherche_commune_precision(self, client, utilisateur, communes_test):
        """Test de recherche avec un terme précis"""
        client.force_login(utilisateur)

        url = reverse('geo:rechercher_communes')
        response = client.get(url, {'q': 'saint-ouen'})

        assert response.status_code == 200
        data = response.json()
        assert len(data['communes']) == 1
        assert data['communes'][0]['nom'] == 'Saint-Ouen'
        assert data['communes'][0]['code_departement'] == '93'

    def test_recherche_commune_trop_courte(self, client, utilisateur, communes_test):
        """Test avec un terme de recherche trop court (< 2 caractères)"""
        client.force_login(utilisateur)

        url = reverse('geo:rechercher_communes')
        response = client.get(url, {'q': 's'})

        assert response.status_code == 200
        data = response.json()
        assert data['communes'] == []

    def test_recherche_sans_parametre(self, client, utilisateur, communes_test):
        """Test sans paramètre de recherche"""
        client.force_login(utilisateur)

        url = reverse('geo:rechercher_communes')
        response = client.get(url)

        assert response.status_code == 200
        data = response.json()
        assert data['communes'] == []

    def test_recherche_avec_distance(self, client, utilisateur, communes_test):
        """Test de recherche avec calcul de distance depuis un point GPS"""
        client.force_login(utilisateur)

        url = reverse('geo:rechercher_communes')
        # Recherche depuis un point proche de Saint-Denis (93)
        response = client.get(
            url,
            {
                'q': 'saint',
                'lat': '48.936',  # Coordonnées de Saint-Denis
                'lon': '2.354',
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data['communes']) > 0

        # Vérifier que les distances sont incluses dans les labels
        for commune in data['communes']:
            if 'Saint-Denis' in commune['nom'] and commune['code_departement'] == '93':
                # La commune exacte devrait avoir une distance très faible
                assert 'm' in commune['label'] or 'km' in commune['label']

    def test_limite_resultats(self, client, utilisateur, communes_test):
        """Test du paramètre limit pour limiter le nombre de résultats"""
        client.force_login(utilisateur)

        url = reverse('geo:rechercher_communes')
        response = client.get(url, {'q': 'saint', 'limit': '1'})

        assert response.status_code == 200
        data = response.json()
        assert len(data['communes']) <= 1

    def test_authentification_requise(self, client, communes_test):
        """Test que l'authentification est requise"""
        url = reverse('geo:rechercher_communes')
        response = client.get(url, {'q': 'saint'})

        # Devrait rediriger vers la page de login
        assert response.status_code == 302


@pytest.mark.django_db
class TestAutoRemplissageGeo:
    """Tests pour vérifier l'auto-remplissage des données géographiques"""

    def test_structure_donnees_complete(self, client, utilisateur, communes_test):
        """Test que toutes les données nécessaires sont retournées pour l'auto-remplissage"""
        client.force_login(utilisateur)

        url = reverse('geo:rechercher_communes')
        response = client.get(url, {'q': 'saint-denis'})

        assert response.status_code == 200
        data = response.json()

        for commune in data['communes']:
            # Vérifier que tous les champs nécessaires pour l'auto-remplissage sont présents
            assert commune['latitude'] is not None
            assert commune['longitude'] is not None
            assert commune['altitude'] is not None
            assert commune['code_insee'] is not None
            assert commune['departement'] is not None

            # Vérifier les types
            assert isinstance(commune['latitude'], str)
            assert isinstance(commune['longitude'], str)
            assert isinstance(commune['altitude'], int | None)

    def test_coordonnees_valides(self, client, utilisateur, communes_test):
        """Test que les coordonnées GPS sont dans des plages valides"""
        client.force_login(utilisateur)

        url = reverse('geo:rechercher_communes')
        response = client.get(url, {'q': 'saint-denis'})

        data = response.json()

        for commune in data['communes']:
            lat = float(commune['latitude'])
            lon = float(commune['longitude'])

            # France métropolitaine : lat entre 41 et 51, lon entre -5 et 10
            assert 41 <= lat <= 51, f"Latitude invalide: {lat}"
            assert -5 <= lon <= 10, f"Longitude invalide: {lon}"


@pytest.mark.django_db
class TestGeocodageManuel:
    """Tests pour le géocodage manuel via /geo/geocoder-commune-manuelle/"""

    def test_geocodage_simple(self, client, utilisateur, fiche_test, communes_test):
        """Test du géocodage manuel d'une commune"""
        client.force_login(utilisateur)

        url = reverse('geo:geocoder_commune')
        response = client.post(
            url,
            {
                'fiche_id': fiche_test.pk,
                'commune': 'Saint-Denis',
                'departement': 'Seine-Saint-Denis',
            },
        )

        assert response.status_code == 200
        data = response.json()

        # Vérifier la réponse
        assert data.get('success') is True
        assert 'coords' in data
        assert 'message' in data

        # Vérifier que la fiche a été mise à jour
        fiche_test.refresh_from_db()
        assert fiche_test.localisation.commune == 'Saint-Denis'
        assert fiche_test.localisation.latitude is not None
        assert fiche_test.localisation.longitude is not None
        assert fiche_test.localisation.source_coordonnees == 'geocodage_manuel'

    def test_geocodage_sans_commune(self, client, utilisateur, fiche_test):
        """Test du géocodage sans nom de commune (devrait échouer)"""
        client.force_login(utilisateur)

        url = reverse('geo:geocoder_commune')
        response = client.post(url, {'fiche_id': fiche_test.pk, 'commune': ''})

        assert response.status_code == 400
        data = response.json()
        assert data.get('success') is False
        assert 'message' in data

    def test_geocodage_fiche_inexistante(self, client, utilisateur):
        """Test du géocodage avec une fiche inexistante"""
        client.force_login(utilisateur)

        url = reverse('geo:geocoder_commune')
        response = client.post(url, {'fiche_id': 99999, 'commune': 'Saint-Denis'})

        assert response.status_code == 404
        data = response.json()
        assert data.get('success') is False


@pytest.mark.django_db
class TestRegressionAutocompletion:
    """Tests spécifiques pour détecter la régression de l'autocomplétion"""

    def test_regression_selection_commune_rempli_champs(self, client, utilisateur, communes_test):
        """
        Test de non-régression : vérifier que la sélection d'une commune
        retourne bien TOUTES les données nécessaires pour remplir les champs

        Régression détectée le 2025-10-10 :
        - L'autocomplétion fonctionnait
        - Mais les champs latitude, longitude, altitude n'étaient pas remplis
        """
        client.force_login(utilisateur)

        url = reverse('geo:rechercher_communes')
        response = client.get(url, {'q': 'saint-denis'})

        assert response.status_code == 200
        data = response.json()
        assert len(data['communes']) > 0

        # CRITIQUE : Vérifier que CHAQUE commune retournée a TOUTES les données
        for commune in data['communes']:
            # Ces champs DOIVENT être présents et non-null pour l'auto-remplissage
            assert 'latitude' in commune, "Champ 'latitude' manquant dans la réponse"
            assert 'longitude' in commune, "Champ 'longitude' manquant dans la réponse"
            assert 'altitude' in commune, "Champ 'altitude' manquant dans la réponse"

            assert commune['latitude'] is not None, "Latitude est None"
            assert commune['longitude'] is not None, "Longitude est None"
            # altitude peut être None pour certaines communes

            # Vérifier que ce sont des valeurs utilisables (pas de string vide)
            assert commune['latitude'] != '', "Latitude est une string vide"
            assert commune['longitude'] != '', "Longitude est une string vide"

            # Vérifier qu'on peut les convertir en float (nécessaire pour le JS)
            try:
                float(commune['latitude'])
                float(commune['longitude'])
            except (ValueError, TypeError) as e:
                pytest.fail(f"Impossible de convertir les coordonnées en float: {e}")
