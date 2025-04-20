# Observations/urls.py
from django.contrib.auth.views import LoginView, LogoutView
from django.urls import path

from Observations.views.saisie_observation_view import fiche_test_observation_view, ajouter_observation
from Observations.views.view_transcription import select_directory, process_images, check_progress, \
    transcription_results
from Observations.views.views_home import home, default_view
from Observations.views.views_observation import (
    fiche_observation_view)

from Observations.views.views_saisie_old import saisie_observation, traiter_saisie_observation

urlpatterns = [
    path('', home, name='home'),
    path('default/', default_view, name='default'),

    # Routes d'authentification - à conserver
    path('logout/', LogoutView.as_view(next_page='home'), name='logout'),
    path('login/', LoginView.as_view(template_name='login.html'), name='login'),

    # Routes d'observations
    path('fiche/<int:fiche_id>/', fiche_observation_view, name='fiche_observation'),
    path('observations/nouvelle/', saisie_observation, name='saisie_observation'),
    path('observations/sauvegarde/', traiter_saisie_observation, name='traiter_saisie_observation'),
    path('observations/saisie/', fiche_test_observation_view, name='saisie_test_new'),
    path('observations/saisie/<int:fiche_id>/', fiche_test_observation_view, name='saisie_test_edit'),
    path('observations/ajoutobservation/<int:fiche_id>/', ajouter_observation, name='saisie_observation'),

    # Routes de transcription
    path('select-directory/', select_directory, name='select_directory'),
    path('process-images/', process_images, name='process_images'),
    path('check-progress/', check_progress, name='check_progress'),
    path('transcription-results/', transcription_results, name='transcription_results'),
]