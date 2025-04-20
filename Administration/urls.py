# Administration/urls.py
from django.urls import path
from . import views, views_emergency

urlpatterns = [
    # Gestion des utilisateurs
    path('utilisateurs/', views.liste_utilisateurs, name='liste_utilisateurs'),
    path('utilisateurs/creer/', views.creer_utilisateur, name='creer_utilisateur'),
    path('utilisateurs/<int:user_id>/modifier/', views.modifier_utilisateur, name='modifier_utilisateur'),
    path('utilisateurs/<int:user_id>/desactiver/', views.desactiver_utilisateur, name='desactiver_utilisateur'),
    path('utilisateurs/<int:user_id>/activer/', views.activer_utilisateur, name='activer_utilisateur'),
    path('utilisateurs/<int:user_id>/detail/', views.detail_utilisateur, name='detail_utilisateur'),

    # Inscription publique
    path('inscription-publique/', views.inscription_publique, name='inscription_publique'),

    # Fonctionnalités d'urgence
    path('urgence/promouvoir-administrateur/', views_emergency.promouvoir_administrateur, name='promouvoir_administrateur'),
]
