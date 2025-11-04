# observations/urls.py
from django.contrib.auth.views import LoginView, LogoutView
from django.urls import path

from .views.saisie_observation_view import (
    ajouter_observation,
    fiche_observation_view,
    historique_modifications,
    saisie_observation,
    soumettre_pour_correction,
)
from .views.upload_views import mes_images_sources, upload_image_source, upload_success
from .views.view_transcription import (
    check_progress,
    process_images,
    select_directory,
    start_transcription_view,
    transcription_results,
)
from .views.views_home import (
    default_view,
    home,
)
from .views.views_observation import (
    liste_fiches_observations,
)
from .views.upload_views import mes_images_sources, upload_image_source, upload_success

app_name = 'observations'

app_name = 'observations'

urlpatterns = [
    # Routes principales
    path('', home, name='home'),
    path('tableau-de-bord/', default_view, name='default'),
    # Routes d'authentification
    path('auth/logout/', LogoutView.as_view(next_page='observations:home'), name='logout'),
    path('auth/login/', LoginView.as_view(template_name='login.html'), name='login'),

    # Routes de téléversement d'images sources
    path('upload-image/', upload_image_source, name='upload_image_source'),
    path('upload-success/', upload_success, name='upload_success'),
    path('mes-images/', mes_images_sources, name='mes_images_sources'),

    # Routes d'observations
    path('observations/', saisie_observation, name='observations_list'),
    path('observations/liste/', liste_fiches_observations, name='liste_fiches_observations'),
    path('observations/<int:fiche_id>/', fiche_observation_view, name='fiche_observation'),
    #    path('observations/nouvelle/', saisie_observation, name='saisie_observation'),
    #    path('observations/sauvegarde/', traiter_saisie_observation, name='traiter_saisie_observation'),
    path('observations/modifier/<int:fiche_id>/', saisie_observation, name='modifier_observation'),
    path('observations/ajouter/<int:fiche_id>/', ajouter_observation, name='ajouter_observation'),
    # Routes de transcription
    path('transcription/selection-repertoire/', select_directory, name='select_directory'),
    path('transcription/traiter-images/', process_images, name='process_images'),
    path('transcription/verifier-progression/', check_progress, name='check_progress'),
    path('transcription/resultats/', transcription_results, name='transcription_results'),
    path('transcription/demarrer/', start_transcription_view, name='start_transcription'),
    # Route pour l'historique des modifications
    path(
        'observations/historique/<int:fiche_id>/',
        historique_modifications,
        name='historique_modifications',
    ),
    # Route pour soumettre une fiche pour correction
    path(
        'observations/soumettre/<int:fiche_id>/',
        soumettre_pour_correction,
        name='soumettre_pour_correction',
    ),
]
'''
# Ajoutez ces URLs à votre liste urlpatterns existante
urlpatterns += [
    # Routes pour la version optimisée
    path('observations/saisie-optimisee/', saisie_observation_optimisee, name='saisie_observation_optimisee'),
    path('observations/saisie-optimisee/<int:fiche_id>/', saisie_observation_optimisee, name='saisie_observation_optimisee'),
    path('observations/ajouter-optimisee/<int:fiche_id>/', ajouter_observation_optimisee, name='ajouter_observation_optimisee'),
    path('observations/historique-optimisee/<int:fiche_id>/', historique_modifications_optimisee, name='historique_modifications_optimisee'),
]
'''
