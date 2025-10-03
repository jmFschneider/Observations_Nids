# Quick Start - Démarrage rapide

## Prérequis

Avant de commencer, assurez-vous d'avoir installé :
- **Python 3.11+** 
- **pip** (gestionnaire de paquets Python)
- **Redis** (pour Celery)
- **Git**
- Un éditeur de code (VS Code, PyCharm, etc.)

---

## Installation en 5 minutes

### 1. Cloner et configurer l'environnement

```bash
# Cloner le projet
git clone <url-du-repo>
cd observations_nids

# Créer un environnement virtuel
python -m venv venv

# Activer l'environnement virtuel
# Sur Linux/Mac :
source venv/bin/activate
# Sur Windows :
venv\Scripts\activate

# Installer les dépendances
pip install -r requirements.txt
```

### 2. Configurer les variables d'environnement

```bash
# Copier le fichier d'exemple
cp .env.example .env

# Éditer le fichier .env avec vos valeurs
# Au minimum, définir :
# - SECRET_KEY (générer une clé sécurisée)
# - DEBUG=True (pour le développement)
```

**Générer une SECRET_KEY :**
```python
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

**Exemple de configuration .env minimale :**
```bash
SECRET_KEY=votre-cle-generee-ici
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

DATABASE_ENGINE=sqlite3
DATABASE_NAME=db.sqlite3

CELERY_BROKER_URL=redis://127.0.0.1:6379/0

SESSION_COOKIE_AGE=3600
USE_DEBUG_TOOLBAR=True
```

### 3. Initialiser la base de données

```bash
# Appliquer les migrations
python manage.py migrate

# Créer un superutilisateur
python manage.py createsuperuser
# Suivez les instructions : entrez email, nom, prénom, mot de passe
```

### 4. Charger les données de test (optionnel)

```bash
# Charger les espèces d'oiseaux
python manage.py loaddata taxonomy/fixtures/especes.json

# Charger des utilisateurs de test
python manage.py loaddata accounts/fixtures/utilisateurs_test.json
```

> **Note :** Si ces fixtures n'existent pas encore, vous pouvez les créer plus tard ou saisir les données manuellement via l'interface admin.

### 5. Démarrer les services

Vous aurez besoin de **3 terminaux** ouverts simultanément :

**Terminal 1 - Serveur Django :**
```bash
python manage.py runserver
```

**Terminal 2 - Redis (pour Celery) :**
```bash
redis-server
```

**Terminal 3 - Worker Celery (pour transcription OCR) :**
```bash
celery -A observations_nids worker --loglevel=info
```

> **Astuce :** Vous pouvez utiliser `tmux` ou `screen` pour gérer plusieurs terminaux facilement.

---

## Premier test

### 1. Accédez à l'application

Ouvrez votre navigateur et allez sur : **http://localhost:8000**

### 2. Connectez-vous

Utilisez les identifiants du superutilisateur créé à l'étape 3.

### 3. Testez l'interface

- **Liste des observations** : http://localhost:8000/observations/liste/
- **Créer une fiche** : http://localhost:8000/observations/nouvelle/
- **Interface de transcription** : http://localhost:8000/transcription/demarrer/
- **Admin Django** : http://localhost:8000/admin/

---

## Vérification de l'installation

Pour vérifier que tout fonctionne correctement :

```bash
# Vérifier la configuration Django
python manage.py check

# Lancer les tests
pytest

# Vérifier que Celery répond
celery -A observations_nids inspect ping
```

Si toutes les commandes s'exécutent sans erreur, votre installation est réussie ! ✅

---

## Problèmes fréquents au démarrage

| Problème | Solution |
|----------|----------|
| `ModuleNotFoundError` | Vérifier que l'environnement virtuel est activé et que les dépendances sont installées : `pip install -r requirements.txt` |
| Erreur de connexion Redis | S'assurer que Redis est démarré : `redis-server`. Vérifier que le port 6379 est libre. |
| Erreur de migration | Réinitialiser la BDD : `rm db.sqlite3` puis `python manage.py migrate` |
| Port 8000 déjà utilisé | Utiliser un autre port : `python manage.py runserver 8001` |
| Erreur Google Vision API | Vérifier que `GOOGLE_APPLICATION_CREDENTIALS` dans `.env` pointe vers le bon fichier JSON de credentials |
| Erreur `SECRET_KEY` | Vérifier que `SECRET_KEY` est définie dans `.env` et qu'elle n'est pas vide |
| Page blanche/erreur 500 | Vérifier les logs dans le terminal du serveur Django. Activer `DEBUG=True` dans `.env` |

### Debug Redis

Si Redis ne démarre pas :
```bash
# Vérifier si Redis est installé
redis-cli --version

# Vérifier si Redis est en cours d'exécution
redis-cli ping
# Doit répondre : PONG
```

### Debug Celery

Si Celery ne fonctionne pas :
```bash
# Vérifier les workers actifs
celery -A observations_nids inspect active

# Voir les tâches en cours
celery -A observations_nids inspect scheduled
```

---

## Structure de développement recommandée

Voici à quoi devrait ressembler votre dossier de projet :

```
observations_nids/
├── venv/                    # Environnement virtuel (git ignored)
├── .env                     # Variables d'environnement (git ignored)
├── .env.example             # Template des variables d'environnement
├── db.sqlite3               # Base de données locale (git ignored)
├── media/                   # Fichiers uploadés (git ignored)
├── staticfiles/             # Fichiers statiques collectés (git ignored)
├── logs/                    # Logs de l'application
├── accounts/                # App gestion utilisateurs
├── audit/                   # App traçabilité
├── core/                    # App utilitaires
├── geo/                     # App localisation
├── ingest/                  # App import de données
├── observations/            # App principale
├── review/                  # App validation
├── taxonomy/                # App taxonomie
├── observations_nids/       # Configuration Django
├── manage.py
├── requirements.txt
└── pytest.ini
```

### Fichiers à ne jamais commiter

Assurez-vous que votre `.gitignore` contient :
```
venv/
.env
*.pyc
__pycache__/
db.sqlite3
media/
staticfiles/
*.log
.DS_Store
```

---

## Prochaines étapes

Une fois l'installation terminée, voici ce que vous devriez faire :

### Pour les développeurs

1. **Lire la documentation architecture** : `Claude/02-architecture.md`
   - Comprendre la structure des applications
   - Explorer les modèles de données
   - Voir les relations entre entités

2. **Explorer le code** :
   - Commencer par `observations/models.py` pour les modèles principaux
   - Regarder `observations/views/` pour comprendre les vues
   - Examiner les templates dans `observations/templates/`

3. **Tester le workflow complet** :
   - Créer une fiche manuellement
   - Tester la transcription OCR (si Google Vision API configurée)
   - Corriger une fiche
   - Valider une observation

4. **Consulter les bonnes pratiques** : `Claude/03-development-guide.md`
   - Standards de code
   - Comment écrire des tests
   - Workflow Git

### Pour Claude (IA)

Avant de m'aider sur ce projet :

1. **Lire la documentation complète** dans le dossier `Claude/`
2. **Comprendre l'architecture** : applications Django et leurs responsabilités
3. **Identifier les modèles centraux** : `FicheObservation`, `Observation`, etc.
4. **Respecter les conventions** : Django best practices, PEP 8, type hints
5. **Toujours lire avant d'éditer** : ne jamais modifier un fichier sans l'avoir lu

---

## Configuration Google Vision API (optionnel)

Si vous souhaitez utiliser la transcription OCR automatique :

### 1. Créer un projet Google Cloud

1. Aller sur https://console.cloud.google.com
2. Créer un nouveau projet
3. Activer l'API "Cloud Vision API"

### 2. Créer des credentials

1. Aller dans "APIs & Services" > "Credentials"
2. Créer un "Service Account"
3. Télécharger le fichier JSON des credentials

### 3. Configurer dans le projet

```bash
# Placer le fichier JSON dans le projet (ne pas commiter !)
mkdir -p config/
mv ~/Downloads/credentials.json config/google-vision-credentials.json

# Ajouter dans .env
echo "GOOGLE_APPLICATION_CREDENTIALS=config/google-vision-credentials.json" >> .env
```

### 4. Tester

```python
# Dans un shell Django
python manage.py shell

from google.cloud import vision
client = vision.ImageAnnotatorClient()
print("Google Vision API configurée avec succès !")
```

---

## Commandes utiles au quotidien

### Développement

```bash
# Démarrer le serveur (avec rechargement auto)
python manage.py runserver

# Shell Django interactif
python manage.py shell

# Shell Django avec imports automatiques (si django-extensions installé)
python manage.py shell_plus
```

### Base de données

```bash
# Créer des migrations
python manage.py makemigrations

# Appliquer les migrations
python manage.py migrate

# Voir l'état des migrations
python manage.py showmigrations

# Accéder à la base de données
python manage.py dbshell
```

### Tests

```bash
# Lancer tous les tests
pytest

# Tests d'une application
pytest observations/tests/

# Tests avec couverture
pytest --cov

# Tests avec sortie détaillée
pytest -v
```

### Données

```bash
# Charger des fixtures
python manage.py loaddata fichier.json

# Créer un dump des données
python manage.py dumpdata app.Model --indent 2 > fichier.json

# Réinitialiser la BDD (DANGER)
python manage.py flush
```

---

## Ressources utiles

### Documentation Django
- [Documentation officielle Django](https://docs.djangoproject.com/)
- [Django Tutorial](https://docs.djangoproject.com/en/stable/intro/tutorial01/)

### Tutoriels Celery
- [First steps with Django](https://docs.celeryproject.org/en/stable/django/first-steps-with-django.html)

### Outils de développement
- [Django Debug Toolbar](https://django-debug-toolbar.readthedocs.io/)
- [pytest-django](https://pytest-django.readthedocs.io/)

---

## Support

### En cas de problème

1. **Vérifier les logs** dans le terminal du serveur Django
2. **Consulter** `Claude/06-troubleshooting.md`
3. **Activer le mode debug** : `DEBUG=True` dans `.env`
4. **Utiliser Django Debug Toolbar** pour analyser les requêtes

### Pour les questions de développement

- Consulter la documentation dans `Claude/`
- Lire le code existant pour comprendre les patterns
- Écrire des tests pour reproduire le problème

---

*Documentation générée pour le projet Observations Nids*  
*Dernière mise à jour : 2025-10-03*  
*Version : 1.0*
