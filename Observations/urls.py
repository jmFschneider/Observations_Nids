from django.contrib.auth.views import LoginView, LogoutView
from django.urls import path
from Observations.views.views_home import home, user_list, user_detail, inscription, default_view
from Observations.views.views_observation import (
    fiche_observation_view, nid_detail_view, resume_observation_view,
    causes_echec_view, remarque_view  # Ajout de remarque_view
)
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
    path('fiche/<int:fiche_id>/nid/', nid_detail_view, name='nid_detail'),
    path('fiche/<int:fiche_id>/resume/', resume_observation_view, name='resume_observation'),
    path('fiche/<int:fiche_id>/causes_echec/', causes_echec_view, name='causes_echec'),
    path('fiche/<int:fiche_id>/remarque/', remarque_view, name='remarque'),  # Correction ici
    path('observations/nouvelle/', saisie_observation, name='saisie_observation'),
    path('observations/sauvegarde/', traiter_saisie_observation, name='traiter_saisie_observation'),
]
