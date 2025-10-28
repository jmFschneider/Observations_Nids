# Correction configuration Apache - Réactivation WSGI

## Problème identifié

La ligne `WSGIScriptAlias` était commentée dans la configuration Apache, empêchant Django de se charger complètement. De plus, la directive `WSGIDaemonProcess` était manquante.

## Changements à appliquer

### 1. Modifier la configuration Apache

Sur le Raspberry Pi, éditer le fichier :
```bash
sudo nano /etc/apache2/sites-enabled/000-default.conf
```

### 2. Ajouter/Décommenter ces lignes

**AVANT** (lignes 5-6) :
```apache
WSGIProcessGroup Observations_Nids
#   WSGIScriptAlias / /var/www/html/Observations_Nids/observations_nids/wsgi.py
```

**APRÈS** (lignes 5-7) :
```apache
# Configuration WSGI pour Django
WSGIDaemonProcess Observations_Nids python-home=/var/www/html/Observations_Nids/.venv python-path=/var/www/html/Observations_Nids
WSGIProcessGroup Observations_Nids
WSGIScriptAlias / /var/www/html/Observations_Nids/observations_nids/wsgi.py
```

### 3. Explication des directives

- **WSGIDaemonProcess** : Crée un processus dédié pour Django
  - `python-home` : Pointe vers le virtualenv
  - `python-path` : Ajoute le projet au PYTHONPATH

- **WSGIProcessGroup** : Associe les requêtes à ce processus

- **WSGIScriptAlias** : Définit le script WSGI à exécuter (wsgi.py)

## Application des changements

### 1. Vérifier la syntaxe Apache

```bash
sudo apachectl configtest
```

Devrait afficher : `Syntax OK`

### 2. Redémarrer Apache

```bash
sudo systemctl restart apache2
```

### 3. Vérifier le statut

```bash
sudo systemctl status apache2
```

Devrait afficher : `active (running)`

## Vérification du fonctionnement

### 1. Tester en local (sur le Raspberry)

```bash
curl -I http://localhost
```

Devrait retourner un code HTTP 200 ou 302 (redirection).

### 2. Tester depuis l'extérieur

Accéder à : http://88.177.71.193/

L'application Django devrait se charger correctement.

### 3. Vérifier les logs en cas d'erreur

```bash
# Logs Apache
sudo tail -f /var/log/apache2/error.log

# Logs Django (si configurés)
tail -f /var/www/html/Observations_Nids/logs/django.log
```

## Si erreur "No module named 'django'"

Cela signifie que le virtualenv n'est pas correctement référencé. Vérifier :

```bash
# Le virtualenv existe-t-il ?
ls -la /var/www/html/Observations_Nids/.venv/bin/python

# Django est-il installé dedans ?
/var/www/html/Observations_Nids/.venv/bin/python -c "import django; print(django.__version__)"
```

Si Django n'est pas trouvé, réinstaller :
```bash
cd /var/www/html/Observations_Nids
source .venv/bin/activate
pip install -r requirements.txt
deactivate
```

## Si erreur "Permission denied" pour wsgi.py

```bash
sudo chmod 644 /var/www/html/Observations_Nids/observations_nids/wsgi.py
sudo chown www-data:www-data /var/www/html/Observations_Nids/observations_nids/wsgi.py
```

## Après correction réussie

Une fois que l'application se charge :

1. Le fichier `.env` sera correctement lu par Django
2. La variable `ALLOWED_HOSTS` devrait fonctionner
3. L'accès depuis l'IP publique (88.177.71.193) devrait fonctionner

## Rollback si problème

Si la modification cause des erreurs :

1. Revoir l'ancienne configuration :
```bash
sudo nano /etc/apache2/sites-enabled/000-default.conf
```

2. Recommenter WSGIScriptAlias si nécessaire :
```apache
#   WSGIScriptAlias / /var/www/html/Observations_Nids/observations_nids/wsgi.py
```

3. Redémarrer Apache :
```bash
sudo systemctl restart apache2
```

---

**Date** : 17 octobre 2025
**Raison du changement** : Correction du chargement Django via Apache WSGI
**Impact** : Permet le fonctionnement complet de l'application web
