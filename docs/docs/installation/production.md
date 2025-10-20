# Guide d'Installation - Environnement de Production (Linux/Raspberry Pi)

Ce document décrit la procédure pour déployer le projet "Observations Nids" sur un serveur de production sous Linux (type Raspberry Pi).

## 1. Prérequis

*   **Python** (version 3.11 ou supérieure)
*   **Git**
*   **Redis**
*   **MariaDB** (recommandé pour la production)
*   **Apache2**
*   **libapache2-mod-wsgi-py3**

## 2. Installation

...

## 3. Déploiement avec Apache et mod_wsgi

...

## 4. Gestion des Services avec systemd

En production, il est crucial de gérer Redis et Celery comme des services `systemd` pour garantir qu'ils démarrent avec le système et redémarrent en cas d'échec.

### 4.1. Service Redis

L'installation de Redis via `apt` (`sudo apt install redis-server`) configure généralement le service `systemd` automatiquement.

**Commandes utiles pour Redis :**

```bash
# Démarrer le service Redis
sudo systemctl start redis-server

# Activer le démarrage automatique au boot
sudo systemctl enable redis-server

# Consulter le statut du service
sudo systemctl status redis-server

# Arrêter le service
sudo systemctl stop redis-server

# Désactiver le démarrage automatique
sudo systemctl disable redis-server
```

### 4.2. Service Celery
[Guide de production Redis-Celery](./redis-celery-production.md)

Contrairement à Redis, vous devez créer manuellement le service pour Celery.

#### Étape 1 : Créer un utilisateur pour Celery

Pour des raisons de sécurité, il est recommandé de lancer Celery avec un utilisateur non privilégié.

```bash
sudo adduser --system --no-create-home --group celery
```

#### Étape 2 : Créer les répertoires pour les logs et les PID

```bash
sudo mkdir -p /var/log/celery /var/run/celery
sudo chown -R celery:celery /var/log/celery /var/run/celery
```

#### Étape 3 : Créer le fichier d'environnement

Ce fichier centralise la configuration de votre service Celery.

**Créez le fichier :**
```bash
sudo nano /etc/default/celeryd
```

**Ajoutez le contenu suivant** (en adaptant les chemins) :

```ini
# Chemin vers l'exécutable de Celery dans votre venv
CELERY_BIN="/chemin/vers/votre/.venv/bin/celery"

# Nom de votre application Celery
CELERY_APP="observations_nids.celery"

# Niveau de log
CELERYD_LOG_LEVEL="INFO"

# Fichier PID
CELERYD_PID_FILE="/var/run/celery/%n.pid"

# Fichier de log
CELERYD_LOG_FILE="/var/log/celery/%n%I.log"
```

#### Étape 4 : Créer le fichier de service systemd

**Créez le fichier :**
```bash
sudo nano /etc/systemd/system/celery.service
```

**Ajoutez le contenu :**

```ini
[Unit]
Description=Celery Service
After=network.target

[Service]
Type=simple
User=celery
Group=celery
EnvironmentFile=/etc/default/celeryd
WorkingDirectory=/chemin/vers/votre/projet
ExecStart=/bin/sh -c '${CELERY_BIN} -A ${CELERY_APP} worker -l ${CELERYD_LOG_LEVEL} --pidfile=${CELERYD_PID_FILE} --logfile=${CELERYD_LOG_FILE}'
Restart=always

[Install]
WantedBy=multi-user.target
```

#### Étape 5 : Activer et gérer le service Celery

```bash
# Recharger systemd pour prendre en compte le nouveau service
sudo systemctl daemon-reload

# Activer et démarrer le service
sudo systemctl enable celery.service
sudo systemctl start celery.service

# Consulter le statut
sudo systemctl status celery.service
```

## 5. Scripts de Gestion des Services

Pour simplifier la gestion des services en développement ou pour des maintenances, vous pouvez utiliser les scripts suivants.

### `start_services.sh`

Ce script active et démarre les services `redis-server` et `celery`.

```bash
#!/bin/bash

# Activer et démarrer Redis
echo "Activation et démarrage de Redis..."
sudo systemctl enable redis-server
sudo systemctl start redis-server

# Activer et démarrer Celery
echo "Activation et démarrage de Celery..."
sudo systemctl enable celery.service
sudo systemctl start celery.service

echo "Services démarrés."
```

### `stop_services.sh`

Ce script arrête et désactive les services.

```bash
#!/bin/bash

# Arrêter et désactiver Redis
echo "Arrêt et désactivation de Redis..."
sudo systemctl stop redis-server
sudo systemctl disable redis-server

# Arrêter et désactiver Celery
echo "Arrêt et désactivation de Celery..."
sudo systemctl stop celery.service
sudo systemctl disable celery.service

echo "Services arrêtés."
```

**Pour utiliser ces scripts :**
1.  Enregistrez-les (par exemple, à la racine de votre projet).
2.  Rendez-les exécutables : `chmod +x start_services.sh stop_services.sh`.
3.  Exécutez-les avec `sudo ./start_services.sh` ou `sudo ./stop_services.sh`.