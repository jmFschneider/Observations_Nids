# Guide de déploiement sur Raspberry Pi

## Vue d'ensemble

Ce guide explique comment déployer la nouvelle version d'Observations Nids sur le Raspberry Pi en production.

## Prérequis

- Accès SSH au Raspberry Pi
- Git installé sur le Pi
- Python 3.11+ et virtualenv
- Apache2 configuré avec mod_wsgi

## Fichiers à préserver

### Fichiers de configuration Apache

Ces fichiers contiennent des configurations spécifiques au Pi et ne doivent **jamais** être écrasés :

1. **`observations_nids.wsgi`** (dans le répertoire du projet)
   - Configuration WSGI pour Apache
   - Contient les chemins spécifiques au Pi

2. **`/etc/apache2/sites-available/observations_nids.conf`**
   - Configuration du virtual host Apache
   - Contient les paramètres de serveur

3. **`.env`** (dans le répertoire du projet)
   - Variables d'environnement de production
   - Contient SECRET_KEY, DEBUG=False, etc.

### Fichiers de données

- **`media/`** : Dossier contenant les images uploadées
- **`db.sqlite3`** : Base de données (sera supprimée dans ce déploiement)

## Méthode 1 : Script automatique (RECOMMANDÉ)

### Étape 1 : Transférer le script sur le Pi

Depuis votre PC :
```bash
# Option A : Via Git (si le Pi a accès au dépôt)
ssh pi@adresse_ip
cd /var/www/observations_nids
git fetch origin
git checkout production
git pull origin production

# Option B : Via SCP
scp deploy_pi.sh pi@adresse_ip:/var/www/observations_nids/
```

### Étape 2 : Rendre le script exécutable

```bash
ssh pi@adresse_ip
cd /var/www/observations_nids
chmod +x deploy_pi.sh
```

### Étape 3 : Exécuter le script

```bash
./deploy_pi.sh
```

Le script effectuera automatiquement :
1. ✅ Sauvegarde des configurations Apache et du .env
2. ✅ Arrêt d'Apache
3. ✅ Mise à jour du code (git pull)
4. ✅ Restauration des configurations Apache
5. ✅ Installation des dépendances Python
6. ✅ Suppression de l'ancienne base (sauvegardée)
7. ✅ Création de la nouvelle base avec migrations
8. ✅ Collecte des fichiers statiques
9. ✅ Redémarrage d'Apache

### Étape 4 : Créer le superutilisateur

```bash
cd /var/www/observations_nids
source venv/bin/activate
python manage.py createsuperuser
```

### Étape 5 : Vérifier le déploiement

Ouvrez dans un navigateur : `http://adresse_ip_du_pi`

## Méthode 2 : Déploiement manuel

Si vous préférez contrôler chaque étape :

### 1. Sauvegarder les fichiers importants

```bash
ssh pi@adresse_ip
cd /var/www/observations_nids

# Créer un dossier de sauvegarde
mkdir -p backups/$(date +%Y%m%d_%H%M%S)
BACKUP_DIR=backups/$(date +%Y%m%d_%H%M%S)

# Sauvegarder les fichiers critiques
cp observations_nids.wsgi $BACKUP_DIR/
cp .env $BACKUP_DIR/
sudo cp /etc/apache2/sites-available/observations_nids.conf $BACKUP_DIR/

# Sauvegarder la base de données
cp db.sqlite3 $BACKUP_DIR/ 2>/dev/null || echo "Pas de base à sauvegarder"
```

### 2. Arrêter Apache

```bash
sudo systemctl stop apache2
```

### 3. Mettre à jour le code

```bash
cd /var/www/observations_nids

# Sauvegarder les changements locaux si nécessaire
git stash

# Récupérer la version production
git fetch origin
git checkout production
git pull origin production
```

### 4. Restaurer les fichiers de configuration

```bash
# Restaurer les fichiers sauvegardés
cp $BACKUP_DIR/observations_nids.wsgi .
cp $BACKUP_DIR/.env .
```

### 5. Mettre à jour l'environnement Python

```bash
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements-prod.txt
```

### 6. Réinitialiser la base de données

```bash
# Supprimer l'ancienne base
rm db.sqlite3

# Créer la nouvelle base
python manage.py migrate
```

### 7. Collecter les fichiers statiques

```bash
python manage.py collectstatic --noinput
```

### 8. Créer un superutilisateur

```bash
python manage.py createsuperuser
```

### 9. Redémarrer Apache

```bash
sudo systemctl start apache2

# Vérifier le statut
sudo systemctl status apache2
```

## Vérifications post-déploiement

### 1. Vérifier qu'Apache fonctionne

```bash
sudo systemctl status apache2
```

### 2. Vérifier les logs Apache

```bash
# Logs d'erreur
sudo tail -f /var/log/apache2/error.log

# Logs d'accès
sudo tail -f /var/log/apache2/access.log
```

### 3. Vérifier les permissions

```bash
# Le serveur web doit pouvoir écrire dans la base de données
sudo chown www-data:www-data /var/www/observations_nids/db.sqlite3

# Et dans le dossier media si nécessaire
sudo chown -R www-data:www-data /var/www/observations_nids/media/
```

### 4. Tester le site

- Accéder à la page d'accueil
- Se connecter avec le superutilisateur
- Vérifier l'interface admin : `/admin/`
- Tester la création d'une observation

## Dépannage

### Apache ne démarre pas

```bash
# Vérifier la syntaxe de la configuration
sudo apache2ctl configtest

# Consulter les logs détaillés
sudo journalctl -xeu apache2.service
```

### Erreur 500 Internal Server Error

```bash
# Vérifier les logs Django
sudo tail -f /var/log/apache2/error.log

# Vérifier les permissions
ls -la /var/www/observations_nids/db.sqlite3

# Tester Django directement
cd /var/www/observations_nids
source venv/bin/activate
python manage.py runserver 0.0.0.0:8001
```

### Problème de fichiers statiques

```bash
# Recollect les fichiers statiques
cd /var/www/observations_nids
source venv/bin/activate
python manage.py collectstatic --clear --noinput

# Vérifier les permissions
sudo chown -R www-data:www-data /var/www/observations_nids/static/
```

### Base de données corrompue

```bash
# Restaurer depuis une sauvegarde
cd /var/www/observations_nids
cp backups/YYYYMMDD_HHMMSS/db.sqlite3 .
sudo chown www-data:www-data db.sqlite3
sudo systemctl restart apache2
```

## Retour en arrière (rollback)

Si le déploiement échoue :

```bash
cd /var/www/observations_nids

# Retourner à la version précédente
git checkout Mise-en-place-des-forms-Django

# Restaurer la base de données
cp backups/YYYYMMDD_HHMMSS/db.sqlite3 .
sudo chown www-data:www-data db.sqlite3

# Installer les anciennes dépendances
source venv/bin/activate
pip install -r requirements.txt

# Redémarrer Apache
sudo systemctl restart apache2
```

## Mises à jour futures

Pour les prochaines mises à jour (une fois la production stabilisée) :

```bash
cd /var/www/observations_nids
git pull origin production
source venv/bin/activate
pip install -r requirements-prod.txt
python manage.py migrate
python manage.py collectstatic --noinput
sudo systemctl restart apache2
```

## Notes importantes

1. **Pas de données à préserver** : Cette première mise à jour supprime complètement l'ancienne base de données car aucune donnée de production n'existe actuellement.

2. **Sauvegardes automatiques** : Le script sauvegarde automatiquement :
   - Les configurations Apache
   - Le fichier .env
   - L'ancienne base de données (au cas où)

3. **Downtime** : Le site sera indisponible pendant environ 2-5 minutes durant la mise à jour.

4. **Environnement virtuel** : Le script suppose que l'environnement virtuel est dans `/var/www/observations_nids/venv/`

5. **Permissions** : Vérifiez que l'utilisateur `www-data` (Apache) a les bonnes permissions sur les fichiers.

## Support

En cas de problème :
1. Consulter les logs : `/var/log/apache2/error.log`
2. Vérifier la configuration Apache : `sudo apache2ctl configtest`
3. Tester Django en mode développement : `python manage.py runserver`
4. Restaurer la version précédente (voir section Rollback)

---

**Version du document** : 1.0
**Date** : 2025-10-05
**Compatible avec** : Branche `production`
