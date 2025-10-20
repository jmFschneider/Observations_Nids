# 14 Octobre 2025 - Amélioration de l'Interface Utilisateur et Notifications

## Interface Utilisateur

- **Amélioration de l'alignement des formulaires** : Les champs de saisie sont maintenant parfaitement alignés verticalement sur toutes les pages de formulaire (inscription, connexion, modification utilisateur).
- **Notification sur page d'accueil** : Ajout d'un bandeau d'alerte jaune sur la page d'accueil pour les administrateurs lorsqu'il y a des demandes de compte en attente.
  - Le bandeau affiche le nombre de demandes en attente
  - Lien direct vers la liste filtrée des demandes
  - Bouton de fermeture temporaire (rouge foncé) pour masquer l'alerte

## Pages modifiées

- `/accounts/inscription-publique/` : Alignement des champs avec système de table CSS
- `/auth/login/` : Amélioration de la mise en page et de l'alignement
- `/accounts/utilisateurs/<id>/modifier/` : Refonte complète avec alignement cohérent
- `/` (page d'accueil) : Ajout du bandeau de notification pour administrateurs

---

# Octobre 2025 - Refactoring et Optimisation

## Amélioration de la Structure des URLs

- **Standardisation** : La structure des URLs a été harmonisée à travers toutes les applications (`observations`, `accounts`, `ingest`) pour plus de clarté et de maintenabilité.
- **Préfixes d'application** : Des préfixes clairs (`/accounts/`, `/ingest/`) ont été mis en place pour éviter les conflits.
- **Conventions** : Les URLs utilisent maintenant des tirets (`-`) et des noms plus descriptifs.

## Optimisation de la Page d'Édition

- **Nettoyage du code** : Suppression des logs de débogage et des commentaires superflus dans le code Python et JavaScript.
- **Amélioration sémantique HTML** : Remplacement des `<div>` génériques par des balises HTML5 sémantiques (`<section>`, `<header>`) pour améliorer la structure et l'accessibilité.
- **Performance** : Réduction des entrées/sorties disque côté serveur (moins de logs) et code JavaScript plus léger côté client.

---

# le 9 mai 2025
1. début de déploiement sur le serveur de production. 
2. Ajout du fichier "mise_a_jour.sh" à la racine de mon dossier perso
3. modification du fichier setting.py pour avoir une lecture correct du fichier .env

# le 28 avril 2025
# V 1.1.0 

1. Mise en place de Celery pour réaliser le traitement des transcriptions et modification du suivi de cette opération
2. Redis est utilisé pour la communication entre Celery et Django

# le 22 avril 2025
# V 1.0.1 

1. Correction de different bug css et js
2. Correction du traitement du lien "montrer l'Image" de la page saisie correctionn fiche observation

# le 21 avril 2025
# V 1.0.0

1. **Mise en place versioning** avec la variable  settings.VERSION
2. **Point sur l'application**
- la gestion des utilisateur se fait depuis l'application administration
- re
- la transcription des images fonctionne
- la lecture des fichiers json également
- le remplissage de la bdd est ok
- modification des fiches observations fonctionnelle
- la suppression des importations est effective.
- modification utilisateur également

3. **Gestion des variables globales**
- déplacement de toutes ces variables vers le fichier Observations_Nids/config.py
- les clefs neessaires ont été déplacees vers le répertoire .env qui n'est pas versionné.