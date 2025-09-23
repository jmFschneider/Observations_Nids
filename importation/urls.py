# urls.py
from django.urls import path

# from .views.workflow_importation_legacy import (
#    especes,
#    home,
#    importation,
# )
from .views import (
    especes,
    home,
    importation,
)
from .views.especes import valider_especes_multiples

urlpatterns = [
    # Accueil et importation initiale
    path('', home.accueil_importation, name='accueil_importation'),
    path('preparer/', importation.preparer_importations, name='preparer_importations'),
    path('importer-json/', importation.importer_json, name='importer_json'),
    path('extraire-candidats/', importation.extraire_candidats, name='extraire_candidats'),
    # Gestion des espèces candidates
    path('especes/', especes.liste_especes_candidates, name='liste_especes_candidates'),
    path('especes/valider-multiples/', valider_especes_multiples, name='valider_especes_multiples'),
    path('especes/<int:espece_id>/valider/', especes.valider_espece, name='valider_espece'),
    path('especes/creer/', especes.creer_nouvelle_espece, name='creer_nouvelle_espece'),
    # Gestion des importations
    path('liste/', importation.liste_importations, name='liste_importations'),
    path('detail/<int:importation_id>/', importation.detail_importation, name='detail_importation'),
    path(
        'finaliser/<int:importation_id>/',
        importation.finaliser_importation,
        name='finaliser_importation',
    ),
    path('resume/', home.resume_importation, name='resume_importation'),
    # Réinitialisation
    path(
        'reinitialiser/<int:importation_id>/',
        importation.reinitialiser_importation,
        name='reinitialiser_importation',
    ),
    path(
        'reinitialiser-toutes/',
        importation.reinitialiser_toutes_importations,
        name='reinitialiser_toutes_importations',
    ),
]
