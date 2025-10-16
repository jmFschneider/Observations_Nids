# Guide de déploiement Celery sur Raspberry Pi

Ce guide explique comment corriger et déployer les services Celery sur votre Raspberry Pi.

## Problème identifié

L'erreur `Failed at step EXEC spawning ... code=13` indique un problème de permissions. Les causes principales étaient :

1. **Type de service incorrect** : `Type=forking` avec `--detach` ne fonctionne pas correctement avec systemd
2. **Permissions insuffisantes** : www-data n'avait pas accès au virtualenv ou aux répertoires nécessaires
3. **Répertoires manquants** : `/var/run/celery/` n'existait pas avec les bonnes permissions

## Solutions apportées

### 1. Configuration du service corrigée

- **Type changé de `forking` à `simple`** : systemd gère le processus directement
- **Suppression de `--detach`** : pas nécessaire avec `Type=simple`
- **Utilisation de `RuntimeDirectory`** : crée automatiquement `/run/celery/` avec les bonnes permissions
- **Ajout de limites de ressources** : optimisé pour Raspberry Pi
- **Sécurisation renforcée** : `ProtectSystem`, `ProtectHome`, etc.

### 2. Script de configuration des permissions

Le script `setup_celery_permissions.sh` configure automatiquement :
- Les permissions du virtualenv
- Les répertoires de logs et media
- Les permissions du fichier .env
- Teste l'exécution de Celery par www-data

## Étapes de déploiement

### 1. Sur votre machine de développement

Commitez les nouveaux fichiers :

```bash
git add deployment/
git commit -m "fix: Corriger la configuration des services Celery pour Raspberry Pi"
git push
```

### 2. Sur le Raspberry Pi

#### A. Mettre à jour le code

```bash
cd /var/www/html/Observations_Nids
sudo -u www-data git pull
```

#### B. Arrêter les services existants (si ils tournent)

```bash
sudo systemctl stop celery-worker 2>/dev/null || true
sudo systemctl stop celery-beat 2>/dev/null || true
sudo systemctl disable celery-worker 2>/dev/null || true
sudo systemctl disable celery-beat 2>/dev/null || true
```

#### C. Configurer les permissions

```bash
cd /var/www/html/Observations_Nids
chmod +x deployment/setup_celery_permissions.sh
sudo deployment/setup_celery_permissions.sh
```

Ce script va :
- ✓ Créer et configurer les répertoires de logs et media
- ✓ Corriger les permissions du virtualenv
- ✓ Rendre Celery exécutable par www-data
- ✓ Vérifier le fichier .env
- ✓ Tester l'exécution de Celery

#### D. Installer les nouveaux fichiers service

```bash
# Copier les fichiers service
sudo cp deployment/celery-worker.service /etc/systemd/system/
sudo cp deployment/celery-beat.service /etc/systemd/system/

# Recharger systemd pour prendre en compte les nouveaux fichiers
sudo systemctl daemon-reload
```

#### E. Démarrer les services

```bash
# Activer les services au démarrage
sudo systemctl enable celery-worker
sudo systemctl enable celery-beat

# Démarrer les services
sudo systemctl start celery-worker
sudo systemctl start celery-beat
```

#### F. Vérifier le statut

```bash
# Vérifier le statut des services
sudo systemctl status celery-worker
sudo systemctl status celery-beat

# Voir les logs en temps réel
sudo journalctl -u celery-worker -f
sudo journalctl -u celery-beat -f

# Ou consulter les fichiers de logs
tail -f /var/www/html/Observations_Nids/logs/celery-worker.log
tail -f /var/www/html/Observations_Nids/logs/celery-beat.log
```

## Commandes utiles

### Gérer les services

```bash
# Démarrer
sudo systemctl start celery-worker
sudo systemctl start celery-beat

# Arrêter
sudo systemctl stop celery-worker
sudo systemctl stop celery-beat

# Redémarrer
sudo systemctl restart celery-worker
sudo systemctl restart celery-beat

# Recharger la configuration (sans interrompre les tâches en cours)
sudo systemctl reload celery-worker

# Voir le statut
sudo systemctl status celery-worker
sudo systemctl status celery-beat
```

### Consulter les logs

```bash
# Logs systemd (recommandé)
sudo journalctl -u celery-worker -n 100
sudo journalctl -u celery-beat -n 100

# Suivre les logs en temps réel
sudo journalctl -u celery-worker -f

# Logs dans les fichiers
tail -f /var/www/html/Observations_Nids/logs/celery-worker.log
tail -f /var/www/html/Observations_Nids/logs/celery-beat.log
```

### Debugging

```bash
# Tester Celery manuellement en tant que www-data
sudo -u www-data /var/www/html/Observations_Nids/.venv/bin/celery -A observations_nids worker --loglevel=debug

# Vérifier les permissions
ls -la /var/www/html/Observations_Nids/.venv/bin/celery
sudo -u www-data test -x /var/www/html/Observations_Nids/.venv/bin/celery && echo "Executable" || echo "Not executable"

# Vérifier les tâches Celery
sudo -u www-data /var/www/html/Observations_Nids/.venv/bin/celery -A observations_nids inspect active
sudo -u www-data /var/www/html/Observations_Nids/.venv/bin/celery -A observations_nids inspect scheduled

# Vérifier la connexion Redis
redis-cli ping
```

## Optimisations pour Raspberry Pi

Les fichiers service incluent des optimisations spécifiques pour Raspberry Pi :

- **Concurrency** : Limité à 2 workers pour ne pas surcharger la mémoire
- **Memory Limit** : 512M pour worker, 256M pour beat
- **CPU Quota** : 150% pour worker, 50% pour beat
- **Max tasks per child** : 100 pour éviter les fuites mémoire

## Tâches de transcription

Pour vérifier que la transcription fonctionne :

```bash
# Vérifier les tâches en cours
sudo -u www-data /var/www/html/Observations_Nids/.venv/bin/celery -A observations_nids inspect active

# Lancer manuellement une tâche de transcription (depuis Django shell)
cd /var/www/html/Observations_Nids
sudo -u www-data .venv/bin/python manage.py shell

# Dans le shell Python :
from transcription.tasks import transcribe_audio
result = transcribe_audio.delay('/path/to/audio/file.wav')
print(result.id)
```

## Troubleshooting

### Erreur "Permission denied" (code 13)

Exécuter à nouveau le script de permissions :
```bash
sudo /var/www/html/Observations_Nids/deployment/setup_celery_permissions.sh
```

### Service ne démarre pas

1. Vérifier les logs : `sudo journalctl -u celery-worker -n 50`
2. Tester manuellement : `sudo -u www-data .venv/bin/celery -A observations_nids worker --loglevel=debug`
3. Vérifier Redis : `redis-cli ping`
4. Vérifier la base de données : `sudo systemctl status mariadb`

### Mémoire insuffisante

Si le Raspberry Pi manque de mémoire :
- Réduire `--concurrency=2` à `--concurrency=1`
- Réduire `MemoryLimit=512M` à `MemoryLimit=256M`
- Ajouter un swap si nécessaire

### Redis non disponible

```bash
sudo systemctl status redis-server
sudo systemctl start redis-server
sudo systemctl enable redis-server
```

## Fichiers créés

- `deployment/celery-worker.service` : Service systemd pour le worker Celery
- `deployment/celery-beat.service` : Service systemd pour le scheduler Celery
- `deployment/setup_celery_permissions.sh` : Script de configuration des permissions
- `deployment/CELERY_DEPLOYMENT.md` : Ce guide

## Support

En cas de problème :
1. Consulter les logs : `sudo journalctl -u celery-worker -n 100`
2. Vérifier les permissions : exécuter le script `setup_celery_permissions.sh`
3. Tester manuellement Celery en tant que www-data
4. Vérifier que Redis et MariaDB fonctionnent correctement
