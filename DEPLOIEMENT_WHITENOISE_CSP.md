# 🚀 Déploiement WhiteNoise + CSP - Checklist

> Guide de déploiement pour corriger les problèmes de fichiers statiques et CSP en production

## 📋 Résumé des Modifications

### Fichiers Modifiés

1. ✅ **requirements-prod.in** - Ajout de `whitenoise` et `django-csp`
2. ✅ **requirements-prod.txt** - Compilé avec les nouvelles dépendances
3. ✅ **observations_nids/settings.py** - Configuration WhiteNoise et CSP
4. ✅ **docs/deploiement/deploiement_docker.md** - Documentation mise à jour

### Fonctionnalités Ajoutées

- **WhiteNoise** : Service des fichiers statiques avec compression et cache
- **django-csp** : Gestion de la Content Security Policy
- **Support CDN** : Autorisation de Bootstrap, Chart.js, Font Awesome

---

## 🐳 Commandes de Déploiement Docker

### Étape 1 : Sur Votre Machine Locale (Windows)

```powershell
# Les fichiers sont déjà modifiés et prêts
# requirements-prod.txt est déjà compilé avec django-csp==4.0 et whitenoise==6.11.0

# Commiter et pusher les changements
git add .
git commit -m "Ajout de WhiteNoise et django-csp pour la gestion des fichiers statiques et CSP"
git push origin main
```

### Étape 2 : Sur le Serveur Pilote (Production)

```bash
cd /chemin/vers/observations_nids/docker

# 1. Récupérer les changements
git pull

# 2. Arrêter les services
docker compose down

# 3. Reconstruire l'image web avec les nouvelles dépendances
docker compose build --no-cache web

# 4. Redémarrer tous les services
docker compose up -d

# 5. Vérifier que les services sont démarrés
docker compose ps

# 6. Vérifier que whitenoise et django-csp sont installés
docker compose exec web pip list | grep -E "(whitenoise|django-csp)"

# 7. Collecter les fichiers statiques avec WhiteNoise
docker compose exec web python manage.py collectstatic --noinput --clear

# 8. Vérifier les logs
docker compose logs -f web
```

### Étape 3 : Vérification

```bash
# Tester l'accès au site
curl https://pilote.observation-nids.meteo-poelley50.fr/

# Vérifier les fichiers statiques
curl https://pilote.observation-nids.meteo-poelley50.fr/static/Observations/css/styles.css

# Accéder à la page de statistiques dans le navigateur
# https://pilote.observation-nids.meteo-poelley50.fr/statistiques/general/
```

---

## ✅ Résultats Attendus

### Avant (Problèmes)

- ❌ Fichiers CSS non chargés en production (`DEBUG=False`)
- ❌ Erreurs CSP bloquant Bootstrap, Chart.js, Font Awesome
- ❌ Page sans style, graphiques non affichés

### Après (Corrections)

- ✅ Fichiers statiques servis par WhiteNoise
- ✅ Noms de fichiers avec hash (ex: `styles.5f097d5b6bbd.css`)
- ✅ Compression Gzip + Brotli automatique
- ✅ Headers de cache optimaux
- ✅ CDN autorisés par la CSP
- ✅ Bootstrap, Chart.js, Font Awesome fonctionnent
- ✅ Graphiques de statistiques affichés

---

## 🔍 Diagnostic en Cas de Problème

### Vérifier WhiteNoise

```bash
# Dans le container
docker compose exec web python -c "import whitenoise; print(whitenoise.__version__)"

# Vérifier les fichiers collectés
docker compose exec web ls -lah /app/staticfiles/
```

### Vérifier django-csp

```bash
# Dans le container
docker compose exec web python -c "import csp; print(csp.__version__)"

# Vérifier le middleware dans settings
docker compose exec web python manage.py shell -c "from django.conf import settings; print('CSP' in str(settings.MIDDLEWARE))"
```

### Vérifier les Headers CSP

```bash
# Tester les headers HTTP
curl -I https://pilote.observation-nids.meteo-poelley50.fr/statistiques/general/
```

Vous devriez voir :
```
Content-Security-Policy: default-src 'self'; script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; ...
```

### Logs à Surveiller

```bash
# Logs Django
docker compose logs -f web

# Logs Nginx
docker compose logs -f nginx

# Logs en temps réel
docker compose logs -f
```

---

## 📚 Configuration CSP Détaillée

Dans `settings.py`, la CSP est configurée ainsi :

```python
# Content Security Policy (CSP) Configuration
CSP_DEFAULT_SRC = ("'self'",)
CSP_SCRIPT_SRC = (
    "'self'",
    "'unsafe-inline'",  # Scripts inline dans les templates
    "https://cdn.jsdelivr.net",  # Bootstrap et Chart.js
)
CSP_STYLE_SRC = (
    "'self'",
    "'unsafe-inline'",  # Styles inline
    "https://cdn.jsdelivr.net",  # Bootstrap
    "https://cdnjs.cloudflare.com",  # Font Awesome
)
CSP_FONT_SRC = (
    "'self'",
    "https://cdnjs.cloudflare.com",  # Font Awesome fonts
)
CSP_IMG_SRC = (
    "'self'",
    "data:",  # Images inline base64
)
CSP_CONNECT_SRC = ("'self'",)
```

### Ajouter d'Autres CDN

Si vous devez ajouter un nouveau CDN à l'avenir :

1. Identifiez le domaine (ex: `https://unpkg.com`)
2. Ajoutez-le à la directive appropriée dans `settings.py`
3. Redéployez avec `docker compose restart web`

---

## 🔒 Sécurité

### Points de Vigilance

- ✅ `'unsafe-inline'` est nécessaire pour les scripts/styles inline dans les templates Django
- ✅ Les CDN sont limités à des sources de confiance (jsdelivr, cloudflare)
- ✅ Les images `data:` URI sont autorisées pour les favicons
- ✅ La directive `default-src 'self'` bloque tout le reste par défaut

### Recommandations

- 📝 Documentez tout nouveau CDN ajouté
- 🔍 Surveillez les erreurs CSP dans la console navigateur
- 🔐 En production finale, envisagez de servir les bibliothèques localement plutôt que via CDN

---

## 📞 Support

En cas de problème :

1. Vérifiez les logs : `docker compose logs -f web`
2. Testez en local d'abord avec `DEBUG=False`
3. Consultez la documentation : `/static/docs/index.html`
4. Ouvrez un ticket dans Helpdesk

---

**Date de création** : 19 janvier 2026  
**Version** : 1.0.0  
**Environnement** : Docker Compose (Pilote/Production)
