# Déploiement de la documentation utilisateur

## 📖 Vue d'ensemble

La documentation utilisateur est construite avec **MkDocs** et le thème **Material**.

- **En développement** : Le serveur MkDocs tourne sur `http://127.0.0.1:8001`
- **En production** : Les fichiers statiques sont servis par Apache via `/static/docs/`

---

## 🔧 Développement local

### Prérequis

```bash
pip install -r requirements-dev.txt
```

### Mode 1 : Serveur MkDocs (développement de la doc)

**Quand l'utiliser** : Vous modifiez la documentation et voulez voir les changements en temps réel.

```bash
# Terminal 1 : Serveur MkDocs
cd docs
mkdocs serve --config-file=mkdocs.yml

# Terminal 2 : Serveur Django
python manage.py runserver
```

La documentation sera accessible sur : `http://127.0.0.1:8001`
Le lien "Aide" dans l'application redirigera automatiquement vers ce serveur.

**Modifications** :
- Les fichiers Markdown sont dans `docs/utilisateurs/`
- La configuration est dans `docs/mkdocs.yml`
- Les modifications sont détectées automatiquement (hot reload)

### Mode 2 : Fichiers statiques (test environnement pilote/prod)

**Quand l'utiliser** : Vous voulez tester le comportement exact de la production.

```bash
# 1. Builder la documentation
bash scripts/build_docs.sh

# 2. Configurer l'environnement pour utiliser les fichiers statiques
echo "MKDOCS_USE_STATIC=True" >> .env

# 3. Lancer Django
python manage.py runserver

# 4. Tester : Le lien "Aide" redirigera vers /static/docs/
```

Pour revenir au mode serveur MkDocs :
```bash
# Retirer ou commenter la ligne dans .env
# MKDOCS_USE_STATIC=True
```

---

## 🚀 Déploiement en production

### Étape 1 : Builder la documentation

Sur votre machine de développement :

```bash
# Option 1 : Script automatique
bash scripts/build_docs.sh

# Option 2 : Manuel
cd docs
mkdocs build --config-file=mkdocs.yml --clean
mkdir -p ../staticfiles/docs
cp -r ../site-user/* ../staticfiles/docs/
```

### Étape 2 : Vérifier le build

```bash
ls -la staticfiles/docs/
# Vous devriez voir : index.html, css/, js/, etc.
```

### Étape 3 : Committer et déployer

```bash
git add staticfiles/docs/
git commit -m "📚 Mise à jour de la documentation utilisateur"
git push
```

### Étape 4 : Sur le Raspberry Pi (Pilote/Production)

```bash
# Se connecter au Raspberry Pi
ssh pi@<adresse-ip>

# Aller dans le dossier du projet
cd /path/to/observations_nids

# Récupérer les changements
git pull

# Activer l'environnement virtuel
source venv/bin/activate

# Collecter les fichiers statiques
python manage.py collectstatic --noinput

# Redémarrer Gunicorn
sudo systemctl restart gunicorn
```

**Important** : Sur le Raspberry Pi, assurez-vous que `DEBUG=False` dans le fichier `.env` (ou configuration production). La variable `MKDOCS_USE_STATIC` n'est pas nécessaire car la documentation sera automatiquement servie depuis `/static/docs/` quand `DEBUG=False`.

---

## 🌐 Configuration Apache

Apache doit servir les fichiers statiques depuis `staticfiles/docs/`.

### Exemple de configuration Apache

```apache
# Dans votre VirtualHost
Alias /static/ /path/to/observations_nids/staticfiles/

<Directory /path/to/observations_nids/staticfiles>
    Require all granted
</Directory>
```

### Vérification

Une fois déployé, la documentation sera accessible via :
- **Lien "Aide" dans le menu** : Redirige vers `/static/docs/index.html`
- **URL directe** : `https://votre-domaine.fr/static/docs/`

---

## 📝 Structure des fichiers

```
observations_nids/
├── docs/
│   ├── mkdocs.yml              # Configuration MkDocs
│   ├── utilisateurs/           # Documentation Markdown
│   │   ├── README.md
│   │   ├── 00_guide_rapide.md
│   │   ├── 01_navigation_generale.md
│   │   ├── 02_saisie_nouvelle_observation.md
│   │   ├── 03_correction_transcription.md
│   │   ├── 04_support_tickets.md
│   │   ├── 05_glossaire.md
│   │   ├── stylesheets/
│   │   └── javascripts/
│   └── README_DEPLOIEMENT.md   # Ce fichier
├── site-user/                  # Build temporaire (ignoré par git)
├── staticfiles/
│   └── docs/                   # Documentation buildée pour production
└── scripts/
    └── build_docs.sh           # Script de build automatique
```

---

## 🔄 Workflow complet

### 1. Modifier la documentation

Éditez les fichiers dans `docs/utilisateurs/` :
```bash
# Exemple
vim docs/utilisateurs/02_saisie_nouvelle_observation.md
```

### 2. Tester localement

```bash
cd docs
mkdocs serve --config-file=mkdocs.yml
# Ouvrir http://127.0.0.1:8001
```

### 3. Builder pour production

```bash
bash scripts/build_docs.sh
```

### 4. Vérifier le build

```bash
# Ouvrir staticfiles/docs/index.html dans un navigateur
```

### 5. Déployer

```bash
git add docs/ staticfiles/docs/
git commit -m "📚 Mise à jour documentation : [description]"
git push

# Sur le serveur
ssh pi@raspberry
cd /path/to/observations_nids
git pull
python manage.py collectstatic --noinput
```

---

## ⚠️ Important

### Fichiers à ne PAS committer

`.gitignore` doit contenir :
```
site-user/
```

### Fichiers à committer

```
docs/utilisateurs/
docs/mkdocs.yml
staticfiles/docs/
scripts/build_docs.sh
```

---

## 🐛 Dépannage

### Le serveur MkDocs ne démarre pas

```bash
# Vérifier les dépendances
pip list | grep mkdocs

# Réinstaller si nécessaire
pip install mkdocs mkdocs-material pymdown-extensions
```

### La documentation n'apparaît pas en production

1. Vérifier que les fichiers sont dans `staticfiles/docs/`
2. Vérifier que `collectstatic` a été exécuté
3. Vérifier la configuration Apache
4. Vérifier les permissions des fichiers

```bash
ls -la staticfiles/docs/
# Les fichiers doivent être lisibles par www-data
```

### Erreurs de build MkDocs

```bash
# Vérifier la configuration
mkdocs serve --config-file=docs/mkdocs.yml --verbose

# Vérifier les liens cassés
mkdocs build --config-file=docs/mkdocs.yml --strict
```

---

## 📚 Ressources

- [Documentation MkDocs](https://www.mkdocs.org/)
- [Material for MkDocs](https://squidfunk.github.io/mkdocs-material/)
- [PyMdown Extensions](https://facelessuser.github.io/pymdown-extensions/)

---

*Dernière mise à jour : Novembre 2025*
