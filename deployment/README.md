# Deployment - Configuration Celery

Ce dossier contient les fichiers nécessaires pour déployer les services Celery sur le Raspberry Pi.

## Fichiers

### Services systemd

- **celery-worker.service** : Service systemd pour le worker Celery (traitement des tâches)
- **celery-beat.service** : Service systemd pour le scheduler Celery (tâches planifiées)

### Scripts

- **deploy_celery.sh** : Script de déploiement automatique complet (recommandé)
- **setup_celery_permissions.sh** : Script de configuration des permissions uniquement

### Documentation

- **[CELERY_DEPLOYMENT.md](../docs/deployment/CELERY_DEPLOYMENT.md)** : Guide complet de déploiement avec toutes les explications

## Déploiement rapide

Sur le Raspberry Pi, une seule commande :

```bash
cd /var/www/html/Observations_Nids
sudo deployment/deploy_celery.sh
```

Ce script exécute automatiquement :
1. Arrêt des services existants
2. Configuration des permissions
3. Installation des fichiers service
4. Rechargement de systemd
5. Activation et démarrage des services
6. Vérification du statut

## Déploiement manuel

Si vous préférez faire étape par étape :

```bash
# 1. Configurer les permissions
sudo deployment/setup_celery_permissions.sh

# 2. Copier les fichiers service
sudo cp deployment/celery-worker.service /etc/systemd/system/
sudo cp deployment/celery-beat.service /etc/systemd/system/

# 3. Recharger systemd
sudo systemctl daemon-reload

# 4. Activer et démarrer
sudo systemctl enable celery-worker celery-beat
sudo systemctl start celery-worker celery-beat

# 5. Vérifier
sudo systemctl status celery-worker celery-beat
```

## Documentation

Consultez [CELERY_DEPLOYMENT.md](../docs/deployment/CELERY_DEPLOYMENT.md) pour :
- Explication détaillée des problèmes corrigés
- Guide complet de déploiement
- Commandes de gestion et debugging
- Troubleshooting
