# Observations Nids

Application Django de gestion et de saisie d'observations ornithologiques de nidification. Ce projet permet de numériser, valider et exploiter des fiches d'observation manuscrites grâce à l'intelligence artificielle.

## Fonctionnalités principales

### Gestion des observations
- **Saisie manuelle** : Interface intuitive pour enregistrer les observations de nidification
- **Transcription automatique** : Numérisation de fiches manuscrites via l'API Google Gemini
- **Géolocalisation** : Calcul automatique des coordonnées GPS et de l'altitude à partir des communes
- **Validation** : Workflow de vérification et correction des données importées

### Gestion taxonomique
- **Référentiel TAXREF** : Intégration de la base de données officielle française des espèces
- **Synchronisation LOF** : Import automatique des données de Faune-France (Liste Ornithologique Française)
- **Liens Oiseaux.net** : Enrichissement automatique avec photos et informations des espèces

### Administration
- **Gestion des utilisateurs** : Inscription, validation, modification et désactivation
- **Système de notifications** : Alertes email pour les demandes de compte
- **Réinitialisation de mot de passe** : Processus sécurisé de récupération de compte
- **Audit** : Traçabilité complète des modifications (qui, quand, quoi)

### Traitement asynchrone
- **Celery + Redis** : Traitement en arrière-plan des tâches lourdes (transcription, géocodage)
- **Monitoring** : Supervision des tâches via Flower

## Technologies

- **Backend** : Django 5.1+, Python 3.11+
- **Base de données** : MariaDB 10.11+
- **Cache & Queue** : Redis 7+
- **Task Queue** : Celery 5+
- **IA** : Google Generative AI (Gemini)
- **Géolocalisation** : Nominatim (OpenStreetMap)
- **Documentation** : MkDocs avec thème Material

## Installation

### Environnement de développement

```bash
# Cloner le repository
git clone https://github.com/jmFschneider/Observations_Nids.git
cd Observations_Nids

# Créer l'environnement virtuel
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate     # Windows

# Installer les dépendances
pip install -r requirements/dev.txt

# Configurer les variables d'environnement
cp .env.example .env
# Éditer .env avec vos clés API

# Initialiser la base de données
python manage.py migrate
python manage.py createsuperuser

# Lancer le serveur de développement
python manage.py runserver
```

Voir la [documentation d'installation détaillée](docs/docs/installation/development.md) pour plus d'informations.

### Production

Voir le [guide de déploiement Raspberry Pi](docs/docs/installation/production.md) pour une installation complète sur serveur.

## Structure du projet

```
observations_nids/
├── accounts/          # Gestion des utilisateurs et authentification
├── audit/             # Traçabilité des modifications
├── core/              # Fonctionnalités communes et utilitaires
├── geo/               # Géolocalisation et géocodage
├── ingest/            # Import et transcription de fiches
├── observations/      # Gestion des observations ornithologiques
├── review/            # Validation et correction des données
├── taxonomy/          # Référentiels taxonomiques
├── docs/              # Documentation MkDocs
├── deployment/        # Scripts de déploiement
└── requirements/      # Dépendances par environnement
```

## Documentation

La documentation complète est disponible dans le dossier `docs/` et peut être consultée via MkDocs :

```bash
mkdocs serve
```

Puis accéder à http://127.0.0.1:8000

## Tests

```bash
# Lancer tous les tests
pytest

# Avec couverture de code
pytest --cov=. --cov-report=html

# Linting et formatage
ruff check .
ruff format .
```

## Contribuer

1. Forker le projet
2. Créer une branche pour votre fonctionnalité (`git checkout -b feature/ma-fonctionnalite`)
3. Commiter vos changements (`git commit -m 'Ajouter ma fonctionnalité'`)
4. Pousser vers la branche (`git push origin feature/ma-fonctionnalite`)
5. Ouvrir une Pull Request

## Licence

Ce projet est un projet personnel à but non lucratif destiné à la gestion d'observations ornithologiques.

## Auteur

Jean-Marc Schneider - [jmFschneider](https://github.com/jmFschneider)

## Remerciements

- **TAXREF** : Référentiel taxonomique officiel français (MNHN)
- **Faune-France** : Plateforme collaborative d'observations naturalistes
- **Oiseaux.net** : Base de données ornithologique francophone
- **Google Generative AI** : API de transcription via Gemini
