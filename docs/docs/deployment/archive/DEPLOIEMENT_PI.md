# Guide de Déploiement sur Raspberry Pi

Ce document est le guide de référence pour déployer l'application "Observations Nids" sur un serveur de production, typiquement un Raspberry Pi.

## 1. Prérequis

### 1.1. Système
- Un Raspberry Pi avec un système d'exploitation à jour (type Debian/Raspberry Pi OS).
- Accès SSH avec un utilisateur ayant les droits `sudo`.
- Git, Python 3.11+ et `virtualenv` installés.
- Serveur web Apache2 installé.

### 1.2. Sécurité

Avant tout déploiement, il est **impératif** de sécuriser votre Raspberry Pi. Suivez la checklist détaillée dans le document suivant :

➡️ **[Guide de Sécurisation du Raspberry Pi](./securite_raspberrypi_checklist.md)**

Ne procédez pas au déploiement sans avoir complété au minimum la Phase 1 de cette checklist.

### 1.3. Configuration Apache

Ce guide suppose que vous utilisez **Apache2 avec `mod_wsgi`**. Une configuration fonctionnelle est nécessaire. Les fichiers de configuration spécifiques au projet sont :

- `/etc/apache2/sites-available/observations_nids.conf` : Fichier VirtualHost.
- `observations_nids.wsgi` : Script d'interface WSGI dans le répertoire du projet.

> **Note sur Gunicorn** : Bien que `gunicorn` soit présent dans `requirements-prod.txt`, la configuration actuelle documentée et scriptée repose sur `mod_wsgi`. Gunicorn peut être utilisé comme alternative, souvent derrière un reverse proxy Nginx, mais ce n'est pas la configuration décrite ici.

---

## 2. Méthode 1 : Déploiement Automatisé (Recommandé)

Cette méthode utilise le script `deploy_pi.sh` pour automatiser toutes les étapes. C'est la méthode la plus fiable et la moins sujette aux erreurs.

### ⚠️ AVERTISSEMENT TRÈS IMPORTANT ⚠️

Dans sa version actuelle, le script `deploy_pi.sh` est **DESTRUCTIF**. Il **supprime et recrée la base de données** (`db.sqlite3`) à chaque exécution. 

- **Utilisez-le uniquement pour la toute première installation** sur un serveur vierge.
- **NE L'UTILISEZ PAS** pour une mise à jour si vous avez des données que vous souhaitez conserver.

Pour les mises à jour futures, voir la section [Mises à jour non-destructives](#4-mises-a-jour-futures-non-destructives).

### Étapes du déploiement automatisé

1.  **Transférer le script sur le Pi (si nécessaire) :**
    ```bash
    # Depuis votre machine locale
    scp deploy_pi.sh pi@<adresse_ip_du_pi>:/chemin/vers/le/projet/
    ```

2.  **Se connecter au Pi et rendre le script exécutable :**
    ```bash
    ssh pi@<adresse_ip_du_pi>
    cd /chemin/vers/le/projet/
    chmod +x deploy_pi.sh
    ```

3.  **Exécuter le script :**
    ```bash
    ./deploy_pi.sh
    ```

Le script va maintenant effectuer les 10 étapes automatiquement : sauvegarde des configurations, arrêt du serveur, mise à jour du code, installation des dépendances, réinitialisation de la base de données, collecte des fichiers statiques et redémarrage du serveur.

4.  **Créer un super-utilisateur :**
    Une fois le script terminé, créez votre compte administrateur.
    ```bash
    cd /chemin/vers/le/projet/
    source .venv/bin/activate
    python manage.py createsuperuser
    ```

5.  **Vérifier le déploiement :**
    Ouvrez votre navigateur et accédez à l'adresse IP ou au nom de domaine de votre Raspberry Pi.

---

## 3. Méthode 2 : Déploiement Manuel

Suivez ces étapes si vous souhaitez un contrôle total sur le processus. Ces étapes correspondent à ce que fait le script `deploy_pi.sh`.

1.  **Sauvegarder les fichiers de configuration :**
    ```bash
    cd /chemin/vers/le/projet/
    mkdir -p backups
    cp .env backups/
    cp observations_nids.wsgi backups/
    sudo cp /etc/apache2/sites-available/observations_nids.conf backups/
    ```

2.  **Arrêter le serveur web :**
    ```bash
    sudo systemctl stop apache2
    ```

3.  **Mettre à jour le code source :**
    ```bash
    git fetch origin
    git checkout production
    git pull origin production
    ```

4.  **Restaurer les fichiers de configuration :**
    ```bash
    cp backups/.env .
    cp backups/observations_nids.wsgi .
    ```

5.  **Mettre à jour l'environnement Python :**
    ```bash
    source .venv/bin/activate
    pip install -r requirements-prod.txt
    ```

6.  **Réinitialiser la base de données (⚠️ Action destructive) :**
    ```bash
    # Sauvegarder l'ancienne base au cas où
    mv db.sqlite3 backups/db.sqlite3.old
    # Appliquer les migrations pour en créer une nouvelle
    python manage.py migrate
    ```

7.  **Collecter les fichiers statiques :**
    ```bash
    python manage.py collectstatic --noinput
    ```

8.  **Redémarrer le serveur web :**
    ```bash
    sudo systemctl start apache2
    ```

9.  **Créer un super-utilisateur et vérifier** comme pour la méthode automatique.

---

## 4. Mises à Jour Futures (Non-destructives)

Une fois que votre application est en production avec des données réelles, vous **NE DEVEZ PLUS** supprimer la base de données.

### Modifier le script `deploy_pi.sh`

Ouvrez le script `deploy_pi.sh` et commentez ou supprimez les lignes qui suppriment la base de données :

```bash
# ÉTAPE 7 : commenter ou supprimer ces lignes
# echo -e "${YELLOW}[7/10]${NC} Suppression de l'ancienne base de données..."
# if [ -f "$PROJECT_DIR/db.sqlite3" ]; then
#     mv "$PROJECT_DIR/db.sqlite3" "$BACKUP_DIR/db_old_$(date +%Y%m%d_%H%M%S).sqlite3"
#     echo -e "${GREEN}✓${NC} Ancienne base sauvegardée\n"
# else
#     echo -e "${YELLOW}!${NC} Aucune base de données trouvée\n"
# fi
```

Le script se contentera alors d'appliquer les nouvelles migrations (`python manage.py migrate`) sans effacer les données existantes.

### Procédure de mise à jour manuelle

La procédure est plus simple :

```bash
# 1. Mettre à jour le code
git pull origin production

# 2. Activer l'environnement
source .venv/bin/activate

# 3. Mettre à jour les dépendances
pip install -r requirements-prod.txt

# 4. Appliquer les migrations de base de données
python manage.py migrate

# 5. Mettre à jour les fichiers statiques
python manage.py collectstatic --noinput

# 6. Redémarrer le serveur
sudo systemctl restart apache2
```