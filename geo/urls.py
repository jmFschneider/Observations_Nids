from django.urls import path

from . import views, views_admin

app_name = 'geo'

urlpatterns = [
    # APIs AJAX (géocodage et autocomplétion)
    path('geocoder/', views.geocoder_commune_manuelle, name='geocoder_commune'),
    path('rechercher-communes/', views.rechercher_communes, name='rechercher_communes'),
    # Pages de gestion des communes (admin)
    path('communes/', views_admin.liste_communes, name='liste_communes'),
    path('communes/<int:commune_id>/', views_admin.detail_commune, name='detail_commune'),
    path('communes/creer/', views_admin.creer_commune, name='creer_commune'),
    path(
        'communes/<int:commune_id>/modifier/', views_admin.modifier_commune, name='modifier_commune'
    ),
    path(
        'communes/<int:commune_id>/supprimer/',
        views_admin.supprimer_commune,
        name='supprimer_commune',
    ),
    path(
        'communes/rechercher-nominatim/',
        views_admin.rechercher_nominatim,
        name='rechercher_nominatim',
    ),
    # Page d'administration des données
    path(
        'communes/administration/',
        views_admin.administration_donnees,
        name='administration_donnees',
    ),
    # Scripts d'administration des données
    path(
        'communes/charger-api/',
        views_admin.charger_communes_api,
        name='charger_communes_api',
    ),
    path(
        'communes/importer-anciennes/',
        views_admin.importer_anciennes_communes_view,
        name='importer_anciennes_communes',
    ),
    path(
        'communes/verifier-deleguees/',
        views_admin.verifier_communes_deleguees_view,
        name='verifier_communes_deleguees',
    ),
]
