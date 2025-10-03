# Documentation Projet Observations Nids - Guide Claude

Documentation complète du projet organisée par thèmes.

## 📚 Table des matières

### 🚀 [Quick Start - Démarrage rapide](01-quick-start.md)
Installation et configuration en 5 minutes pour commencer à développer.
- Prérequis et installation
- Configuration de base
- Premier démarrage
- Vérification de l'installation

### 🏗️ [Architecture](02-architecture.md)
Structure du projet, applications Django et modèles de données.
- Vue d'ensemble
- Applications et responsabilités
- Modèles principaux
- Relations entre entités

### 💻 [Guide de développement](03-development-guide.md)
Bonnes pratiques, commandes utiles et instructions pour Claude.
- Standards de code
- Commandes Django/Git
- Tests
- Instructions spécifiques pour Claude

### 🔄 [Workflows](04-workflows.md)
Processus métier détaillés de l'application.
- Transcription OCR automatique
- Correction et saisie manuelle
- Système de validation
- Audit et traçabilité

### 🚢 [Déploiement](05-deployment.md)
Configuration production et mise en ligne.
- Configuration serveur
- Base de données PostgreSQL
- Nginx/Gunicorn
- Maintenance

### 🔧 [Troubleshooting](06-troubleshooting.md)
Résolution des problèmes courants.
- Erreurs fréquentes
- Debug
- FAQ technique

## 🎯 Objectifs du projet

**Observations Nids** est une application Django pour la gestion d'observations ornithologiques de nidification.

**Fonctionnalités principales :**
- ✅ Numérisation automatisée par OCR (Google Vision API)
- ✅ Saisie et correction collaborative
- ✅ Workflow de validation avec rôles
- ✅ Traçabilité complète des modifications
- ✅ Contrôle qualité des données

## 📊 Technologies

- **Backend** : Django 4.x, Python 3.11+
- **Base de données** : SQLite (dev) / PostgreSQL (prod)
- **Async** : Celery + Redis
- **OCR** : Google Vision API
- **Frontend** : Bootstrap 5, JavaScript vanilla
- **Tests** : pytest, pytest-django

## 🔗 Liens rapides

- **Serveur local** : http://localhost:8000
- **Admin Django** : http://localhost:8000/admin/
- **Liste observations** : http://localhost:8000/observations/liste/

## 📝 Version

- **Dernière mise à jour** : 2025-10-03
- **Version Django** : 4.x
- **Version Python** : 3.11+

---

*Pour toute question, consultez d'abord le [Troubleshooting](06-troubleshooting.md)*