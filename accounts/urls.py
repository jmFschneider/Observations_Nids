from django.urls import path

from .views import auth

app_name = 'accounts'

urlpatterns = [
    # Gestion des utilisateurs
    path('utilisateurs/', auth.ListeUtilisateursView.as_view(), name='liste_utilisateurs'),
    path('utilisateurs/creer/', auth.creer_utilisateur, name='creer_utilisateur'),
    path(
        'utilisateurs/<int:user_id>/modifier/',
        auth.modifier_utilisateur,
        name='modifier_utilisateur',
    ),
    path(
        'utilisateurs/<int:user_id>/desactiver/',
        auth.desactiver_utilisateur,
        name='desactiver_utilisateur',
    ),
    path(
        'utilisateurs/<int:user_id>/activer/', auth.activer_utilisateur, name='activer_utilisateur'
    ),
    path('utilisateurs/<int:user_id>/detail/', auth.detail_utilisateur, name='detail_utilisateur'),
    path(
        'utilisateurs/<int:user_id>/valider/', auth.valider_utilisateur, name='valider_utilisateur'
    ),
    # Profil utilisateur
    path('mon-profil/', auth.mon_profil, name='mon_profil'),
    # Inscription publique
    path('inscription-publique/', auth.inscription_publique, name='inscription_publique'),
    path('inscription-completee/', auth.inscription_completee, name='inscription_completee'),
    path('compte-en-attente/<int:user_id>/', auth.compte_en_attente, name='compte_en_attente'),
    path(
        'renvoyer-notification/<int:user_id>/',
        auth.renvoyer_notification_admin,
        name='renvoyer_notification',
    ),
    # Fonctionnalités d'urgence
    path(
        'urgence/promouvoir-administrateur/',
        auth.promouvoir_administrateur,
        name='promouvoir_administrateur',
    ),
    # Réinitialisation de mot de passe
    path('mot-de-passe-oublie/', auth.mot_de_passe_oublie, name='mot_de_passe_oublie'),
    path(
        'reinitialiser-mot-de-passe/<uidb64>/<token>/',
        auth.reinitialiser_mot_de_passe,
        name='reinitialiser_mot_de_passe',
    ),
]
