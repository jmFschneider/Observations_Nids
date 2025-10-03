# Projet Observations Nids - Guide de Développement Claude

## Vue d'ensemble du projet

**Observations Nids** est une application Django pour la gestion d'observations ornithologiques de nidification. L'application permet la transcription OCR automatique de fiches papier, la saisie manuelle, la correction collaborative et la validation des données avec traçabilité complète.

### Objectifs principaux
1. **Numérisation automatisée** : OCR des fiches papier via Google Vision API
2. **Saisie et correction** : Interface web intuitive pour gérer les observations
3. **Workflow collaboratif** : Système de rôles (observateur, correcteur, validateur, admin)
4. **Traçabilité** : Historique complet de toutes les modifications
5. **Qualité des données** : Validation stricte et workflow de révision

---

## Architecture du projet

### Structure des applications Django

```
observations_nids/
├── accounts/              # Authentification et gestion utilisateurs
├── audit/                 # Historique et traçabilité des modifications
├── core/                  # Fonctionnalités communes et utilitaires
├── geo/                   # Gestion des localisations géographiques
├── ingest/                # Ingestion et traitement de données externes
├── observations/          # Application principale - gestion des observations
├── review/                # Système de révision et validation
├── taxonomy/              # Classification taxonomique des espèces
└── observations_nids/     # Configuration Django principale
```

### Applications et responsabilités

#### **accounts/** - Gestion des utilisateurs
- Modèle `Utilisateur` (AUTH_USER_MODEL personnalisé)
- Rôles : observateur, correcteur, validateur, administrateur
- Authentification et permissions

#### **audit/** - Traçabilité
- Modèle `HistoriqueModification` : enregistre toutes les modifications
- Tracking automatique au niveau du champ
- Interface de consultation de l'historique

#### **core/** - Utilitaires partagés
- Fonctions communes à plusieurs applications
- Mixins et décorateurs réutilisables
- Configuration partagée

#### **geo/** - Données géographiques
- Modèle `Localisation` : coordonnées, commune, lieu-dit, département
- Gestion des sites d'observation
- Validation des coordonnées GPS

#### **ingest/** - Traitement des données externes
- Import de données depuis fichiers JSON
- Parsing et normalisation des données
- Gestion des candidats (espèces, observateurs)

#### **observations/** - Application principale
- Modèles centraux : `FicheObservation`, `Observation`, `Nid`, `ResumeObservation`, `CausesEchec`
- Vues de saisie, modification, consultation
- Système de transcription OCR (Celery + Google Vision API)
- Interface principale de l'application

#### **review/** - Révision et validation
- Workflow de correction et validation
- États de correction : nouveau, en_cours, corrigé, validé, rejeté
- Suivi de la progression

#### **taxonomy/** - Taxonomie
- Modèle `Espece` : classification des espèces d'oiseaux
- Nomenclature scientifique et vernaculaire

---

## Modèles de données principaux

### FicheObservation (observations/models.py)
**Modèle central** représentant une fiche d'observation complète.

**Champs principaux :**
- `num_fiche` : AutoField (clé primaire)
- `observateur` : ForeignKey vers Utilisateur
- `espece` : ForeignKey vers Espece
- `annee` : Année de l'observation
- `chemin_image` : Chemin vers l'image scannée
- `chemin_json` : Chemin vers les données OCR JSON
- `transcription` : Boolean indiquant si issue de la transcription OCR

**Relations OneToOne :**
- `Localisation` : où se trouve le nid
- `Nid` : caractéristiques du nid
- `ResumeObservation` : synthèse des données de reproduction
- `CausesEchec` : causes d'échec de la nidification
- `EtatCorrection` : état du workflow de correction

**Particularités :**
- Création automatique des objets liés lors du `save()` d'une nouvelle fiche
- Index sur `observateur` et `date_creation` pour les performances

### Observation (observations/models.py)
**Observations individuelles** au sein d'une fiche (relation OneToMany).

**Champs :**
- `fiche` : ForeignKey vers FicheObservation
- `date_observation` : Date
- `heure_observation` : Time
- `nombre_oeufs` : IntegerField
- `nombre_poussins` : IntegerField
- `notes` : TextField pour remarques

### Autres modèles importants

**Nid** : hauteur, support, orientation, couverture végétale
**Localisation** : commune, département, coordonnées GPS, altitude, paysage
**ResumeObservation** : nombre d'œufs pondus/éclos, nombre de poussins
**CausesEchec** : description textuelle des causes d'échec
**EtatCorrection** : statut, pourcentage de complétion, dates de modification

---

## Workflow principal : De la transcription à la validation

### 1. Transcription automatique (observations/views/view_transcription.py)

**URLs :**
- `/transcription/demarrer/` : Interface de démarrage
- `/transcription/selection-repertoire/` : Sélection du dossier d'images
- `/transcription/traiter-images/` : Lancement du traitement
- `/transcription/verifier-progression/` : API de suivi en temps réel
- `/transcription/resultats/` : Affichage des résultats

**Technologies :**
- **Celery** : traitement asynchrone des images par lots
- **Google Vision API** : OCR et extraction de texte
- **Redis** : broker de messages pour Celery

**Processus :**
1. L'utilisateur sélectionne un dossier contenant les images de fiches
2. Une tâche Celery est lancée pour traiter chaque image
3. Google Vision API extrait le texte de chaque fiche
4. Parsing intelligent des données structurées
5. Création automatique des `FicheObservation` en base
6. Interface de monitoring en temps réel
7. Redirection vers la liste des fiches créées

**Fichiers clés :**
- `observations/tasks.py` : Tâches Celery pour transcription
- `observations/templates/transcription/` : Templates de l'interface
- Configuration Celery dans `observations_nids/settings.py`

### 2. Correction et saisie (observations/views/saisie_observation_view.py)

**URL principale :** `/observations/modifier/<fiche_id>/`

**Interface de correction (`saisie_observation_optimise.html`) :**

La page est divisée en sections (cards Bootstrap) :
1. **Informations générales** : observateur, espèce, année
2. **Localisation** : commune, coordonnées GPS, altitude, paysage
3. **Description du nid** : hauteur, support, orientation
4. **Observations** : tableau dynamique avec date/heure, œufs, poussins, notes
5. **Résumé** : synthèse des données de reproduction
6. **Causes d'échec et remarques** : description des échecs

**Fonctionnalités avancées :**
- **Django Formsets** : gestion dynamique des observations multiples
- **Validation en temps réel** : contrôles de cohérence
- **Système de remarques** : popup modal AJAX pour ajouter des remarques
- **Suppression d'observations** : boutons pour marquer/supprimer
- **Sauvegarde** : persistance de l'état de correction
- **Interface responsive** : adaptée tablettes et écrans tactiles

**Formulaires (observations/forms.py) :**
- `FicheObservationForm`
- `LocalisationForm`
- `NidForm`
- `ObservationForm`
- `ResumeObservationForm`
- `CausesEchecForm`

### 3. Consultation (observations/views/views_observation.py)

**URLs :**
- `/observations/fiche/<fiche_id>/` : Vue détaillée d'une fiche
- `/observations/liste/` : Liste paginée des fiches

**Template :** `fiche_observation.html`

**Affichage :**
- Résumé de la fiche avec toutes les données
- Tableau des observations chronologiques
- Historique des modifications
- Actions : modifier, voir historique, supprimer

### 4. Audit et traçabilité (audit/models.py)

**Modèle :** `HistoriqueModification`

**Champs :**
- `fiche` : ForeignKey vers FicheObservation
- `utilisateur` : qui a fait la modification
- `date_modification` : quand
- `champ_modifie` : quel champ
- `ancienne_valeur` / `nouvelle_valeur` : avant/après
- `type_modification` : création, modification, suppression

**Fonctionnalités :**
- Tracking automatique via signaux Django
- Granularité au niveau du champ
- Interface de consultation : `/observations/historique/<fiche_id>/`

### 5. Validation (review/)

**Workflow :**
1. **Nouveau** : fiche créée par transcription ou saisie manuelle
2. **En cours** : en cours de correction par un correcteur
3. **Corrigé** : soumis pour validation
4. **Validé** : approuvé par un validateur
5. **Rejeté** : refusé, retour en correction

**URL :** `/observations/soumettre/<fiche_id>/`

---

## Configuration technique

### Variables d'environnement (.env)

**Fichier de référence :** `.env.example`

**Variables essentielles :**
```bash
# Django
SECRET_KEY=your-secret-key
DEBUG=True  # False en production
ALLOWED_HOSTS=localhost,127.0.0.1

# Base de données
DATABASE_ENGINE=sqlite3  # ou postgresql
DATABASE_NAME=db.sqlite3
DATABASE_USER=
DATABASE_PASSWORD=
DATABASE_HOST=
DATABASE_PORT=

# Session
SESSION_COOKIE_AGE=3600

# Celery
CELERY_BROKER_URL=redis://127.0.0.1:6379/0

# Debug Toolbar
USE_DEBUG_TOOLBAR=True

# Google Vision API (pour OCR)
GOOGLE_APPLICATION_CREDENTIALS=/path/to/credentials.json
```

### Configuration Pydantic (observations_nids/config.py)

Le projet utilise **Pydantic Settings** pour valider et typer les variables d'environnement.

**Avantages :**
- Validation stricte des variables
- Types Python avec autocomplétion
- Documentation automatique
- Gestion des valeurs par défaut

### Base de données

**Développement :** SQLite (`db_local.sqlite3`)
**Production :** PostgreSQL (recommandé)

**Migrations :**
```bash
python manage.py makemigrations
python manage.py migrate
```

### Technologies frontend

- **Bootstrap 5** : framework CSS responsive
- **Font Awesome** : icônes
- **JavaScript vanilla** : interactions dynamiques
- **AJAX** : communication asynchrone (remarques)

### Authentification

- **Modèle personnalisé :** `accounts.Utilisateur`
- **LOGIN_URL :** `/auth/login/`
- **LOGIN_REDIRECT_URL :** `/`
- **Session :** expire après 1 heure d'inactivité

---

## Commandes utiles

### Développement

```bash
# Démarrer le serveur de développement
python manage.py runserver

# Lancer Celery (pour transcription)
celery -A observations_nids worker --loglevel=info

# Lancer Redis (broker Celery)
redis-server

# Créer un superutilisateur
python manage.py createsuperuser

# Collecter les fichiers statiques
python manage.py collectstatic

# Lancer les tests
pytest
```

### Migrations

```bash
# Créer des migrations
python manage.py makemigrations

# Appliquer les migrations
python manage.py migrate

# Voir l'état des migrations
python manage.py showmigrations

# Réinitialiser les migrations (DANGER)
python manage.py migrate <app> zero
```

### Outils de développement

```bash
# Formater le code avec Black
black .

# Linter avec Ruff
ruff check .

# Type checking avec mypy
mypy .

# Django shell amélioré
python manage.py shell_plus

# Voir les dépendances
pip-compile requirements.in
```

---

## Bonnes pratiques de développement

### Code style
- **PEP 8** : respecter les conventions Python
- **Black** : formateur de code automatique configuré
- **Type hints** : utiliser les annotations de type
- **Docstrings** : documenter les fonctions et classes complexes

### Django
- **Migrations** : toujours créer des migrations pour les changements de modèles
- **Transactions** : utiliser `@transaction.atomic` pour les opérations critiques
- **Requêtes ORM** : optimiser avec `select_related()` et `prefetch_related()`
- **Permissions** : vérifier les permissions dans les vues
- **CSRF** : toujours inclure `{% csrf_token %}` dans les formulaires

### Git
- **Commits atomiques** : un commit = une fonctionnalité/correction
- **Messages explicites** : décrire ce qui a été fait et pourquoi
- **Branches** : utiliser des branches pour les nouvelles fonctionnalités
- **Tests** : s'assurer que les tests passent avant de commit

### Sécurité
- **Secrets** : jamais de secrets dans le code (utiliser .env)
- **Validation** : toujours valider les données côté serveur
- **SQL Injection** : utiliser l'ORM Django (pas de SQL brut)
- **XSS** : échapper les données utilisateur dans les templates

---

## Points d'attention et pièges courants

### Formsets Django
- **Management form** : toujours inclure `{{ formset.management_form }}` dans le template
- **Prefix** : utiliser des prefix différents si plusieurs formsets sur la même page
- **Validation** : appeler `formset.is_valid()` ET `form.is_valid()`
- **Suppression** : utiliser `DELETE` checkbox pour marquer les lignes à supprimer

### Celery
- **Worker** : toujours démarrer un worker Celery pour que les tâches s'exécutent
- **Broker** : Redis ou RabbitMQ doit être en cours d'exécution
- **Sérialisation** : préférer JSON à pickle pour la sécurité
- **Retry** : configurer des retry pour les tâches critiques

### Base de données
- **Migrations** : ne jamais modifier les migrations déjà appliquées en production
- **Transactions** : attention aux deadlocks avec des transactions imbriquées
- **Index** : ajouter des index sur les champs fréquemment filtrés
- **N+1 queries** : utiliser `select_related()` / `prefetch_related()`

### Frontend
- **Static files** : run `collectstatic` avant le déploiement
- **AJAX** : toujours inclure le CSRF token dans les requêtes POST
- **Bootstrap** : vérifier la compatibilité des composants (utilise Bootstrap 5)

---

## Structure des tests

Le projet utilise **pytest** avec **pytest-django**.

**Configuration :** `pytest.ini` ou `pyproject.toml`

**Structure :**
```
observations/tests/
├── __init__.py
├── conftest.py          # Fixtures communes
├── test_models.py       # Tests des modèles
├── test_views.py        # Tests des vues
└── test_forms.py        # Tests des formulaires
```

**Fixtures communes (conftest.py) :**
- `client` : client de test Django
- `utilisateur` : utilisateur de test
- `fiche_observation` : fiche de test
- `espece` : espèce de test

**Lancer les tests :**
```bash
pytest                           # Tous les tests
pytest observations/tests/       # Tests d'une app
pytest -v                        # Verbose
pytest --cov                     # Avec couverture
pytest -k test_model             # Tests correspondant au pattern
```

---

## Déploiement

### Prérequis production
- Python 3.11+
- PostgreSQL
- Redis
- Nginx ou Apache
- Gunicorn ou uWSGI
- Supervisord (pour Celery)

### Configuration production

**settings.py :**
```python
DEBUG = False
ALLOWED_HOSTS = ['votre-domaine.fr']
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'observations_nids',
        'USER': 'postgres_user',
        'PASSWORD': 'secure_password',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```

**Commandes de déploiement :**
```bash
# Installer les dépendances
pip install -r requirements-prod.txt

# Collecter les fichiers statiques
python manage.py collectstatic --noinput

# Appliquer les migrations
python manage.py migrate

# Créer un superutilisateur
python manage.py createsuperuser

# Démarrer Gunicorn
gunicorn observations_nids.wsgi:application --bind 0.0.0.0:8000
```

---

## Points techniques notables

### Gestion automatique des objets liés
Lors de la création d'une `FicheObservation`, les objets liés sont automatiquement créés avec des valeurs par défaut :
- `Localisation`
- `Nid`
- `ResumeObservation`
- `CausesEchec`
- `EtatCorrection`

Cela simplifie la logique métier et garantit l'intégrité des données.

### Optimisations performance
- **Index de base de données** sur les champs fréquemment filtrés
- **Select/Prefetch related** pour réduire les requêtes N+1
- **Pagination** pour les listes longues
- **Cache** pour les données de référence (espèces, utilisateurs)

### Sécurité
- **CSRF Protection** activée
- **Session security** : expiration automatique
- **Permissions** vérifiées dans chaque vue
- **SQL Injection** : utilisation exclusive de l'ORM
- **XSS** : autoescaping dans les templates

---

## Ressources et documentation

### Django
- [Documentation officielle Django](https://docs.djangoproject.com/)
- [Django ORM Optimization](https://docs.djangoproject.com/en/stable/topics/db/optimization/)
- [Django Forms](https://docs.djangoproject.com/en/stable/topics/forms/)

### Celery
- [Celery Documentation](https://docs.celeryproject.org/)
- [Django + Celery](https://docs.celeryproject.org/en/stable/django/first-steps-with-django.html)

### Autres
- [Google Vision API](https://cloud.google.com/vision/docs)
- [Pydantic Settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/)
- [pytest-django](https://pytest-django.readthedocs.io/)

---

## État actuel du projet et travaux en cours

### Refactoring récent (branche: refactor-structure-apps)

Le projet a été récemment réorganisé pour séparer les responsabilités en applications distinctes :
- Migration des fonctionnalités d'`administration/` vers `accounts/`
- Migration des fonctionnalités d'`importation/` vers `ingest/`
- Création de nouvelles apps : `audit/`, `core/`, `geo/`, `review/`, `taxonomy/`

**Statut :** En cours - les anciens fichiers sont marqués pour suppression (git status)

### Optimisations récentes
- Nettoyage des logs de debug
- Amélioration de la structure HTML (sémantique HTML5)
- Optimisation de l'interface de saisie
- Correction du bug de suppression d'observations

### Tests
Structure de tests ajoutée avec pytest, mais couverture à améliorer.

---

## Instructions pour Claude

### Approche générale
1. **Lire avant d'éditer** : toujours lire les fichiers existants avant de les modifier
2. **Préférer l'édition** : éditer les fichiers existants plutôt que d'en créer de nouveaux
3. **Respecter l'architecture** : suivre la structure d'applications existante
4. **Tests** : ajouter des tests pour les nouvelles fonctionnalités
5. **Documentation** : mettre à jour ce fichier pour les changements importants

### Workflow de développement
1. **Comprendre le contexte** : lire les modèles, vues et templates concernés
2. **Planifier** : utiliser TodoWrite pour les tâches complexes
3. **Implémenter** : suivre les bonnes pratiques Django
4. **Tester** : vérifier que les tests passent
5. **Commit** : créer un commit clair si demandé

### Cas d'usage fréquents

**Ajouter un champ à un modèle :**
1. Modifier `models.py`
2. Créer une migration : `python manage.py makemigrations`
3. Appliquer : `python manage.py migrate`
4. Mettre à jour les formulaires dans `forms.py`
5. Mettre à jour les templates
6. Ajouter des tests

**Créer une nouvelle vue :**
1. Définir la vue dans `views/`
2. Ajouter l'URL dans `urls.py`
3. Créer le template dans `templates/`
4. Vérifier les permissions
5. Ajouter des tests

**Modifier l'interface :**
1. Identifier le template concerné
2. Lire le template existant
3. Éditer avec les changements
4. Vérifier la cohérence avec Bootstrap 5
5. Tester l'interface

### Fichiers critiques à ne pas modifier sans précaution
- `observations/models.py` : modèles centraux
- `observations_nids/settings.py` : configuration Django
- Migrations existantes : ne jamais modifier
- `observations_nids/urls.py` : routing principal

### Priorités de développement
1. **Stabilité** : ne pas casser les fonctionnalités existantes
2. **Tests** : améliorer la couverture de tests
3. **Performance** : optimiser les requêtes ORM
4. **UX** : améliorer l'interface utilisateur
5. **Documentation** : maintenir ce guide à jour

---

*Documentation générée pour Claude Code - Version 1.0*
*Dernière mise à jour : 2025-10-03*
