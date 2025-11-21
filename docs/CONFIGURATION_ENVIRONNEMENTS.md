# ⚙️ Configuration des environnements - Documentation MkDocs

## 📋 Résumé

Le lien "Aide" dans l'application redirige intelligemment vers la documentation selon l'environnement :

| Environnement | DEBUG | MKDOCS_USE_STATIC | Comportement |
|---------------|-------|-------------------|--------------|
| **Dev (modification doc)** | True | Non défini | → `http://127.0.0.1:8001/` (serveur MkDocs live) |
| **Dev (test prod)** | True | `True` | → `/static/docs/index.html` (fichiers statiques) |
| **Pilote** | False | Non nécessaire | → `/static/docs/index.html` (fichiers statiques) |
| **Production** | False | Non nécessaire | → `/static/docs/index.html` (fichiers statiques) |

---

## 🔧 Configuration par environnement

### 1. Développement local (modification de la documentation)

**Objectif** : Modifier la documentation avec rechargement automatique (hot reload)

**Configuration `.env`** :
```env
DEBUG=True
# MKDOCS_USE_STATIC non défini ou commenté
```

**Commandes** :
```bash
# Terminal 1 : Serveur MkDocs
cd docs
mkdocs serve --config-file=mkdocs.yml

# Terminal 2 : Serveur Django
python manage.py runserver
```

**Résultat** :
- Documentation accessible sur `http://127.0.0.1:8001/`
- Lien "Aide" → Redirige vers le serveur MkDocs
- Modifications Markdown visibles immédiatement

---

### 2. Développement local (test comportement production)

**Objectif** : Tester que la documentation fonctionne comme en production/pilote

**Configuration `.env`** :
```env
DEBUG=True
MKDOCS_USE_STATIC=True
```

**Commandes** :
```bash
# Builder la documentation
bash scripts/build_docs.sh

# Lancer Django
python manage.py runserver
```

**Résultat** :
- Documentation buildée dans `staticfiles/docs/`
- Lien "Aide" → Redirige vers `/static/docs/index.html`
- Comportement identique au pilote/production

---

### 3. Environnement Pilote (Raspberry Pi)

**Objectif** : Environnement de test proche de la production

**Configuration `.env`** :
```env
DEBUG=False
ENVIRONMENT=pilote
# MKDOCS_USE_STATIC non nécessaire
```

**Déploiement** :
```bash
# Sur votre PC
bash scripts/build_docs.sh
git add staticfiles/docs/
git commit -m "📚 Mise à jour documentation"
git push

# Sur le Raspberry Pi
ssh pi@<ip>
cd /path/to/observations_nids
git pull
source venv/bin/activate
python manage.py collectstatic --noinput
sudo systemctl restart gunicorn
```

**Résultat** :
- Documentation servie par Apache depuis `/static/docs/`
- Lien "Aide" → Redirige vers `/static/docs/index.html`
- MkDocs N'EST PAS installé sur le serveur

---

### 4. Environnement Production

**Identique au pilote** avec :

**Configuration `.env`** :
```env
DEBUG=False
ENVIRONMENT=production
```

---

## 🎯 Pourquoi cette approche ?

### Avantages

1. **Développement rapide** : Hot reload pour modifier la documentation
2. **Tests réalistes** : Possibilité de tester le comportement exact de production
3. **Pas de dépendances prod** : MkDocs uniquement en développement
4. **Performance** : Fichiers statiques servis directement par Apache
5. **Cohérence** : Environnement pilote identique à production

### Compromis

- **Build manuel** : Il faut builder la doc avant de déployer
- **Deux terminaux** : En dev, besoin de MkDocs + Django

---

## 📝 Checklist de déploiement

### Avant de pousser en production/pilote

- [ ] Modifier la documentation dans `docs/utilisateurs/`
- [ ] Tester localement avec MkDocs : `mkdocs serve --config-file=docs/mkdocs.yml`
- [ ] Builder la documentation : `bash scripts/build_docs.sh`
- [ ] Vérifier le build : Ouvrir `staticfiles/docs/index.html` dans un navigateur
- [ ] Tester en mode statique local : `MKDOCS_USE_STATIC=True` dans `.env`
- [ ] Committer : `git add docs/ staticfiles/docs/`
- [ ] Pousser : `git push`

### Sur le serveur (pilote/production)

- [ ] Pull : `git pull`
- [ ] Collecter les statiques : `python manage.py collectstatic --noinput`
- [ ] Redémarrer : `sudo systemctl restart gunicorn`
- [ ] Tester : Cliquer sur "Aide" dans l'application

---

## 🐛 Dépannage

### Le lien "Aide" redirige toujours vers 127.0.0.1:8001 en production

**Cause** : `DEBUG=True` sur le serveur

**Solution** :
```bash
# Vérifier .env sur le serveur
cat .env | grep DEBUG
# Devrait être DEBUG=False

# Si DEBUG=True, corriger
echo "DEBUG=False" >> .env
sudo systemctl restart gunicorn
```

---

### En dev, je veux tester les fichiers statiques mais ça redirige vers MkDocs

**Cause** : `MKDOCS_USE_STATIC` pas défini

**Solution** :
```bash
echo "MKDOCS_USE_STATIC=True" >> .env
python manage.py runserver
```

---

### Les changements dans la documentation n'apparaissent pas en production

**Cause** : Oubli de builder avant de committer

**Solution** :
```bash
# Builder la doc
bash scripts/build_docs.sh

# Vérifier que staticfiles/docs/ est modifié
git status

# Committer si nécessaire
git add staticfiles/docs/
git commit -m "📚 Build documentation"
git push

# Sur le serveur
git pull
python manage.py collectstatic --noinput
```

---

## 💡 Bonnes pratiques

1. **En dev** : Laissez `MKDOCS_USE_STATIC` commenté pour le hot reload
2. **Avant commit** : Buildez toujours la doc avec `build_docs.sh`
3. **En pilote/prod** : `DEBUG=False` obligatoire
4. **Tests** : Testez en mode statique local avant de déployer
5. **Git** : Committez toujours `staticfiles/docs/` après un build

---

*Dernière mise à jour : Novembre 2025*
