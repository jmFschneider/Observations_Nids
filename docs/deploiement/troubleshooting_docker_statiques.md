# 🔧 Troubleshooting Docker & Fichiers Statiques

> Guide de résolution des problèmes courants avec Docker, WhiteNoise et les fichiers statiques (CSS/JS)

---

## 📋 Table des Matières

- [Problèmes Courants](#problèmes-courants)
- [Workflow de Développement](#workflow-de-développement)
- [Gestion du Cache](#gestion-du-cache)
- [Bonnes Pratiques](#bonnes-pratiques)
- [Checklist de Déploiement](#checklist-de-déploiement)
- [Commandes Utiles](#commandes-utiles)

---

## 🐛 Problèmes Courants

### Problème 1 : Modifications JavaScript/CSS Non Prises en Compte

**Symptômes** :
- Les modifications de fichiers JS/CSS ne sont pas visibles dans le navigateur
- L'ancien code continue de s'exécuter malgré les modifications
- Les erreurs JavaScript persistent après correction

**Causes Possibles** :
1. ✏️ Fichier non sauvegardé dans l'éditeur (Cursor/VSCode)
2. 🐳 Image Docker non reconstruite
3. 📦 WhiteNoise n'a pas régénéré le manifeste (`collectstatic` non exécuté)
4. 🌐 Cache navigateur agressif
5. 🔄 Paramètre de version non mis à jour dans les templates

**Solution Rapide** :

```bash
# 1. Sauvegarder le fichier dans l'éditeur (Ctrl+S)

# 2. Copier directement dans le conteneur (développement rapide)
docker cp chemin/local/fichier.js observations_web:/app/chemin/fichier.js

# 3. Régénérer les fichiers statiques
docker compose exec web python manage.py collectstatic --noinput --clear

# 4. Redémarrer le conteneur
docker compose restart web

# 5. Vider le cache navigateur (Ctrl+Shift+R ou Ctrl+Shift+Delete)
```

**Solution Complète (Production)** :

```bash
# 1. Sauvegarder tous les fichiers (Ctrl+S)

# 2. Reconstruire l'image sans cache
cd docker
docker compose build --no-cache web

# 3. Redémarrer avec la nouvelle image
docker compose up -d web

# 4. Attendre que le conteneur démarre (30 secondes)
docker compose logs -f web

# 5. Régénérer les fichiers statiques
docker compose exec web python manage.py collectstatic --noinput --clear

# 6. Vérifier que le fichier est correct dans le conteneur
docker compose exec web cat /app/chemin/fichier.js | head -n 50

# 7. Vider le cache navigateur
```

---

### Problème 2 : Erreur JavaScript "URL constructor: Invalid URL"

**Symptômes** :
```
Uncaught TypeError: URL constructor: undefined is not a valid URL
```

**Cause** :
- Tentative de créer une URL à partir d'une propriété `href` inexistante ou invalide
- Souvent causé par l'utilisation de `querySelectorAll('.classe')` qui retourne des éléments de types différents

**Solution** :

```javascript
// ❌ MAUVAIS : Pas de vérification
const links = document.querySelectorAll('.nav-link');
links.forEach(link => {
    const url = new URL(link.href); // ERREUR si link est un <form> ou <div>
});

// ✅ BON : Vérifications complètes
const links = document.querySelectorAll('.nav-link');
links.forEach(link => {
    // Vérifier que c'est bien un lien <a>
    if (link.tagName !== 'A') {
        return;
    }
    
    // Vérifier que href existe et est valide
    if (!link.href || link.href === '' || link.href === '#') {
        return;
    }
    
    // Utiliser try-catch pour les cas limites
    try {
        const url = new URL(link.href);
        // ... utiliser url
    } catch (e) {
        console.warn('Invalid URL:', link.href, e);
    }
});
```

**Règle d'or** : Toujours vérifier le type et l'existence des propriétés avant de les utiliser.

---

### Problème 3 : Formulaire Sans Bouton Submit

**Symptômes** :
- Cliquer sur un formulaire ne fait rien
- Pas de soumission du formulaire

**Cause** :
- Formulaire sans `<button type="submit">` ou `<input type="submit">`
- Clic sur des éléments qui ne déclenchent pas la soumission

**Solution** :

```html
<!-- ❌ MAUVAIS : Pas de bouton submit -->
<form method="post" action="/logout/" class="nav-link">
    {% csrf_token %}
    <i class="fas fa-sign-out-alt"></i>
    <span>Déconnexion</span>
</form>

<!-- ✅ BON Option 1 : Avec bouton submit -->
<form method="post" action="/logout/" class="nav-link">
    {% csrf_token %}
    <button type="submit" class="btn-link">
        <i class="fas fa-sign-out-alt"></i>
        <span>Déconnexion</span>
    </button>
</form>

<!-- ✅ BON Option 2 : Avec JavaScript onclick -->
<form method="post" action="/logout/" class="nav-link" 
      onclick="this.submit();" style="cursor: pointer;">
    {% csrf_token %}
    <i class="fas fa-sign-out-alt"></i>
    <span>Déconnexion</span>
</form>
```

---

## 🔄 Workflow de Développement

### Modifications de Code Python/Templates

Les templates Django sont rechargés automatiquement en mode développement :

```bash
# Aucune action nécessaire en développement
# En production, redémarrer le conteneur :
docker compose restart web
```

### Modifications de Fichiers Statiques (CSS/JS)

**Option 1 : Développement Rapide** (recommandé pour itérations rapides)

```bash
# 1. Modifier le fichier localement et SAUVEGARDER (Ctrl+S)

# 2. Copier dans le conteneur
docker cp observations/static/Observations/js/fichier.js \
         observations_web:/app/observations/static/Observations/js/fichier.js

# 3. Régénérer les fichiers statiques
docker compose exec web python manage.py collectstatic --noinput --clear

# 4. Redémarrer (optionnel mais recommandé)
docker compose restart web
```

**Option 2 : Rebuild Complet** (recommandé avant commit/production)

```bash
# 1. Sauvegarder tous les fichiers (Ctrl+S)

# 2. Reconstruire l'image
cd docker
docker compose build --no-cache web

# 3. Redémarrer
docker compose up -d web

# 4. Collecter les statiques
docker compose exec web python manage.py collectstatic --noinput --clear
```

### Vérification des Modifications

```bash
# Vérifier le contenu du fichier dans le conteneur
docker compose exec web cat /app/observations/static/Observations/js/sidebar.js | head -n 50

# Vérifier les fichiers collectés
docker compose exec web ls -lh /app/staticfiles/Observations/js/

# Vérifier les logs
docker compose logs -f web
```

---

## 🗂️ Gestion du Cache

### Cache Côté Serveur (Django/WhiteNoise)

**Paramètres de Version dans les Templates** :

```django
<!-- ❌ MAUVAIS : Pas de versioning -->
<script src="{% static 'Observations/js/sidebar.js' %}"></script>

<!-- ✅ BON : Avec paramètre de version -->
<script src="{% static 'Observations/js/sidebar.js' %}?v=20260121"></script>

<!-- ✅ MIEUX : Avec variable dynamique -->
<script src="{% static 'Observations/js/sidebar.js' %}?v={{ VERSION }}"></script>
```

**Régénération du Manifeste WhiteNoise** :

```bash
# Toujours exécuter après modification de fichiers statiques
docker compose exec web python manage.py collectstatic --noinput --clear

# Le flag --clear supprime les anciens fichiers avant de copier les nouveaux
```

### Cache Côté Navigateur

**En Développement** :

1. **Méthode 1** : Rechargement forcé
   - Windows/Linux : `Ctrl + Shift + R`
   - Mac : `Cmd + Shift + R`

2. **Méthode 2** : Désactiver le cache dans DevTools
   - Ouvrir DevTools (F12)
   - Onglet Network
   - Cocher ☑ "Disable cache"
   - Garder DevTools ouvert

3. **Méthode 3** : Navigation privée
   - Utiliser une fenêtre de navigation privée pour les tests
   - Pas de cache persistant entre les sessions

**Vidage Complet du Cache** :

- Windows/Linux : `Ctrl + Shift + Delete`
- Mac : `Cmd + Shift + Delete`
- Cocher "Fichiers en cache" et valider

---

## 🎯 Bonnes Pratiques

### 1. Toujours Sauvegarder les Fichiers ⚠️ CRITIQUE

**Problème Fréquent** : Les modifications faites par des outils d'IA (Cursor, GitHub Copilot, etc.) sont souvent dans le **buffer mémoire de l'éditeur** mais **PAS sur le disque**.

**Symptômes** :
- `docker compose build` n'intègre pas les modifications
- `git diff` ne montre aucun changement
- Le fichier lu avec PowerShell/cat diffère de celui dans l'éditeur
- Les modifications "disparaissent" après redémarrage de l'éditeur

**Solution** :

```bash
# ✅ 1. TOUJOURS sauvegarder après modification par l'IA
# Windows/Linux : Ctrl+S
# Mac : Cmd+S

# ✅ 2. Vérifier visuellement dans l'éditeur
# Onglet du fichier : sidebar.js •    ← Pas sauvegardé (point ou astérisque)
# Après Ctrl+S :      sidebar.js      ← Sauvegardé (pas de symbole)

# ✅ 3. Vérifier avec Git (si le fichier est versionné)
git status                    # Doit montrer le fichier comme "modified"
git diff chemin/fichier.js    # Doit montrer les différences

# ✅ 4. En cas de doute, vérifier sur le disque
Get-Content "chemin/fichier.js" | Select-Object -First 20  # Windows PowerShell
cat chemin/fichier.js | head -n 20                          # Linux/Mac

# ✅ 5. Comparer avec le conteneur Docker (après build)
docker compose exec web cat /app/chemin/fichier.js | head -n 20
```

**Workflow Recommandé** :

1. L'IA modifie un fichier → **Ctrl+S immédiatement**
2. Vérifier l'onglet → **Pas de point/astérisque**
3. `git status` → **Fichier "modified"**
4. Continuer avec Docker build/restart

### 2. Vérifier les Types en JavaScript

```javascript
// ✅ Toujours vérifier le type avant utilisation
if (element.tagName === 'A' && element.href) {
    // Utiliser element.href en toute sécurité
}

// ✅ Utiliser try-catch pour les opérations risquées
try {
    const url = new URL(someValue);
} catch (e) {
    console.warn('Invalid URL:', someValue, e);
}

// ✅ Vérifier l'existence des propriétés
if (obj && obj.property && obj.property.subProperty) {
    // Utiliser obj.property.subProperty
}
```

### 3. Versioning des Fichiers Statiques

```python
# settings.py - Ajouter une variable VERSION
VERSION = os.environ.get('VERSION', 'dev')

# context_processors.py - Exposer VERSION aux templates
def version_context(request):
    return {
        'VERSION': settings.VERSION,
    }
```

```django
<!-- base.html - Utiliser VERSION dans les URLs statiques -->
<link rel="stylesheet" href="{% static 'Observations/css/styles.css' %}?v={{ VERSION }}">
<script src="{% static 'Observations/js/sidebar.js' %}?v={{ VERSION }}"></script>
```

### 4. Logging et Debugging

```javascript
// ✅ Utiliser console.warn pour les problèmes non-bloquants
if (!element.href) {
    console.warn('Element without href:', element);
    return;
}

// ✅ Utiliser console.error pour les erreurs critiques
try {
    // code risqué
} catch (e) {
    console.error('Critical error:', e);
}

// ❌ Éviter console.log en production
// console.log('Debug info'); // À retirer avant commit
```

### 5. Structure des Formulaires

```html
<!-- ✅ Formulaire avec bouton submit explicite -->
<form method="post" action="{% url 'logout' %}">
    {% csrf_token %}
    <button type="submit" class="btn btn-primary">
        <i class="fas fa-sign-out-alt"></i>
        Déconnexion
    </button>
</form>

<!-- ✅ Formulaire avec JavaScript (si nécessaire) -->
<form method="post" action="{% url 'logout' %}" 
      onclick="this.submit();" 
      style="cursor: pointer;">
    {% csrf_token %}
    <i class="fas fa-sign-out-alt"></i>
    <span>Déconnexion</span>
</form>
```

---

## ✅ Checklist de Déploiement

Avant de pousser en production ou de commiter :

### Fichiers et Code

- [ ] Tous les fichiers sont sauvegardés (Ctrl+S)
- [ ] Aucune instrumentation de debug dans le code
- [ ] Aucun `console.log()` inutile
- [ ] Les commentaires sont à jour
- [ ] Le code respecte les conventions du projet

### Docker et Statiques

- [ ] `docker compose build --no-cache web` exécuté
- [ ] `docker compose up -d web` exécuté
- [ ] `collectstatic --noinput --clear` exécuté
- [ ] Paramètres de version mis à jour dans les templates
- [ ] Fichiers vérifiés dans le conteneur

### Tests

- [ ] Tests manuels effectués (navigation, formulaires, etc.)
- [ ] Aucune erreur JavaScript dans la console
- [ ] Cache navigateur vidé pour les tests
- [ ] Tests sur plusieurs navigateurs (Chrome, Firefox, Edge)
- [ ] Tests en navigation privée

### Documentation

- [ ] CHANGELOG.md mis à jour si nécessaire
- [ ] Documentation technique mise à jour
- [ ] Commentaires de commit clairs et descriptifs

---

## 🛠️ Commandes Utiles

### Gestion des Conteneurs

```bash
# Voir les conteneurs en cours d'exécution
docker compose ps

# Voir les logs en temps réel
docker compose logs -f web

# Redémarrer un conteneur
docker compose restart web

# Arrêter tous les conteneurs
docker compose down

# Démarrer tous les conteneurs
docker compose up -d

# Reconstruire une image
docker compose build --no-cache web
```

### Inspection des Fichiers

```bash
# Lire un fichier dans le conteneur
docker compose exec web cat /app/chemin/fichier.js

# Lister les fichiers statiques collectés
docker compose exec web ls -lh /app/staticfiles/

# Chercher un texte dans un fichier
docker compose exec web grep "texte" /app/chemin/fichier.js

# Afficher les premières lignes
docker compose exec web head -n 50 /app/chemin/fichier.js
```

### Copie de Fichiers

```bash
# Copier du local vers le conteneur
docker cp chemin/local/fichier.js observations_web:/app/chemin/fichier.js

# Copier du conteneur vers le local
docker cp observations_web:/app/chemin/fichier.js chemin/local/

# Copier un dossier entier
docker cp chemin/local/dossier/ observations_web:/app/chemin/
```

### Gestion des Fichiers Statiques

```bash
# Collecter les fichiers statiques
docker compose exec web python manage.py collectstatic --noinput

# Collecter avec suppression des anciens fichiers
docker compose exec web python manage.py collectstatic --noinput --clear

# Vérifier la configuration des statiques
docker compose exec web python manage.py findstatic fichier.js

# Lister tous les fichiers statiques
docker compose exec web python manage.py collectstatic --noinput --dry-run
```

### Debugging

```bash
# Ouvrir un shell dans le conteneur
docker compose exec web bash

# Exécuter une commande Python
docker compose exec web python manage.py shell

# Vérifier les variables d'environnement
docker compose exec web env | grep DJANGO

# Vérifier les processus en cours
docker compose exec web ps aux

# Vérifier l'espace disque
docker compose exec web df -h
```

---

## 🔍 Diagnostic Avancé

### Problème : Fichiers Statiques Non Servis

```bash
# 1. Vérifier que WhiteNoise est installé
docker compose exec web pip list | grep whitenoise

# 2. Vérifier la configuration Django
docker compose exec web python manage.py shell -c "from django.conf import settings; print(settings.STATIC_ROOT)"

# 3. Vérifier que les fichiers existent
docker compose exec web ls -lh /app/staticfiles/Observations/js/

# 4. Vérifier les permissions
docker compose exec web ls -la /app/staticfiles/

# 5. Tester l'accès direct
curl http://localhost:8010/static/Observations/js/sidebar.js
```

### Problème : Modifications Non Visibles

```bash
# 1. Vérifier le timestamp du fichier local
ls -lh observations/static/Observations/js/sidebar.js

# 2. Vérifier le timestamp dans le conteneur
docker compose exec web ls -lh /app/observations/static/Observations/js/sidebar.js

# 3. Comparer les contenus
diff <(cat observations/static/Observations/js/sidebar.js) \
     <(docker compose exec web cat /app/observations/static/Observations/js/sidebar.js)

# 4. Vérifier le manifeste WhiteNoise
docker compose exec web cat /app/staticfiles/staticfiles.json | grep sidebar.js
```

---

## 📚 Ressources

- [Documentation Django Static Files](https://docs.djangoproject.com/en/5.1/howto/static-files/)
- [Documentation WhiteNoise](http://whitenoise.evans.io/)
- [Documentation Docker Compose](https://docs.docker.com/compose/)
- [MDN JavaScript Best Practices](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide)

---

## 💡 Cas d'Usage Réels

### Cas 1 : Correction d'un Bug JavaScript

```bash
# 1. Identifier le problème dans la console navigateur
# 2. Modifier le fichier localement
# 3. Sauvegarder (Ctrl+S)
# 4. Copier dans le conteneur
docker cp observations/static/Observations/js/sidebar.js \
         observations_web:/app/observations/static/Observations/js/sidebar.js

# 5. Régénérer les statiques
docker compose exec web python manage.py collectstatic --noinput --clear

# 6. Redémarrer
docker compose restart web

# 7. Tester avec cache vidé (Ctrl+Shift+R)
```

### Cas 2 : Ajout d'une Nouvelle Fonctionnalité CSS

```bash
# 1. Créer/modifier le fichier CSS localement
# 2. Sauvegarder (Ctrl+S)
# 3. Mettre à jour le template avec le nouveau paramètre de version
# 4. Rebuild complet
docker compose build --no-cache web
docker compose up -d web
docker compose exec web python manage.py collectstatic --noinput --clear

# 5. Tester
```

### Cas 3 : Déploiement en Production

```bash
# 1. Commit et push des modifications
git add .
git commit -m "Fix: Correction bug JavaScript sidebar"
git push origin main

# 2. Sur le serveur de production
cd /opt/observations_nids/docker
git pull

# 3. Rebuild
docker compose build --no-cache web

# 4. Arrêt gracieux
docker compose down

# 5. Démarrage
docker compose up -d

# 6. Attendre le démarrage
sleep 30

# 7. Collecter les statiques
docker compose exec web python manage.py collectstatic --noinput --clear

# 8. Vérifier
docker compose ps
docker compose logs -f web

# 9. Test de santé
curl http://localhost:8010/health/
```

---

**Dernière mise à jour** : 21 janvier 2026  
**Auteur** : Documentation générée suite à session de debugging  
**Version** : 1.0
