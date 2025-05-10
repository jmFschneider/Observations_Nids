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