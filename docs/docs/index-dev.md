# Documentation Développeur - Observations Nids

> **Documentation technique pour les développeurs**
> Architecture, API, tests, déploiement et contribution au projet

---

## 👋 Bienvenue Développeur !

Cette documentation s'adresse aux **développeurs** qui souhaitent :
- 🔧 Contribuer au projet
- 🏗️ Comprendre l'architecture
- 🧪 Écrire des tests
- 🚀 Déployer en production
- ⚙️ Utiliser les API

**Pour les utilisateurs finaux** (observateurs, correcteurs, validateurs), consultez la **[Documentation Utilisateur](index.md)**.

---

## 🚀 Démarrage Rapide Développeur

### Installation de l'environnement de développement

```bash
# 1. Cloner le projet
git clone https://github.com/jmFschneider/Observations_Nids.git
cd Observations_Nids

# 2. Créer l'environnement virtuel
python -m venv .venv
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # macOS/Linux

# 3. Installer les dépendances de développement
pip install -r requirements-dev.txt

# 4. Configurer .env
cp .env.example .env
# Éditer .env avec vos valeurs

# 5. Appliquer les migrations
python manage.py migrate

# 6. Créer un super-utilisateur
python manage.py createsuperuser

# 7. Lancer les services
# Terminal 1: Redis
redis-server

# Terminal 2: Celery
celery -A observations_nids worker --pool=solo --loglevel=info

# Terminal 3: Django
python manage.py runserver
```

**Guide complet** : [Installation Développement](installation/development.md)

---

## 📚 Documentation par Section

### 🏗️ Architecture

Comprendre la structure du projet, les modèles de données et les choix techniques.

| Section | Description |
|---------|-------------|
| **[Vue d'ensemble](architecture/index.md)** | 7 applications Django, 24 modèles, statistiques |
| **[Domaines métier](architecture/index.md#domaines-métier)** | 9 domaines détaillés (utilisateurs, observations, taxonomie, etc.) |
| **[Diagrammes](architecture/diagrammes/erd.md)** | ERD complet avec relations |

**Points d'entrée recommandés :**
1. [Architecture - Vue d'ensemble](architecture/index.md)
2. [Domaine : Fiches d'observation](architecture/domaines/observations.md) (modèle pivot)
3. [Diagramme ERD](architecture/diagrammes/erd.md)

---

### 🚀 Installation & Déploiement

| Guide | Usage | Durée |
|-------|-------|-------|
| **[Installation Développement](installation/development.md)** | Environnement local (SQLite, runserver) | 30 min |
| **[Installation Production](installation/production.md)** | Serveur de production (MariaDB, Apache) | 2h |
| **[Déploiement Production](deployment/production.md)** | Guide complet : sécurisation + déploiement Raspberry Pi | 3-4h |

**Déploiement Production** : Guide unique de 1528 lignes incluant :
- Sécurisation préalable (3 phases)
- Déploiement initial (automatisé/manuel)
- Maintenance et surveillance
- Scripts de backup et monitoring

---

### 🧪 Tests & Qualité

| Document | Description |
|----------|-------------|
| **[Stratégie de Tests](testing/STRATEGIE_TESTS.md)** | Plan complet : 4 phases, 149 tests, fixtures, bonnes pratiques |
| **[Exemple : Tests Reset MDP](testing/TESTS_REINITIALISATION_MDP.md)** | 21 tests documentés avec cas de sécurité |

**Standards de qualité :**
- **Pytest** : Framework de tests
- **Ruff** : Linting et formatage (PEP 8)
- **MyPy** : Vérification de types statiques
- **Couverture** : Objectif 80% (actuellement 41%, 66 tests)

**Commandes :**
```bash
# Lancer les tests
pytest

# Linting
ruff check .
ruff format .

# Typage statique
mypy .

# Couverture
pytest --cov
```

---

### ⚙️ Configuration & API

| Section | Description |
|---------|-------------|
| **[Configuration](configuration/configuration.md)** | Variables d'environnement, settings Django, Redis, Celery |
| **[API Documentation](api/API_DOCUMENTATION.md)** | Endpoints REST (autocomplétion, géocodage) |
| **[Base de données](database/reset_database.md)** | Migrations, reset, maintenance |

**APIs disponibles :**
- `/geo/rechercher-communes/` - Recherche de communes (autocomplétion)
- `/geo/geocoder/` - Géocodage d'une adresse
- `/observations/api/` - Endpoints observations (à documenter)

---

### 📚 Apprentissage & Contribution

| Guide | Description |
|-------|-------------|
| **[Git Workflow](learning/git/README.md)** | Branches, commits, pull requests, bonnes pratiques |
| **[CI-CD](learning/ci-cd/README.md)** | Intégration continue (à implémenter) |
| **[Troubleshooting](learning/troubleshooting/README.md)** | Résolution des problèmes courants |
| **[Bases de données](learning/databases/README.md)** | Migrations, requêtes ORM, optimisations |

---

## 🎯 Par Objectif

### Je veux comprendre le code

1. **[Architecture - Vue d'ensemble](architecture/index.md)** - Structure des 7 applications
2. **[Diagramme ERD](architecture/diagrammes/erd.md)** - Relations entre modèles
3. **[Fiches d'observation](architecture/domaines/observations.md)** - Modèle pivot central
4. **[Workflows](project/workflows.md)** - 5 processus métier détaillés

### Je veux contribuer au code

1. **[Git Workflow](learning/git/README.md)** - Créer une branche, commit, PR
2. **[Stratégie de Tests](testing/STRATEGIE_TESTS.md)** - Écrire des tests
3. **[Installation Développement](installation/development.md)** - Environnement local
4. **[Standards de qualité](#-tests--qualité)** - Ruff, MyPy, Pytest

### Je veux déployer l'application

1. **[Déploiement Production](deployment/production.md)** - Guide complet Raspberry Pi
2. **[Installation Production](installation/production.md)** - Configuration serveur
3. **[Configuration](configuration/configuration.md)** - Variables d'environnement

### Je veux utiliser les API

1. **[API Documentation](api/API_DOCUMENTATION.md)** - Endpoints disponibles
2. **[Géolocalisation](guides/fonctionnalites/geolocalisation.md)** - API géocodage
3. **[Taxonomie](guides/fonctionnalites/taxonomie.md)** - API espèces

---

## 🏗️ Stack Technique

### Backend
- **Django 5.2.7** - Framework web Python
- **Python 3.12** - Langage de programmation
- **MariaDB 10.x** - Base de données (production)
- **SQLite** - Base de données (développement)

### Tâches asynchrones
- **Celery 5.x** - Task queue
- **Redis 7.x** - Message broker

### Frontend
- **Bootstrap 5.3** - Framework CSS
- **JavaScript vanilla** - Interactions (autocomplétion, formsets)
- **AJAX** - Appels API asynchrones

### Tests & Qualité
- **Pytest 8.x** - Framework de tests
- **pytest-django** - Tests Django
- **Ruff 0.x** - Linting et formatage
- **MyPy 1.x** - Vérification de types

### API & Services
- **Google Vision API v1** - OCR pour transcription
- **API Nominatim** - Géocodage (fallback)
- **API données.gouv.fr** - Base Adresse Nationale

### Déploiement
- **Apache 2.4 + mod_wsgi** - Serveur web production
- **Gunicorn** - Alternative WSGI (optionnel)
- **systemd** - Services (Celery)

### Documentation
- **MkDocs 1.5** - Générateur de documentation
- **Material for MkDocs** - Thème
- **Mermaid** - Diagrammes

---

## 📊 Statistiques du Projet

- **Applications Django** : 7 (accounts, observations, ingest, taxonomy, geo, review, audit)
- **Modèles de données** : 24
- **Lignes de code Python** : 41 600
- **Tests** : 66 (objectif : 149 - 4 phases)
- **Couverture** : 41% (objectif : 80%)
- **Commits** : 100+ (depuis octobre 2024)

---

## 🔗 Liens Externes

- **Dépôt GitHub** : [jmFschneider/Observations_Nids](https://github.com/jmFschneider/Observations_Nids)
- **Issues** : [Signaler un bug](https://github.com/jmFschneider/Observations_Nids/issues)
- **Django Docs** : [Documentation officielle](https://docs.djangoproject.com/)
- **Material for MkDocs** : [Documentation](https://squidfunk.github.io/mkdocs-material/)

---

## 📝 Contribuer

Nous accueillons les contributions ! Pour contribuer :

1. **Fork** le dépôt GitHub
2. Créer une **branche** pour votre fonctionnalité (`git checkout -b feature/ma-fonctionnalite`)
3. **Écrire des tests** pour votre code
4. **Linter** votre code (`ruff check --fix .`)
5. **Commiter** vos changements (`git commit -m "feat: description"`)
6. **Pousser** vers votre fork (`git push origin feature/ma-fonctionnalite`)
7. Créer une **Pull Request**

**Standards de commit** :
- `feat:` - Nouvelle fonctionnalité
- `fix:` - Correction de bug
- `docs:` - Documentation
- `test:` - Tests
- `refactor:` - Refactoring
- `chore:` - Maintenance

---

## 🆘 Besoin d'aide ?

- **Documentation** : Utilisez la recherche (en haut de cette page)
- **Troubleshooting** : [Guide de dépannage](learning/troubleshooting/README.md)
- **Issues GitHub** : [Poser une question](https://github.com/jmFschneider/Observations_Nids/issues)
- **Documentation Utilisateur** : [Guide pour les utilisateurs finaux](index.md)

---

**Bonne contribution au projet Observations Nids !** 🚀

---

**Documentation créée le** : 24 octobre 2025
**Dernière mise à jour** : 25 octobre 2025
**Version** : 2.0 - Documentation développeur
