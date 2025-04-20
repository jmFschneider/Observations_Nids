# urls.py
from django.urls import path
from . import views

urlpatterns = [
    # Accueil et importation initiale
    path('', views.accueil_importation, name='accueil_importation'),
    path('preparer/', views.preparer_importations, name='preparer_importations'),
    path('importer-json/', views.importer_json, name='importer_json'),
    path('extraire-candidats/', views.extraire_candidats, name='extraire_candidats'),

    # Gestion des espèces candidates
    path('especes/', views.liste_especes_candidates, name='liste_especes_candidates'),
    path('especes/<int:espece_id>/valider/', views.valider_espece, name='valider_espece'),
    path('especes/creer/', views.creer_nouvelle_espece, name='creer_nouvelle_espece'),

    # Gestion des importations
    path('liste/', views.liste_importations, name='liste_importations'),
    path('detail/<int:importation_id>/', views.detail_importation, name='detail_importation'),
    path('finaliser/<int:importation_id>/', views.finaliser_importation, name='finaliser_importation'),
    path('resume/', views.resume_importation, name='resume_importation'),

    # Réinitialisation
    path('reinitialiser/<int:importation_id>/', views.reinitialiser_importation, name='reinitialiser_importation'),
    path('reinitialiser-toutes/', views.reinitialiser_toutes_importations, name='reinitialiser_toutes_importations'),
]
