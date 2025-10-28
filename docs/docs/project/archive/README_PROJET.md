# Projet Observations Nids - Documentation Technique

## Vue d'ensemble

Le projet **Observations Nids** est une application Django dédiée à la gestion et au suivi des observations ornithologiques de nidification. L'application permet la saisie, la correction, la validation et l'historique complet des données d'observations de nids d'oiseaux.

### Objectifs principaux

1. **Numérisation automatisée** : Transcription automatique de fiches d'observation papier via OCR Google Vision API
2. **Gestion des données** : Saisie, modification et validation des observations de nidification
3. **Workflow collaboratif** : Système de correction et validation avec rôles utilisateurs différenciés
4. **Traçabilité complète** : Historique détaillé de toutes les modifications
5. **Interface utilisateur intuitive** : Interface web responsive pour la gestion des données

## Architecture du projet

### Structure des applications Django

```
observations_nids/
├── observations/           # Application principale - gestion des observations
├── accounts/              # Gestion des utilisateurs et authentification
├── audit/                 # Historique et traçabilité des modifications
├── core/                  # Fonctionnalités communes et utilitaires
├── geo/                   # Gestion des données géographiques (localisation)
├── ingest/                # Ingestion et traitement des données externes
├── review/                # Système de révision et validation
└── taxonomy/              # Classification taxonomique des espèces
```

### Modèles de données principaux

#### FicheObservation (observations/models.py)
Modèle central représentant une fiche d'observation complète :
- **Métadonnées** : observateur, espèce, année, localisation
- **Images** : chemin vers l'image originale et données JSON de transcription
- **États** : statut de correction et validation
- **Relations** : liens vers localisation, nid, résumé, causes d'échec

#### Observation (observations/models.py)
Observations individuelles au sein d'une fiche :
- **Temporalité** : date et heure d'observation
- **Données quantitatives** : nombre d'œufs, nombre de poussins
- **Observations qualitatives** : notes textuelles

#### Modèles annexes
- **Localisation** : coordonnées géographiques et description du site
- **Nid** : caractéristiques du nid (hauteur, support, orientation)
- **ResumeObservation** : synthèse des données de reproduction
- **CausesEchec** : description des causes d'échec de la nidification

## Workflow principal : De la transcription à la validation

### 1. Phase de transcription (Module `transcription`)

#### Fichiers clés
- `observations/views/view_transcription.py` : Vues pour la transcription automatique
- `observations/tasks.py` : Tâches Celery pour traitement asynchrone
- `observations/templates/transcription/` : Templates pour l'interface de transcription

#### Processus
1. **Sélection du répertoire** (`select_directory`) : L'utilisateur sélectionne un dossier contenant les images de fiches
2. **Lancement du traitement** (`process_images`) : Démarrage d'une tâche Celery pour traitement par lots
3. **Transcription OCR** :
   - Appel à Google Vision API pour extraction du texte
   - Parsing intelligent des données structurées
   - Création automatique des fiches en base de données
4. **Suivi de progression** (`check_progress`) : Interface de monitoring en temps réel
5. **Résultats** (`transcription_results`) : Affichage des résultats avec liens vers les fiches créées

#### Technologies utilisées
- **Celery** : Traitement asynchrone des images
- **Google Vision API** : OCR et extraction de texte
- **Redis/RabbitMQ** : Queue de tâches pour Celery

### 2. Phase de correction (Module principal)

#### Fichiers clés
- `observations/views/saisie_observation_view.py` : Vue principale de saisie/modification
- `observations/templates/saisie/saisie_observation_optimise.html` : Interface de correction
- `observations/forms.py` : Formulaires Django pour la validation des données

#### Interface de correction
L'interface principale (`saisie_observation_optimise.html`) comprend :

1. **Section Fiche** : Données générales (observateur, espèce, année, localisation)
2. **Section Nid** : Caractéristiques du nid
3. **Section Observations** : Tableau dynamique avec :
   - Date/heure de chaque observation
   - Nombre d'œufs et poussins
   - Notes textuelles
   - **Fonctionnalité de suppression** : Boutons pour marquer/supprimer des observations
4. **Section Résumé** : Synthèse des données de reproduction
5. **Section Causes d'échec** : Description des échecs éventuels

#### Fonctionnalités avancées
- **Formsets Django** : Gestion dynamique des observations multiples
- **Validation en temps réel** : Contrôles de cohérence des données
- **Sauvegarde incrémentale** : Possibilité de sauvegarder à tout moment
- **Interface responsive** : Adaptée aux tablettes et écrans tactiles

### 3. Phase d'audit et traçabilité

#### Fichier clé
- `audit/models.py` : Modèle HistoriqueModification

#### Fonctionnalités
- **Tracking automatique** : Chaque modification est automatiquement enregistrée
- **Granularité fine** : Historique au niveau du champ individuel
- **Métadonnées** : Qui, quand, quoi, valeur avant/après
- **Interface de consultation** : Vue dédiée pour consulter l'historique

### 4. Phase de validation (Module `review`)

#### Workflow de validation
1. **Première correction** : Correcteur vérifie et corrige les données OCR
2. **Validation** : Validateur final approuve ou rejette
3. **États de la fiche** : Brouillon → En cours → Validée

## Fichiers et composants techniques importants

### Vues principales
- `saisie_observation()` : Vue principale pour saisie/modification (GET/POST)
- `fiche_observation_view()` : Vue de consultation d'une fiche
- `liste_fiches_observations()` : Liste paginée des fiches

### Formulaires
- `FicheObservationForm` : Formulaire principal
- `ObservationForm` : Formulaire pour une observation individuelle
- `LocalisationForm`, `NidForm`, `ResumeObservationForm` : Formulaires spécialisés

### Templates
- `base.html` : Template de base avec Bootstrap et Font Awesome
- `saisie_observation_optimise.html` : Interface principale de saisie
- `fiche_observation.html` : Vue de consultation
- `liste_fiches_observations.html` : Liste des fiches

### APIs et endpoints
- `/observations/modifier/<id>/` : Modification d'une fiche
- `/observations/fiche/<id>/` : Consultation d'une fiche
- `/observations/liste/` : Liste des fiches
- `/transcription/` : Interface de transcription
- `/transcription/verifier-progression/` : API de suivi de progression

## Configuration technique

### Base de données
- **PostgreSQL** (production) ou **SQLite** (développement)
- **Migrations Django** : Gestion des évolutions de schéma
- **Contraintes d'intégrité** : Relations entre les modèles

### Authentification et autorisation
- **Système d'utilisateurs Django** étendu
- **Rôles** : Observateur, Correcteur, Validateur, Admin
- **Permissions granulaires** par vue et par action

### Technologies frontend
- **Bootstrap 5** : Framework CSS responsive
- **Font Awesome** : Icônes
- **JavaScript vanilla** : Interactions dynamiques
- **AJAX** : Communication asynchrone avec le serveur

### Traitement asynchrone
- **Celery** : Worker pour tâches longues (transcription)
- **Redis/RabbitMQ** : Broker de messages
- **Monitoring** : Interface de suivi des tâches

## Points techniques notables

### Gestion des formsets
L'application utilise intensivement les **Django Inline Formsets** pour gérer les observations multiples au sein d'une fiche. Cela permet :
- Ajout/suppression dynamique d'observations
- Validation cohérente des données liées
- Interface utilisateur fluide

### Optimisations performance
- **Select_related/Prefetch_related** : Optimisation des requêtes ORM
- **Pagination** : Gestion des grandes listes
- **Mise en cache** : Cache des données de référence (espèces, localisations)

### Sécurité
- **CSRF Protection** : Protection contre les attaques CSRF
- **Validation des données** : Contrôles stricts côté serveur
- **Authentification requise** : Toutes les vues nécessitent une authentification
- **Permissions** : Contrôle d'accès basé sur les rôles

## Gestion des Dépendances Python

La gestion des dépendances Python a été restructurée pour plus de clarté et de maintenabilité. Elle s'articule autour de trois fichiers principaux dans le répertoire racine :

-   `requirements-base.txt` : Contient la liste de toutes les dépendances de base requises pour faire fonctionner l'application. Les versions des paquets y sont définies et servent de source unique de vérité.
-   `requirements-dev.txt` : Dédié à l'environnement de développement. Il inclut la base et y ajoute les outils nécessaires pour les tests, le linting et le débogage (ex: `pytest`, `ruff`, `django-debug-toolbar`).
-   `requirements-prod.txt` : Dédié à l'environnement de production. Il inclut la base et y ajoute les paquets spécifiques à la production (ex: `gunicorn`).

### Commandes d'installation

**Pour un environnement de développement complet :**
```bash
pip install -r requirements-dev.txt
```

**Pour un environnement de production :**
```bash
pip install -r requirements-prod.txt
```

Cette organisation assure que les environnements de développement et de production partagent exactement les mêmes versions des paquets de base, évitant ainsi les problèmes de type "ça marche sur ma machine".

## Déploiement et maintenance

### Environnements
- **Développement** : Django runserver + SQLite
- **Production** : Gunicorn + Nginx + PostgreSQL + Redis

### Monitoring
- **Logs applicatifs** : Logging détaillé des opérations
- **Celery monitoring** : Suivi des tâches asynchrones
- **Métriques de performance** : Temps de réponse, utilisation ressources

### Sauvegarde
- **Base de données** : Sauvegardes automatiques PostgreSQL
- **Fichiers uploadés** : Synchronisation des médias
- **Code source** : Versioning Git

---

*Documentation générée automatiquement - Version 1.0*
*Dernière mise à jour : Janvier 2025*