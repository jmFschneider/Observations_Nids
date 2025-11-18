"""
Tests pour les vues d'administration des communes (geo/views_admin.py).
"""

import pytest
from django.contrib.messages import get_messages
from django.urls import reverse

from accounts.models import Utilisateur
from geo.models import AncienneCommune, CommuneFrance


@pytest.fixture
def admin_user(db):
    """Utilisateur administrateur pour les tests."""
    return Utilisateur.objects.create_user(
        username='admin_test',
        email='admin@test.com',
        password='testpass123',
        first_name='Admin',
        last_name='Test',
        role='administrateur',
        is_staff=True,
        is_active=True,
    )


@pytest.fixture
def normal_user(db):
    """Utilisateur normal (non-admin) pour les tests de permissions."""
    return Utilisateur.objects.create_user(
        username='user_test',
        email='user@test.com',
        password='testpass123',
        first_name='User',
        last_name='Test',
        role='observateur',
        is_staff=False,
        is_active=True,
    )


@pytest.fixture
def commune_test(admin_user):
    """Commune de test."""
    return CommuneFrance.objects.create(
        nom='TestVille',
        code_insee='99001',
        code_postal='75001',
        departement='Paris',
        code_departement='75',
        region='Île-de-France',
        latitude=48.8566,
        longitude=2.3522,
        altitude=35,
        source_ajout='manuel',
        ajoutee_par=admin_user,
    )


@pytest.fixture
def ancienne_commune(commune_test):
    """Ancienne commune fusionnée."""
    return AncienneCommune.objects.create(
        nom='AncienneTestVille',
        code_insee='99002',
        commune_actuelle=commune_test,
        date_fusion='2024-01-01',
    )


@pytest.mark.django_db
class TestListeCommunes:
    """Tests pour la vue liste_communes."""

    def test_acces_admin_autorise(self, client, admin_user):
        """Un admin peut accéder à la liste des communes."""
        client.force_login(admin_user)
        response = client.get(reverse('geo:liste_communes'))
        assert response.status_code == 200
        assert 'page_obj' in response.context

    def test_acces_non_admin_refuse(self, client, normal_user):
        """Un utilisateur non-admin ne peut pas accéder à la liste."""
        client.force_login(normal_user)
        response = client.get(reverse('geo:liste_communes'))
        assert response.status_code == 302  # Redirection

    def test_acces_non_authentifie_refuse(self, client):
        """Un utilisateur non authentifié ne peut pas accéder."""
        response = client.get(reverse('geo:liste_communes'))
        assert response.status_code == 302  # Redirection vers login

    def test_affichage_communes(self, client, admin_user, commune_test):
        """La liste affiche correctement les communes."""
        client.force_login(admin_user)
        response = client.get(reverse('geo:liste_communes'))
        assert response.status_code == 200
        assert commune_test.nom in str(response.content)

    def test_recherche_par_nom(self, client, admin_user, commune_test):
        """La recherche par nom fonctionne."""
        client.force_login(admin_user)
        response = client.get(reverse('geo:liste_communes'), {'q': 'TestVille'})
        assert response.status_code == 200
        assert commune_test.nom in str(response.content)

    def test_recherche_ancienne_commune(self, client, admin_user, commune_test, ancienne_commune):
        """La recherche trouve les communes actuelles liées aux anciennes."""
        client.force_login(admin_user)
        response = client.get(reverse('geo:liste_communes'), {'q': 'AncienneTestVille'})
        assert response.status_code == 200
        # La commune actuelle devrait apparaître dans les résultats
        assert commune_test.nom in str(response.content)

    def test_filtre_par_departement(self, client, admin_user, commune_test):
        """Le filtre par département fonctionne."""
        client.force_login(admin_user)
        response = client.get(reverse('geo:liste_communes'), {'departement': '75'})
        assert response.status_code == 200
        assert commune_test.nom in str(response.content)

    def test_filtre_par_region(self, client, admin_user, commune_test):
        """Le filtre par région fonctionne."""
        client.force_login(admin_user)
        response = client.get(reverse('geo:liste_communes'), {'region': 'Île-de-France'})
        assert response.status_code == 200
        assert commune_test.nom in str(response.content)

    def test_filtre_par_source(self, client, admin_user, commune_test):
        """Le filtre par source fonctionne."""
        client.force_login(admin_user)
        response = client.get(reverse('geo:liste_communes'), {'source': 'manuel'})
        assert response.status_code == 200
        assert commune_test.nom in str(response.content)

    def test_statistiques_affichees(self, client, admin_user, commune_test):
        """Les statistiques sont correctement affichées."""
        client.force_login(admin_user)
        response = client.get(reverse('geo:liste_communes'))
        assert response.status_code == 200
        stats = response.context['stats']
        assert stats['total'] >= 1
        assert 'source_manuelle' in stats  # Correction: source_manuelle au lieu de source_manuel

    def test_pagination(self, client, admin_user):
        """La pagination fonctionne."""
        # Créer 60 communes pour tester la pagination (50 par page)
        for i in range(60):
            CommuneFrance.objects.create(
                nom=f'Commune{i:02d}',
                code_insee=f'99{i:03d}',
                code_postal='00000',
                latitude=48.0,
                longitude=2.0,
                source_ajout='manuel',
                ajoutee_par=admin_user,
            )

        client.force_login(admin_user)
        response = client.get(reverse('geo:liste_communes'))
        assert response.status_code == 200
        assert response.context['page_obj'].paginator.num_pages >= 2


@pytest.mark.django_db
class TestDetailCommune:
    """Tests pour la vue detail_commune."""

    def test_affichage_detail(self, client, admin_user, commune_test):
        """Le détail d'une commune s'affiche correctement."""
        client.force_login(admin_user)
        response = client.get(reverse('geo:detail_commune', args=[commune_test.id]))
        assert response.status_code == 200
        assert response.context['commune'] == commune_test
        assert 'nombre_fiches' in response.context

    def test_affichage_anciennes_communes(self, client, admin_user, commune_test, ancienne_commune):
        """Les anciennes communes liées sont affichées."""
        client.force_login(admin_user)
        response = client.get(reverse('geo:detail_commune', args=[commune_test.id]))
        assert response.status_code == 200
        assert ancienne_commune in response.context['anciennes_communes']

    def test_commune_inexistante(self, client, admin_user):
        """Erreur 404 si la commune n'existe pas."""
        client.force_login(admin_user)
        response = client.get(reverse('geo:detail_commune', args=[99999]))
        assert response.status_code == 404

    def test_acces_non_admin_refuse(self, client, normal_user, commune_test):
        """Un non-admin ne peut pas voir le détail."""
        client.force_login(normal_user)
        response = client.get(reverse('geo:detail_commune', args=[commune_test.id]))
        assert response.status_code == 302


@pytest.mark.django_db
class TestCreerCommune:
    """Tests pour la vue creer_commune."""

    def test_affichage_formulaire(self, client, admin_user):
        """Le formulaire de création s'affiche."""
        client.force_login(admin_user)
        response = client.get(reverse('geo:creer_commune'))
        assert response.status_code == 200

    def test_creation_commune_valide(self, client, admin_user):
        """Une commune valide peut être créée."""
        client.force_login(admin_user)
        data = {
            'nom': 'NouvelleCommune',
            'code_insee': '99999',
            'code_postal': '75002',
            'departement': 'Paris',
            'code_departement': '75',
            'region': 'Île-de-France',
            'latitude': '48.8566',
            'longitude': '2.3522',
            'altitude': '35',
            'autres_noms': 'Alias1, Alias2',
            'commentaire': 'Test de création',
        }
        response = client.post(reverse('geo:creer_commune'), data)
        assert response.status_code == 302  # Redirection après succès
        assert CommuneFrance.objects.filter(code_insee='99999').exists()

        # Vérifier le message de succès
        messages = list(get_messages(response.wsgi_request))
        assert any('créée avec succès' in str(m) for m in messages)

    def test_creation_avec_virgule_coordonnees(self, client, admin_user):
        """Les coordonnées avec virgules sont correctement converties."""
        client.force_login(admin_user)
        data = {
            'nom': 'CommuneVirgule',
            'code_insee': '99998',
            'latitude': '48,8566',  # Virgule au lieu de point
            'longitude': '2,3522',
            'altitude': '35,5',
        }
        response = client.post(reverse('geo:creer_commune'), data)
        commune = CommuneFrance.objects.get(code_insee='99998')
        # Comparaison avec Decimal car latitude/longitude sont des DecimalField
        assert float(commune.latitude) == 48.8566
        assert float(commune.longitude) == 2.3522
        assert commune.altitude == 35

    def test_creation_sans_nom_refuse(self, client, admin_user):
        """Une commune sans nom est refusée."""
        client.force_login(admin_user)
        data = {
            'nom': '',
            'code_insee': '99997',
            'latitude': '48.8566',
            'longitude': '2.3522',
        }
        response = client.post(reverse('geo:creer_commune'), data)
        assert not CommuneFrance.objects.filter(code_insee='99997').exists()
        messages = list(get_messages(response.wsgi_request))
        assert any('obligatoires' in str(m) for m in messages)

    def test_creation_sans_coordonnees_refuse(self, client, admin_user):
        """Une commune sans coordonnées est refusée."""
        client.force_login(admin_user)
        data = {
            'nom': 'CommuneSansCoord',
            'code_insee': '99996',
            'latitude': '',
            'longitude': '',
        }
        response = client.post(reverse('geo:creer_commune'), data)
        assert not CommuneFrance.objects.filter(code_insee='99996').exists()

    def test_creation_code_insee_duplique_refuse(self, client, admin_user, commune_test):
        """Un code INSEE en double est refusé."""
        client.force_login(admin_user)
        data = {
            'nom': 'Doublon',
            'code_insee': commune_test.code_insee,  # Même code INSEE
            'latitude': '48.8566',
            'longitude': '2.3522',
        }
        response = client.post(reverse('geo:creer_commune'), data)
        # Ne doit créer qu'une seule commune
        assert CommuneFrance.objects.filter(code_insee=commune_test.code_insee).count() == 1
        messages = list(get_messages(response.wsgi_request))
        assert any('existe déjà' in str(m) for m in messages)


@pytest.mark.django_db
class TestModifierCommune:
    """Tests pour la vue modifier_commune."""

    def test_affichage_formulaire(self, client, admin_user, commune_test):
        """Le formulaire de modification s'affiche."""
        client.force_login(admin_user)
        response = client.get(reverse('geo:modifier_commune', args=[commune_test.id]))
        assert response.status_code == 200
        assert response.context['commune'] == commune_test

    def test_modification_commune_valide(self, client, admin_user, commune_test):
        """Une commune peut être modifiée."""
        client.force_login(admin_user)
        data = {
            'nom': 'NomModifie',
            'code_insee': commune_test.code_insee,
            'code_postal': '75003',
            'departement': 'Paris Modifié',
            'code_departement': '75',
            'region': 'Île-de-France',
            'latitude': '48.9000',
            'longitude': '2.4000',
            'altitude': '40',
            'autres_noms': 'Nouveau alias',
            'commentaire': 'Modifié',
        }
        response = client.post(reverse('geo:modifier_commune', args=[commune_test.id]), data)
        assert response.status_code == 302

        commune_test.refresh_from_db()
        assert commune_test.nom == 'NomModifie'
        assert float(commune_test.latitude) == 48.9000  # Conversion en float
        assert commune_test.code_postal == '75003'

    def test_modification_code_insee_duplique_refuse(self, client, admin_user):
        """Impossible de modifier avec un code INSEE déjà existant."""
        # Créer deux communes
        commune1 = CommuneFrance.objects.create(
            nom='Commune1',
            code_insee='99111',
            latitude=48.0,
            longitude=2.0,
            source_ajout='manuel',
            ajoutee_par=admin_user,
        )
        commune2 = CommuneFrance.objects.create(
            nom='Commune2',
            code_insee='99222',
            latitude=48.0,
            longitude=2.0,
            source_ajout='manuel',
            ajoutee_par=admin_user,
        )

        client.force_login(admin_user)
        data = {
            'nom': 'Commune1',
            'code_insee': commune2.code_insee,  # Code INSEE de commune2
            'latitude': '48.0',
            'longitude': '2.0',
        }
        response = client.post(reverse('geo:modifier_commune', args=[commune1.id]), data)

        commune1.refresh_from_db()
        assert commune1.code_insee == '99111'  # Pas changé
        messages = list(get_messages(response.wsgi_request))
        assert any('existe déjà' in str(m) for m in messages)

    def test_modification_sans_champs_obligatoires(self, client, admin_user, commune_test):
        """La modification sans champs obligatoires est refusée."""
        client.force_login(admin_user)
        data = {
            'nom': '',  # Nom vide
            'code_insee': commune_test.code_insee,
            'latitude': '48.8566',
            'longitude': '2.3522',
        }
        response = client.post(reverse('geo:modifier_commune', args=[commune_test.id]), data)
        messages = list(get_messages(response.wsgi_request))
        assert any('obligatoires' in str(m) for m in messages)


@pytest.mark.django_db
class TestSupprimerCommune:
    """Tests pour la vue supprimer_commune."""

    def test_affichage_confirmation(self, client, admin_user, commune_test):
        """La page de confirmation de suppression s'affiche."""
        client.force_login(admin_user)
        response = client.get(reverse('geo:supprimer_commune', args=[commune_test.id]))
        assert response.status_code == 200
        assert response.context['commune'] == commune_test

    def test_suppression_commune_sans_fiches(self, client, admin_user, commune_test):
        """Une commune sans fiches peut être supprimée."""
        client.force_login(admin_user)
        commune_id = commune_test.id
        response = client.post(reverse('geo:supprimer_commune', args=[commune_id]))
        assert response.status_code == 302  # Redirection
        assert not CommuneFrance.objects.filter(id=commune_id).exists()

        messages = list(get_messages(response.wsgi_request))
        assert any('supprimée avec succès' in str(m) for m in messages)

    def test_suppression_commune_avec_fiches_refusee(
        self, client, admin_user, commune_test
    ):
        """Une commune utilisée dans des fiches ne peut pas être supprimée."""
        # Créer une fiche et l'associer à la commune
        from observations.models import FicheObservation
        from taxonomy.models import Espece

        # Créer une espèce si elle n'existe pas
        espece, _ = Espece.objects.get_or_create(
            nom='Espèce Test',
            defaults={'nom_scientifique': 'Species testus'}
        )

        # Créer une fiche d'observation
        fiche = FicheObservation.objects.create(
            observateur=admin_user,
            espece=espece,
            annee=2024
        )

        # Associer la commune à la fiche via la localisation
        fiche.localisation.commune = commune_test.nom
        fiche.localisation.code_insee = commune_test.code_insee  # Important pour la détection
        fiche.localisation.save()

        client.force_login(admin_user)
        response = client.post(reverse('geo:supprimer_commune', args=[commune_test.id]))

        # La commune doit toujours exister
        assert CommuneFrance.objects.filter(id=commune_test.id).exists()

        messages = list(get_messages(response.wsgi_request))
        assert any('Impossible de supprimer' in str(m) for m in messages)


@pytest.mark.django_db
class TestRechercherNominatim:
    """Tests pour la vue rechercher_nominatim."""

    def test_affichage_formulaire(self, client, admin_user):
        """Le formulaire de recherche Nominatim s'affiche."""
        client.force_login(admin_user)
        response = client.get(reverse('geo:rechercher_nominatim'))
        assert response.status_code == 200

    def test_recherche_sans_nom_refuse(self, client, admin_user):
        """Une recherche sans nom est refusée."""
        client.force_login(admin_user)
        data = {'action': 'rechercher', 'nom': '', 'departement': '75'}
        response = client.post(reverse('geo:rechercher_nominatim'), data)
        messages = list(get_messages(response.wsgi_request))
        assert any('obligatoire' in str(m) for m in messages)

    def test_recherche_nominatim_avec_mock(self, client, admin_user, monkeypatch):
        """La recherche Nominatim fonctionne avec un mock."""
        # Mock du géocodeur avec monkeypatch au lieu de mocker
        class MockGeocodeur:
            def geocoder_commune(self, nom, departement=None):
                return {
                    'latitude': 48.8566,
                    'longitude': 2.3522,
                    'altitude': 35,
                    'nom': 'Paris',
                    'adresse': 'Paris, Île-de-France, France',
                }

        def mock_get_geocodeur():
            return MockGeocodeur()

        monkeypatch.setattr('geo.views_admin.get_geocodeur', mock_get_geocodeur)

        client.force_login(admin_user)
        data = {'action': 'rechercher', 'nom': 'Paris', 'departement': '75'}
        response = client.post(reverse('geo:rechercher_nominatim'), data)

        assert response.status_code == 200
        assert response.context['result'] is not None
        assert 'Paris' in str(response.context['result'])

    def test_ajout_commune_depuis_nominatim(self, client, admin_user):
        """Une commune peut être ajoutée depuis Nominatim."""
        client.force_login(admin_user)
        data = {
            'action': 'ajouter',
            'nom_trouve': 'NominatimVille',
            'code_insee': '99888',  # Code court valide
            'latitude': '48.8566',
            'longitude': '2.3522',
            'altitude': '35',
            'adresse': 'NominatimVille, Paris, France',
        }
        response = client.post(reverse('geo:rechercher_nominatim'), data)

        assert CommuneFrance.objects.filter(nom='NominatimVille').exists()
        commune = CommuneFrance.objects.get(nom='NominatimVille')
        assert commune.source_ajout == 'nominatim'
        assert commune.ajoutee_par == admin_user

    def test_ajout_commune_existante_refuse(self, client, admin_user, commune_test):
        """Impossible d'ajouter une commune qui existe déjà."""
        client.force_login(admin_user)
        data = {
            'action': 'ajouter',
            'nom_trouve': commune_test.nom,  # Nom existant
            'latitude': '48.8566',
            'longitude': '2.3522',
            'adresse': 'Test, France',
        }
        response = client.post(reverse('geo:rechercher_nominatim'), data)

        # Une seule commune avec ce nom
        assert CommuneFrance.objects.filter(nom=commune_test.nom).count() == 1

        messages = list(get_messages(response.wsgi_request))
        assert any('existe déjà' in str(m) for m in messages)


@pytest.mark.django_db
class TestPermissions:
    """Tests des permissions d'accès."""

    def test_toutes_vues_requierent_admin(self, client, normal_user, commune_test):
        """Toutes les vues admin requièrent le statut administrateur."""
        client.force_login(normal_user)

        urls_admin = [
            reverse('geo:liste_communes'),
            reverse('geo:detail_commune', args=[commune_test.id]),
            reverse('geo:creer_commune'),
            reverse('geo:modifier_commune', args=[commune_test.id]),
            reverse('geo:supprimer_commune', args=[commune_test.id]),
            reverse('geo:rechercher_nominatim'),
        ]

        for url in urls_admin:
            response = client.get(url)
            assert response.status_code == 302  # Redirection

    def test_admin_peut_acceder_toutes_vues(self, client, admin_user, commune_test):
        """Un admin peut accéder à toutes les vues."""
        client.force_login(admin_user)

        urls_admin = [
            reverse('geo:liste_communes'),
            reverse('geo:detail_commune', args=[commune_test.id]),
            reverse('geo:creer_commune'),
            reverse('geo:modifier_commune', args=[commune_test.id]),
            reverse('geo:supprimer_commune', args=[commune_test.id]),
            reverse('geo:rechercher_nominatim'),
        ]

        for url in urls_admin:
            response = client.get(url)
            assert response.status_code == 200
