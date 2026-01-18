# 🐦 Observations Nids

> **Application web de gestion des fiches d'observation de nidification d'oiseaux**

---

## 🎯 Présentation

**Observations Nids** est une application Django permettant de :

- 📝 **Saisir** des fiches d'observation de nidification
- 🤖 **Transcrire** automatiquement des fiches papier via OCR (Google Gemini)
- ✅ **Valider** et corriger les fiches via un workflow de review
- 📊 **Analyser** les données ornithologiques

L'application est conçue pour le **Groupe Ornithologique Normand (GONM)** et permet de numériser des décennies de fiches papier.

---

## ✨ Fonctionnalités Principales

### 📋 Gestion des Fiches

- Saisie manuelle de fiches d'observation
- Formulaires dynamiques avec autocomplétion (espèces, communes)
- Gestion des observations multiples par fiche
- Historique complet des modifications

### 🤖 Transcription OCR

- Upload d'images de fiches papier
- Transcription automatique via Google Gemini
- Traitement batch avec suivi de progression
- Évaluation de la qualité des transcriptions

### ✅ Workflow de Correction

- Statuts : Nouveau → En édition → En correction → Validé
- Système de verrouillage par reviewer
- Fusion des observateurs en doublon
- Calcul automatique du pourcentage de complétion

### 👥 Gestion des Utilisateurs

- Rôles : Observateur, Reviewer, Administrateur
- Inscription publique avec validation
- Notifications internes

---

## 🛠️ Stack Technique

| Composant | Technologie |
|-----------|-------------|
| **Backend** | Django 6.0, Python 3.11+ |
| **Base de données** | MariaDB 10.11 / MySQL |
| **Cache & Broker** | Redis 7 |
| **Tâches async** | Celery 5.6 |
| **OCR** | Google Gemini API |
| **Serveur web** | Gunicorn + Nginx |
| **Conteneurisation** | Docker Compose |

---

## 🚀 Quick Start

### Prérequis

- Python 3.11+
- Redis
- MariaDB/MySQL
- Clé API Google Gemini (pour l'OCR)

### Installation Rapide (Docker)

```bash
# Cloner le projet
git clone <repository-url>
cd observations_nids

# Configurer les variables d'environnement
cp docker/.env.example docker/.env
# Éditer docker/.env avec vos paramètres

# Lancer les services
cd docker
docker-compose up -d

# Accéder à l'application
# http://localhost:8010
```

### Installation Manuelle

```bash
# Créer l'environnement virtuel
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate     # Windows

# Installer les dépendances
pip install -r requirements-base.txt

# Configurer la base de données
python manage.py migrate

# Créer un superutilisateur
python manage.py createsuperuser

# Lancer le serveur de développement
python manage.py runserver
```

---

## 📁 Structure du Projet

```
observations_nids/
├── observations/       # 📋 Application principale (fiches)
├── taxonomy/          # 🐦 Espèces et classification
├── geo/               # 🗺️ Communes et géolocalisation
├── accounts/          # 👥 Utilisateurs et authentification
├── review/            # ✅ Validation des fiches
├── audit/             # 📜 Historique des modifications
├── ingest/            # 📥 Import des transcriptions
├── ocr/               # 🤖 Transcription OCR Gemini
├── core/              # ⚙️ Utilitaires partagés
├── docker/            # 🐳 Configuration Docker
└── docs/              # 📚 Documentation
```

---

## 📚 Documentation

| Document | Description |
|----------|-------------|
| [Architecture](./architecture.md) | Architecture technique du projet |
| [Applications](./applications/) | Documentation des 9 applications Django |
| [Plan Directeur](./docs_todo.md) | État d'avancement de la documentation |

### Applications Documentées

- [observations](./applications/observations.md) - Fiches d'observation
- [taxonomy](./applications/taxonomy.md) - Espèces et codes GONM
- [geo](./applications/geo.md) - Communes et géolocalisation
- [accounts](./applications/accounts.md) - Utilisateurs et rôles
- [review](./applications/review.md) - Validation
- [audit](./applications/audit.md) - Historique
- [ingest](./applications/ingest.md) - Import JSON
- [ocr](./applications/ocr.md) - Transcription OCR
- [core](./applications/core.md) - Utilitaires

---

## 🔧 Configuration

### Variables d'Environnement

| Variable | Description | Exemple |
|----------|-------------|---------|
| `SECRET_KEY` | Clé secrète Django | `your-secret-key` |
| `DEBUG` | Mode debug | `False` |
| `DB_NAME` | Nom de la base | `observations_db` |
| `DB_USER` | Utilisateur BDD | `obs_user` |
| `DB_PASSWORD` | Mot de passe BDD | `***` |
| `REDIS_HOST` | Hôte Redis | `localhost` |
| `GEMINI_API_KEY` | Clé API Gemini | `AIza...` |

---

## 🧪 Tests

```bash
# Lancer tous les tests
python manage.py test

# Lancer les tests d'une application
python manage.py test observations

# Avec couverture
coverage run manage.py test
coverage report
```

---

## 📄 Licence

Ce projet est développé pour le Groupe Ornithologique Normand (GONM).

---

## 🤝 Contribution

1. Fork le projet
2. Créer une branche (`git checkout -b feature/nouvelle-fonctionnalite`)
3. Commit (`git commit -m 'Ajout nouvelle fonctionnalité'`)
4. Push (`git push origin feature/nouvelle-fonctionnalite`)
5. Ouvrir une Pull Request
