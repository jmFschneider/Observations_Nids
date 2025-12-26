# Migration vers Bind Mount pour les Médias

## Modifications effectuées

Le fichier `docker/docker-compose.yml` a été modifié pour utiliser un bind mount local au lieu d'un volume Docker nommé pour les médias.

**Changements** :
- Services `web`, `celery_worker`, et `nginx` : utilisation de `/opt/observations_nids_pilote/media` au lieu de `media_volume`
- Suppression de la définition du volume `media_volume` dans la section volumes

## Instructions de déploiement sur Ubuntu

### 1. Transférer le fichier docker-compose.yml modifié

Depuis Windows, transférez le fichier vers Ubuntu :
```powershell
# Exemple avec SCP (adaptez selon votre méthode de transfert)
scp docker\docker-compose.yml schneider@ubuntuell:/opt/observations_nids_pilote/docker/
```

### 2. Ajuster les permissions du répertoire media

Sur Ubuntu, exécutez :
```bash
# Se connecter à Ubuntu
ssh schneider@ubuntuell

# Ajuster les permissions pour que Django puisse écrire
sudo chown -R www-data:www-data /opt/observations_nids_pilote/media
sudo chmod -R 775 /opt/observations_nids_pilote/media

# Ou si vous préférez utiliser l'utilisateur observations
# sudo chown -R observations:www-data /opt/observations_nids_pilote/media
```

**Note** : `www-data` est utilisé car NextCloud tourne avec cet utilisateur. Les permissions 775 permettent au groupe d'écrire également.

### 3. Arrêter et redémarrer les conteneurs

```bash
cd /opt/observations_nids_pilote/docker

# Arrêter les conteneurs
docker compose down

# Optionnel : Supprimer l'ancien volume (si vous voulez libérer l'espace)
# docker volume rm docker_media_volume

# Redémarrer les conteneurs
docker compose up -d

# Vérifier que tout fonctionne
docker compose ps
docker compose logs web | tail -20
```

### 4. Vérifier que les médias sont accessibles

```bash
# Créer un fichier test depuis le conteneur
docker exec observations_web touch /app/mediafiles/test_from_container.txt

# Vérifier qu'il apparaît sur le système hôte
ls -la /opt/observations_nids_pilote/media/
```

## Configuration NextCloud

Maintenant que les médias sont dans un dossier local, vous pouvez configurer NextCloud pour y accéder :

### Option A : External Storage (Interface Web)

1. Connectez-vous à NextCloud (http://ubuntuell:8080)
2. Allez dans **Settings** → **Administration** → **External Storage**
3. Ajoutez un nouveau stockage :
   - **Type** : Local
   - **Folder name** : `observations_nids_media` (ou autre nom de votre choix)
   - **Configuration** : `/opt/observations_nids_pilote/media`
   - **Available for** : Sélectionnez les utilisateurs/groupes

### Option B : Volume Mount dans le conteneur NextCloud

Si vous préférez monter le dossier directement dans le conteneur NextCloud, modifiez le docker-compose.yml de NextCloud pour ajouter :

```yaml
services:
  nextcloud:
    volumes:
      - /opt/observations_nids_pilote/media:/var/www/html/data/observations_media
```

Puis redémarrez NextCloud :
```bash
cd /chemin/vers/nextcloud
docker compose restart
```

## Synchronisation depuis Windows

Une fois NextCloud configuré :

1. **Installez le client NextCloud** sur Windows
2. **Configurez la synchronisation** vers le dossier `observations_nids_media`
3. **Déposez vos fiches scannées** dans ce dossier
4. Elles seront automatiquement synchronisées vers Ubuntu → `/opt/observations_nids_pilote/media`

## Structure des répertoires pour les fiches scannées

Organisez vos fiches dans des sous-répertoires, par exemple :
```
/opt/observations_nids_pilote/media/
├── transcription_results/     # Résultats de transcription
├── fiches_2024/              # Fiches par année
│   ├── janvier/
│   ├── fevrier/
│   └── ...
└── fiches_archive/           # Archives
```

## Vérification finale

```bash
# Vérifier les permissions
ls -la /opt/observations_nids_pilote/media/

# Vérifier les logs des conteneurs
docker compose logs web celery_worker nginx

# Tester l'upload depuis l'interface web d'observations_nids
```

## Dépannage

### Erreur de permissions
Si vous avez des erreurs de permissions :
```bash
sudo chown -R www-data:www-data /opt/observations_nids_pilote/media
sudo chmod -R 775 /opt/observations_nids_pilote/media
```

### Les fichiers n'apparaissent pas
Vérifiez que le bind mount est bien actif :
```bash
docker inspect observations_web | grep -A 5 "Mounts"
```

### NextCloud ne voit pas les fichiers
Vérifiez que le chemin `/opt/observations_nids_pilote/media` est accessible depuis le conteneur NextCloud.
