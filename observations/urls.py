# observations/urls.py
from django.contrib.auth.views import LogoutView
from django.urls import path

from accounts.views.auth import CustomLoginView

from .views.api_observateurs import (
    creer_observateur,
    fusionner_observateurs,
    obtenir_nom_ocr_json,
    rechercher_observateurs,
    rechercher_observateurs_similaires,
)
from .views.saisie_observation_view import (
    ajouter_observation,
    fiche_observation_view,
    historique_modifications,
    liberer_verrou_fiche,
    rechercher_fiches,
    saisie_observation,
    soumettre_pour_correction,
    valider_correction,
)
from .views.upload_views import mes_images_sources, upload_image_source, upload_success
from .views.view_transcription import (
    check_progress,
    process_images,
    redirect_to_pilot_ocr,
    select_directory,
    start_transcription_view,
    transcription_results,
)
from .views.views_home import (
    aide_view,
    default_view,
    home,
    test_boutons_styles,
)
from .views.views_observation import (
    liste_fiches_observations,
    statistiques_view,
)
from .views.views_stats import (
    StatsCorrecteursView,
    StatsDashboardView,
)

app_name = 'observations'

urlpatterns = [
    # Routes principales
    path('', home, name='home'),
    path('tableau-de-bord/', default_view, name='default'),
    # Route de test pour les styles de boutons
    path('test-boutons-styles/', test_boutons_styles, name='test_boutons_styles'),
    # Route pour la documentation d'aide
    path('aide/', aide_view, name='aide'),
    # Routes d'authentification
    path('auth/logout/', LogoutView.as_view(next_page='observations:home'), name='logout'),
    path('auth/login/', CustomLoginView.as_view(template_name='login.html'), name='login'),
    # Routes de téléversement d'images sources
    path('upload-image/', upload_image_source, name='upload_image_source'),
    path('upload-success/', upload_success, name='upload_success'),
    path('mes-images/', mes_images_sources, name='mes_images_sources'),
    # Routes d'observations
    path('observations/', saisie_observation, name='observations_list'),
    path('observations/liste/', liste_fiches_observations, name='liste_fiches_observations'),
    path('observations/<int:fiche_id>/', fiche_observation_view, name='fiche_observation'),
    # Routes de statistiques
    path('statistiques/', statistiques_view, name='statistiques'),  # Page publique des stats
    path('statistiques/dashboard/', StatsDashboardView.as_view(), name='stats_dashboard'),
    path('statistiques/corrections/', StatsCorrecteursView.as_view(), name='stats_corrections'),
    #    path('observations/nouvelle/', saisie_observation, name='saisie_observation'),
    #    path('observations/sauvegarde/', traiter_saisie_observation, name='traiter_saisie_observation'),
    path('observations/modifier/<int:fiche_id>/', saisie_observation, name='modifier_observation'),
    path('observations/ajouter/<int:fiche_id>/', ajouter_observation, name='ajouter_observation'),
    # Routes de transcription
    # Redirection de l'ancien système de transcription vers le nouveau (Pilot)
    path('transcription/', redirect_to_pilot_ocr, name='transcription_redirect'),
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
    # Route pour valider la correction d'une fiche
    path(
        'observations/valider/<int:fiche_id>/',
        valider_correction,
        name='valider_correction',
    ),
    # Route pour libérer le verrou d'une fiche
    path(
        'observations/<int:fiche_id>/liberer-verrou/',
        liberer_verrou_fiche,
        name='liberer_verrou_fiche',
    ),
    # Route AJAX pour rechercher des fiches
    path(
        'observations/rechercher/',
        rechercher_fiches,
        name='rechercher_fiches',
    ),
    # Routes API observateurs (recherche similaire, autocomplétion, fusion)
    path(
        'api/observateurs/similaires/',
        rechercher_observateurs_similaires,
        name='api_observateurs_similaires',
    ),
    path(
        'api/observateurs/rechercher/',
        rechercher_observateurs,
        name='api_rechercher_observateurs',
    ),
    path(
        'api/observateurs/fusionner/',
        fusionner_observateurs,
        name='api_fusionner_observateurs',
    ),
    path(
        'api/observateurs/nom-ocr/',
        obtenir_nom_ocr_json,
        name='api_nom_ocr_json',
    ),
    path(
        'api/observateurs/creer/',
        creer_observateur,
        name='api_creer_observateur',
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
