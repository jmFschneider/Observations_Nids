from django.contrib.auth.views import LoginView, LogoutView
from django.urls import path

from Observations.views.view_test_saisie import fiche_test_observation_view, ajouter_observation
from Observations.views.view_transcription import select_directory, process_images, check_progress, \
    transcription_results
from Observations.views.views_home import home, user_list, user_detail, inscription, default_view
from Observations.views.views_observation import (
    fiche_observation_view)

from Observations.views.views_saisie import saisie_observation, traiter_saisie_observation

urlpatterns = [
    path('', home, name='home'),
    path('default/', default_view, name='default'),

    path('inscription/', inscription, name='inscription'),
    path('logout/', LogoutView.as_view(next_page='home'), name='logout'),
    path('login/', LoginView.as_view(template_name='login.html'), name='login'),
    path('users/', user_list, name='user_list'),
    path('users/<int:user_id>/', user_detail, name='user_detail'),
    path('users/add/', inscription, name='user_create'),
    path('fiche/<int:fiche_id>/', fiche_observation_view, name='fiche_observation'),
    path('observations/nouvelle/', saisie_observation, name='saisie_observation'),
    path('observations/sauvegarde/', traiter_saisie_observation, name='traiter_saisie_observation'),
    path('observations/saisie/', fiche_test_observation_view, name='saisie_test_new'),
    path('observations/saisie/<int:fiche_id>/', fiche_test_observation_view, name='saisie_test_edit'),
    path('observations/ajoutobservation/<int:fiche_id>/', ajouter_observation, name='saisie_observation'),
    path('select-directory/', select_directory, name='select_directory'),
    path('process-images/', process_images, name='process_images'),
    path('check-progress/', check_progress, name='check_progress'),
    path('transcription-results/', transcription_results, name='transcription_results'),
]
