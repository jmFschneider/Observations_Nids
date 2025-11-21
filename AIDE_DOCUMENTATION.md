# 📚 Documentation d'aide utilisateur - Guide complet

## ✅ Ce qui a été fait

### 1. Lien "Aide" dans le menu latéral

✅ **Ajouté dans `templates/base.html` (ligne 183)**
- Le lien "Aide" ouvre maintenant la documentation dans un nouvel onglet
- En développement : redirige vers `http://127.0.0.1:8001/`
- En production : redirige vers `/static/docs/index.html`

### 2. Vue Django pour la redirection

✅ **Créée dans `observations/views/views_home.py`**
- Fonction `aide_view()` qui gère la redirection
- Détecte automatiquement l'environnement (DEBUG vs Production)

✅ **Route ajoutée dans `observations/urls.py`**
- URL : `/aide/`
- Name : `observations:aide`

### 3. Configuration MkDocs

✅ **Fichier `docs/mkdocs.yml`**
- Configuration complète avec thème Material
- Navigation structurée
- `docs_dir: utilisateurs` (les fichiers Markdown sont dans ce dossier)
- `site_dir: ../site-user` (build temporaire)

### 4. Documentation complète

✅ **7 fichiers Markdown créés/modifiés** :
1. `README.md` - Page d'accueil moderne ✨
2. `00_guide_rapide.md` - Démarrage en 5 minutes ✨
3. `01_navigation_generale.md` - Navigation complète ✅
4. `02_saisie_nouvelle_observation.md` - Guide de saisie ✅
5. `03_correction_transcription.md` - Guide de transcription ✅
6. `04_support_tickets.md` - Support et tickets ✅
7. `05_glossaire.md` - Glossaire complet ✨

### 5. Scripts de déploiement

✅ **Créés** :
- `scripts/build_docs.sh` - Script de build automatique
- `docs/README_DEPLOIEMENT.md` - Guide de déploiement complet

### 6. Configuration Git

✅ **`.gitignore` mis à jour**
- `site-user/` ajouté (builds temporaires)
- `staticfiles/` reste ignoré (sera créé en prod)

---

## 🚀 Utilisation

### En développement (votre PC)

1. **Démarrer le serveur MkDocs** :
   ```bash
   cd docs
   mkdocs serve --config-file=mkdocs.yml
   ```
   → Accessible sur `http://127.0.0.1:8001/`

2. **Démarrer Django** :
   ```bash
   python manage.py runserver
   ```

3. **Tester le lien "Aide"** :
   - Se connecter à l'application : `http://127.0.0.1:8000/`
   - Cliquer sur "Aide" dans le menu latéral
   - Un nouvel onglet s'ouvre avec la documentation

### En production (Raspberry Pi)

#### Étape 1 : Builder la documentation

Sur votre PC de développement :

```bash
# Option automatique
bash scripts/build_docs.sh

# Option manuelle
cd docs
mkdocs build --config-file=mkdocs.yml --clean
mkdir -p ../staticfiles/docs
cp -r ../site-user/* ../staticfiles/docs/
```

#### Étape 2 : Committer les changements

```bash
git add docs/ staticfiles/docs/ scripts/ templates/ observations/
git commit -m "📚 Ajout de la documentation d'aide utilisateur"
git push
```

#### Étape 3 : Déployer sur le Raspberry Pi

```bash
# Se connecter au Raspberry Pi
ssh pi@<adresse-ip>

# Aller dans le dossier du projet
cd /chemin/vers/observations_nids

# Récupérer les changements
git pull

# Collecter les fichiers statiques
source venv/bin/activate
python manage.py collectstatic --noinput

# Redémarrer Gunicorn
sudo systemctl restart gunicorn
```

#### Étape 4 : Vérifier

- Se connecter à l'application en production
- Cliquer sur "Aide" dans le menu
- La documentation doit s'ouvrir

---

## 🔧 Configuration Apache (Production)

Assurez-vous que votre configuration Apache sert les fichiers statiques :

```apache
<VirtualHost *:80>
    ServerName votre-domaine.fr

    # Servir les fichiers statiques
    Alias /static/ /chemin/vers/observations_nids/staticfiles/

    <Directory /chemin/vers/observations_nids/staticfiles>
        Require all granted
    </Directory>

    # Proxy vers Gunicorn
    ProxyPass /static/ !
    ProxyPass / http://127.0.0.1:8000/
    ProxyPassReverse / http://127.0.0.1:8000/
</VirtualHost>
```

**Important** : La ligne `ProxyPass /static/ !` empêche Apache de proxifier les requêtes `/static/` vers Gunicorn.

---

## 📝 Modifier la documentation

### Ajouter/Modifier une page

1. **Éditer le fichier Markdown** dans `docs/utilisateurs/`
   ```bash
   vim docs/utilisateurs/02_saisie_nouvelle_observation.md
   ```

2. **Tester localement** :
   ```bash
   cd docs
   mkdocs serve --config-file=mkdocs.yml
   # Ouvrir http://127.0.0.1:8001/
   ```

3. **Builder pour production** :
   ```bash
   bash scripts/build_docs.sh
   ```

4. **Committer et déployer** :
   ```bash
   git add docs/ staticfiles/docs/
   git commit -m "📚 Mise à jour : [description]"
   git push
   # Puis déployer sur le Raspberry Pi
   ```

### Ajouter une nouvelle page au menu

1. **Créer le fichier Markdown** dans `docs/utilisateurs/`

2. **Ajouter au menu** dans `docs/mkdocs.yml` :
   ```yaml
   nav:
     - '🏠 Accueil': 'README.md'
     - '⚡ Démarrage Rapide': '00_guide_rapide.md'
     - '📖 Guides Utilisateur':
       - 'Navigation Générale': '01_navigation_generale.md'
       - 'Votre nouvelle page': 'nouvelle_page.md'  # ← Ici
   ```

3. **Tester, builder, déployer** (étapes ci-dessus)

---

## 🐛 Dépannage

### Le lien "Aide" ne fonctionne pas en développement

**Vérifier que MkDocs tourne** :
```bash
# Terminal 1
cd docs
mkdocs serve --config-file=mkdocs.yml

# Terminal 2
python manage.py runserver
```

**Vérifier l'URL** :
- Le lien devrait rediriger vers `http://127.0.0.1:8001/`

### Le lien "Aide" donne 404 en production

**Vérifier les fichiers statiques** :
```bash
ls -la staticfiles/docs/
# Doit contenir index.html, css/, js/, etc.
```

**Collecter les statiques** :
```bash
python manage.py collectstatic --noinput
```

**Vérifier Apache** :
```bash
# Voir les logs Apache
sudo tail -f /var/log/apache2/error.log
sudo tail -f /var/log/apache2/access.log
```

### Erreur de build MkDocs

**Extensions manquantes** :
```bash
pip install mkdocs mkdocs-material pymdown-extensions
```

**Liens cassés** :
```bash
cd docs
mkdocs build --config-file=mkdocs.yml --strict
# Affichera toutes les erreurs de liens
```

---

## 📊 Structure complète

```
observations_nids/
├── docs/
│   ├── mkdocs.yml                   # Config MkDocs
│   ├── README_DEPLOIEMENT.md        # Guide de déploiement
│   └── utilisateurs/                # Documentation Markdown
│       ├── README.md                # Page d'accueil
│       ├── 00_guide_rapide.md
│       ├── 01_navigation_generale.md
│       ├── 02_saisie_nouvelle_observation.md
│       ├── 03_correction_transcription.md
│       ├── 04_support_tickets.md
│       ├── 05_glossaire.md
│       ├── CAPTURES_ECRAN_A_AJOUTER.md
│       ├── stylesheets/
│       └── javascripts/
├── site-user/                       # Build MkDocs (ignoré par git)
├── staticfiles/docs/                # Documentation buildée pour prod
├── scripts/
│   └── build_docs.sh                # Script de build auto
├── templates/
│   └── base.html                    # Menu avec lien "Aide"
├── observations/
│   ├── urls.py                      # Route /aide/
│   └── views/
│       └── views_home.py            # Vue aide_view()
└── AIDE_DOCUMENTATION.md            # Ce fichier
```

---

## ✨ Prochaines étapes

### À faire maintenant

1. ✅ **Tester en local** : Vérifier que le lien "Aide" fonctionne
2. ✅ **Builder la documentation** : `bash scripts/build_docs.sh`
3. ✅ **Committer** : Enregistrer tous les changements

### À faire plus tard

1. **Ajouter des captures d'écran** : Suivre `docs/utilisateurs/CAPTURES_ECRAN_A_AJOUTER.md`
2. **Tester en production** : Déployer sur le Raspberry Pi
3. **Créer des vidéos tutorielles** (optionnel)
4. **Recueillir les retours utilisateurs**

---

## 📚 Ressources

- [Documentation MkDocs](https://www.mkdocs.org/)
- [Material for MkDocs](https://squidfunk.github.io/mkdocs-material/)
- [Guide Markdown](https://www.markdownguide.org/)

---

**Résumé** :

✅ Lien "Aide" dans le menu latéral
✅ Vue Django avec redirection automatique (dev/prod)
✅ Documentation complète et structurée
✅ Scripts de build et déploiement
✅ Configuration Apache documentée

**Le système est prêt à être déployé en production !** 🎉

---

*Dernière mise à jour : Novembre 2025*
