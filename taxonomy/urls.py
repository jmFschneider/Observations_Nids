"""URLs de l'application taxonomy."""

from django.urls import path

from taxonomy import views, views_admin

app_name = 'taxonomy'

urlpatterns = [
    # Liste et détail
    path('especes/', views.liste_especes, name='liste_especes'),
    path('especes/<int:espece_id>/', views.detail_espece, name='detail_espece'),
    # CRUD
    path('especes/creer/', views.creer_espece, name='creer_espece'),
    path('especes/<int:espece_id>/modifier/', views.modifier_espece, name='modifier_espece'),
    path('especes/<int:espece_id>/supprimer/', views.supprimer_espece, name='supprimer_espece'),
    # Import (ancienne interface - conservée pour compatibilité)
    path('importer/', views.importer_especes, name='importer_especes'),
    # Page d'administration des données
    path(
        'administration/',
        views_admin.administration_donnees,
        name='administration_donnees',
    ),
    # Scripts d'administration des données
    path(
        'charger-lof/',
        views_admin.charger_especes_lof_view,
        name='charger_especes_lof',
    ),
    path(
        'charger-taxref/',
        views_admin.charger_especes_taxref_view,
        name='charger_especes_taxref',
    ),
    path(
        'recuperer-liens-oiseaux-net/',
        views_admin.recuperer_liens_oiseaux_net_view,
        name='recuperer_liens_oiseaux_net',
    ),
]
