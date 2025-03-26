# urls.py
from django.urls import path
from . import views

urlpatterns = [
    # Accueil et importation initiale
    path('importation/', views.accueil_importation, name='accueil_importation'),
    path('preparer/', views.preparer_importations, name='preparer_importations'),
    path('importation/importer_json/', views.importer_json, name='importer_json'),
    path('importation/extraire_candidats/', views.extraire_candidats, name='extraire_candidats'),

    # Gestion des espèces candidates
    path('importation/especes/', views.liste_especes_candidates, name='liste_especes_candidates'),
    path('importation/especes/<int:espece_id>/valider/', views.valider_espece, name='valider_espece'),
    path('importation/especes/creer/', views.creer_nouvelle_espece, name='creer_nouvelle_espece'),

    # Gestion des observateurs candidats
    path('importation/observateurs/', views.liste_observateurs_candidats, name='liste_observateurs_candidats'),
    path('importation/observateurs/<int:observateur_id>/valider/', views.valider_observateur,
         name='valider_observateur'),
    path('importation/observateurs/creer/', views.creer_nouvel_utilisateur, name='creer_nouvel_utilisateur'),

    # Gestion des importations
    path('importation/preparer/', views.preparer_importations, name='preparer_importations'),
    path('importation/liste/', views.liste_importations, name='liste_importations'),
    path('importation/detail/<int:importation_id>/', views.detail_importation, name='detail_importation'),
    path('importation/finaliser/<int:importation_id>/', views.finaliser_importation, name='finaliser_importation'),

    # Nouvelles routes pour la réinitialisation
    path('importation/reinitialiser/<int:importation_id>/', views.reinitialiser_importation, name='reinitialiser_importation'),
    path('importation/reinitialiser-toutes/', views.reinitialiser_toutes_importations, name='reinitialiser_toutes_importations'),
]
