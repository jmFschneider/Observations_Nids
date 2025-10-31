# Gestion du Cache et Debugging Django

Ce document explique les problèmes de cache fréquents lors du développement avec Django et comment les résoudre.

## Problème typique : "Mes modifications ne sont pas prises en compte !"

Vous modifiez un fichier Python (views, models, etc.), vous rafraîchissez la page... et rien ne change ! 🤯

### Pourquoi ça arrive ?

Django et Python utilisent **plusieurs niveaux de cache** qui peuvent parfois ne pas se synchroniser correctement.

---

## Les différents niveaux de cache

### 1. Cache Python (.pyc)

**C'est quoi ?**
- Python compile les fichiers `.py` en bytecode `.pyc` pour accélérer l'exécution
- Ces fichiers sont stockés dans les dossiers `__pycache__/`
- Exemple : `views.py` → `__pycache__/views.cpython-312.pyc`

**Le problème :**
- Normalement, Python détecte les changements et recompile automatiquement
- Mais parfois, un fichier `.pyc` obsolète reste en cache
- Résultat : Python exécute l'ancienne version du code !

**Solution :**
```bash
# Supprimer tous les fichiers .pyc
find . -type f -name "*.pyc" -delete

# Supprimer tous les dossiers __pycache__
find . -type d -name __pycache__ -exec rm -rf {} +

# Sous Windows PowerShell :
Get-ChildItem -Recurse -Filter __pycache__ | Remove-Item -Recurse -Force
```

---

### 2. Cache du serveur de développement Django

**C'est quoi ?**
- Le serveur `runserver` garde les modules Python en mémoire pour la performance
- Il est censé détecter automatiquement les modifications et recharger (`auto-reload`)
- Un message s'affiche normalement : `Watching for file changes with StatReloader`

**Le problème :**
- L'auto-reload ne fonctionne pas toujours parfaitement
- Certains types de changements ne sont pas détectés :
  - Modification de fichiers `.html` → ✅ détecté
  - Modification de fichiers `.py` → ✅ normalement détecté
  - Ajout de **nouveaux** fichiers `.py` ou templates → ⚠️ parfois non détecté
  - Modification de `settings.py` → ⚠️ nécessite souvent un redémarrage manuel

**Solution :**
```bash
# Dans le terminal où tourne le serveur :
Ctrl+C  # Arrêter le serveur
python manage.py runserver  # Redémarrer
```

---

### 3. Processus Python zombie

**C'est quoi ?**
- Parfois, quand vous faites `Ctrl+C`, le processus Python ne se termine pas complètement
- Il continue à tourner en arrière-plan, écoutant toujours sur le port 8000
- Quand vous relancez `runserver`, vous pensez démarrer un nouveau serveur...
- **Mais c'est l'ancien processus zombie qui répond encore !**

**Comment le détecter ?**
```bash
# Lister tous les processus Python
tasklist | findstr python

# Vous devriez voir quelque chose comme :
# python.exe    12345 Console    1    125 000 Ko
# python.exe    67890 Console    1    128 000 Ko  ← zombie !
```

**Solution :**
```bash
# Tuer TOUS les processus Python
taskkill /F /IM python.exe
taskkill /F /IM pythonw.exe

# Attendre 2-3 secondes
timeout /t 2

# Redémarrer le serveur
python manage.py runserver
```

---

### 4. Cache des templates Django

**C'est quoi ?**
- Django peut mettre en cache les templates compilés
- En `DEBUG = True`, ce cache est normalement désactivé
- Mais certaines configurations peuvent le réactiver

**Le problème :**
- Vous modifiez un template `.html`, mais l'ancienne version s'affiche toujours

**Solution :**
```python
# Dans settings.py, vérifier :
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [...],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [...],
            # En développement, NE PAS activer le cache :
            # 'loaders': [
            #     ('django.template.loaders.cached.Loader', [...]),
            # ],
        },
    },
]
```

Sinon, redémarrer le serveur suffit généralement.

---

### 5. Décorateurs Python et stack traces

**C'est quoi ?**
- Les décorateurs comme `@login_required` ou `@user_passes_test` "enveloppent" les fonctions
- Python voit le fichier source comme étant celui du **décorateur**, pas de votre fonction
- Exemple :
  ```python
  @user_passes_test(is_admin)
  def detail_espece(request, espece_id):
      ...
  ```
  → Python indique que la fonction est dans `django/contrib/auth/decorators.py` !

**Le problème :**
- Les messages d'erreur et stack traces peuvent être trompeurs
- Vous cherchez l'erreur au mauvais endroit

**Solution :**
- Regarder **le numéro de ligne** dans le traceback, pas seulement le nom du fichier
- Les décorateurs Django préservent généralement les bonnes lignes

---

## Workflow recommandé pour le développement

### Quand vous modifiez des fichiers Python (views, models, forms)

1. **Arrêter le serveur** : `Ctrl+C` dans le terminal
2. **Vérifier qu'il est bien arrêté** :
   ```bash
   tasklist | findstr python
   # Si des processus apparaissent, les tuer :
   taskkill /F /IM python.exe
   ```
3. **Si problème persistant, nettoyer les caches** :
   ```bash
   # Supprimer __pycache__
   powershell -Command "Get-ChildItem -Recurse -Filter __pycache__ | Remove-Item -Recurse -Force"
   ```
4. **Redémarrer dans un NOUVEAU terminal** (recommandé) :
   ```bash
   cd C:\Projets\observations_nids
   .venv\Scripts\activate
   python manage.py runserver
   ```

### Quand vous modifiez des templates (.html)

- Normalement, **un simple refresh du navigateur** suffit
- Si ça ne fonctionne pas : `Ctrl+C` puis relancer `runserver`

### Quand vous modifiez des fichiers statiques (.css, .js)

1. **En développement** : refresh du navigateur (+ `Ctrl+F5` pour vider le cache navigateur)
2. **En production** : relancer `collectstatic` :
   ```bash
   python manage.py collectstatic --noinput
   ```

---

## Script de redémarrage automatique

Pour éviter ces problèmes, créez un script `restart.bat` :

```batch
@echo off
echo ========================================
echo   Redémarrage propre du serveur Django
echo ========================================

REM Tuer tous les processus Python
echo [1/4] Arrêt des processus Python...
taskkill /F /IM python.exe 2>nul
taskkill /F /IM pythonw.exe 2>nul
timeout /t 2 >nul

REM Nettoyer les caches (optionnel)
echo [2/4] Nettoyage des caches...
powershell -Command "Get-ChildItem -Path . -Recurse -Filter __pycache__ -ErrorAction SilentlyContinue | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue"

REM Activer l'environnement virtuel
echo [3/4] Activation de l'environnement virtuel...
cd C:\Projets\observations_nids
call .venv\Scripts\activate

REM Démarrer le serveur
echo [4/4] Démarrage du serveur Django...
echo ========================================
python manage.py runserver
```

**Utilisation :**
```bash
# Au lieu de `python manage.py runserver`, lancez :
restart.bat
```

---

## Problèmes spécifiques et solutions

### "TemplateDoesNotExist" alors que le fichier existe

**Causes possibles :**
1. Le template est dans le mauvais dossier
2. `APP_DIRS = True` n'est pas configuré dans `TEMPLATES`
3. Le serveur n'a pas été redémarré après création du template

**Solution :**
```bash
# Vérifier la configuration
python manage.py shell -c "from django.conf import settings; print(settings.TEMPLATES[0]['APP_DIRS'])"
# Doit afficher : True

# Redémarrer le serveur
taskkill /F /IM python.exe
python manage.py runserver
```

### "AttributeError: 'Model' object has no attribute 'field_name'"

**Causes possibles :**
1. Migration non appliquée
2. Le modèle est en cache avec l'ancienne définition

**Solution :**
```bash
# Vérifier les migrations
python manage.py showmigrations

# Appliquer les migrations manquantes
python manage.py migrate

# Nettoyer les caches et redémarrer
taskkill /F /IM python.exe
powershell -Command "Get-ChildItem -Recurse -Filter __pycache__ | Remove-Item -Recurse -Force"
python manage.py runserver
```

### "Related object not found" après modification d'un ForeignKey

**Cause :**
- Vous avez changé le `related_name` d'un ForeignKey
- Exemple : `related_name="fiches"` → `related_name="observations"`

**Solution :**
```bash
# 1. Chercher toutes les occurrences de l'ancien nom
rg "ficheobservation_set" --type py

# 2. Remplacer par le nouveau nom
sed -i 's/ficheobservation_set/observations/g' taxonomy/views.py

# 3. Nettoyer et redémarrer
taskkill /F /IM python.exe
powershell -Command "Get-ChildItem -Recurse -Filter __pycache__ | Remove-Item -Recurse -Force"
python manage.py runserver
```

---

## Commandes de debugging utiles

### Vérifier quel fichier Python voit

```bash
python manage.py shell -c "
from taxonomy import views
import inspect
print('Fichier source:', inspect.getsourcefile(views.detail_espece))
print('Ligne de départ:', inspect.getsourcelines(views.detail_espece)[1])
"
```

### Vérifier les templates chargés

```bash
python manage.py shell -c "
from django.conf import settings
print('APP_DIRS:', settings.TEMPLATES[0]['APP_DIRS'])
print('DIRS:', settings.TEMPLATES[0]['DIRS'])
"
```

### Lister tous les processus Python

```bash
# Windows
tasklist | findstr python

# Linux/Mac
ps aux | grep python
```

### Vérifier les migrations appliquées

```bash
python manage.py showmigrations taxonomy
```

---

## Résumé : Checklist de dépannage

Quand vos modifications ne sont pas prises en compte :

- [ ] **1. Sauvegarder le fichier** (ça paraît bête, mais ça arrive !)
- [ ] **2. Vérifier que vous modifiez le bon fichier** (pas une copie ailleurs)
- [ ] **3. Arrêter complètement le serveur** (`Ctrl+C`)
- [ ] **4. Vérifier qu'aucun processus Python ne tourne** (`tasklist | findstr python`)
- [ ] **5. Si doute, tuer tous les processus** (`taskkill /F /IM python.exe`)
- [ ] **6. Nettoyer les caches** (`Get-ChildItem -Recurse -Filter __pycache__ | Remove-Item -Recurse -Force`)
- [ ] **7. Redémarrer dans un NOUVEAU terminal**
- [ ] **8. Vider le cache du navigateur** (`Ctrl+F5`)

**Si rien ne fonctionne :**
```bash
# Reset complet (⚠️ en dernier recours)
taskkill /F /IM python.exe
powershell -Command "Get-ChildItem -Recurse -Filter __pycache__ | Remove-Item -Recurse -Force"
powershell -Command "Get-ChildItem -Recurse -Filter *.pyc | Remove-Item -Force"
# Fermer TOUS les terminaux
# Ouvrir un NOUVEAU terminal
cd C:\Projets\observations_nids
.venv\Scripts\activate
python manage.py check  # Vérifier qu'il n'y a pas d'erreur
python manage.py runserver
```

---

## Pour aller plus loin

### Documentation Django sur l'auto-reload
- [Django runserver auto-reloading](https://docs.djangoproject.com/en/stable/ref/django-admin/#runserver)

### Outils de monitoring
- **django-extensions** : shell amélioré, graphes de modèles
  ```bash
  pip install django-extensions
  python manage.py shell_plus  # Shell avec imports automatiques
  ```

- **django-debug-toolbar** : debug panel dans le navigateur
  - Déjà installé dans ce projet
  - Affiche les requêtes SQL, templates utilisés, cache, etc.

---

**Dernière mise à jour :** 2025-10-09
**Auteur :** Documentation générée avec Claude Code
