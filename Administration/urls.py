# Administration/urls.py
from django.urls import path
from .views import auth

urlpatterns = [
    # Gestion des utilisateurs
    path('utilisateurs/', auth.ListeUtilisateursView.as_view(), name='liste_utilisateurs'),
    path('utilisateurs/creer/', auth.creer_utilisateur, name='creer_utilisateur'),
    path('utilisateurs/<int:user_id>/modifier/', auth.modifier_utilisateur, name='modifier_utilisateur'),
    path('utilisateurs/<int:user_id>/desactiver/', auth.desactiver_utilisateur, name='desactiver_utilisateur'),
    path('utilisateurs/<int:user_id>/activer/', auth.activer_utilisateur, name='activer_utilisateur'),
    path('utilisateurs/<int:user_id>/detail/', auth.detail_utilisateur, name='detail_utilisateur'),

    # Inscription publique
    path('inscription-publique/', auth.inscription_publique, name='inscription_publique'),

    # Fonctionnalités d'urgence
    path('urgence/promouvoir-administrateur/', auth.promouvoir_administrateur, name='promouvoir_administrateur'),
]
