# Scripts Utilitaires - Observations Nids

> Collection de scripts Bash et Python pour la maintenance et l'administration du projet

## 📋 Liste des scripts

### 🔧 Maintenance

| Script | Description | Usage |
|--------|-------------|-------|
| `maintenance_on.sh` | Active le mode maintenance | `sudo ./scripts/maintenance_on.sh` |
| `maintenance_off.sh` | Désactive le mode maintenance | `sudo ./scripts/maintenance_off.sh` |

**Fonctionnement** : Ces scripts créent/suppriment un fichier `.maintenance` qui déclenche un middleware Django affichant une page de maintenance.

**Documentation** : Voir [Page de maintenance](../docs/docs/deployment/production.md#mode-maintenance)

---

### 📊 Statistiques & Monitoring

| Script | Description | Usage |
|--------|-------------|-------|
| `generate_stats.sh` | Génère les statistiques GoAccess multi-sites | `sudo /usr/local/bin/generate_stats.sh` |

**Fonctionnement** :
- Analyse les logs Apache (`access.log` et `django-access.log`)
- Génère 3 rapports HTML séparés (météo, observations, global)
- Crée un tableau de bord centralisé
- Déploie les fichiers dans `/var/www/html/stats/`

**Rapports générés** :
- `/stats/` - Tableau de bord principal
- `/stats/meteo/` - Stats meteo-poelley50.fr
- `/stats/observations/` - Stats observation-nids.meteo-poelley50.fr
- `/stats/global/` - Stats combinées

**Automatisation** : Configurable via cron (recommandé : toutes les heures)

**Documentation complète** : [GoAccess Multi-Sites](../docs/docs/learning/goaccess-multi-sites.md)

---

### 🔍 Vérifications

| Script | Description | Usage |
|--------|-------------|-------|
| `check_duplicate_emails.py` | Vérifie les doublons d'emails dans la base | `python scripts/check_duplicate_emails.py` |

**Fonctionnement** : Script Python/Django qui interroge la base de données pour détecter les emails dupliqués.

---

## 📦 Déploiement des scripts sur le serveur

### Méthode 1 : Via SCP (recommandée)

```bash
# Depuis votre PC (répertoire du projet)
scp scripts/generate_stats.sh pi@meteo-poelley50.fr:/tmp/

# Sur le serveur
ssh pi@meteo-poelley50.fr
sudo mv /tmp/generate_stats.sh /usr/local/bin/
sudo chmod +x /usr/local/bin/generate_stats.sh
```

### Méthode 2 : Via Git

```bash
# Sur le serveur
cd /var/www/html/Observations_Nids
git pull origin main
sudo cp scripts/generate_stats.sh /usr/local/bin/
sudo chmod +x /usr/local/bin/generate_stats.sh
```

---

## 🔐 Permissions

Les scripts de maintenance nécessitent les droits `sudo` car ils modifient des fichiers dans `/var/www/html/`.

**Vérifier les permissions** :
```bash
ls -la /usr/local/bin/generate_stats.sh
# Attendu : -rwxr-xr-x  1 root root  ...  generate_stats.sh
```

**Corriger si nécessaire** :
```bash
sudo chmod +x /usr/local/bin/generate_stats.sh
sudo chown root:root /usr/local/bin/generate_stats.sh
```

---

## ⏰ Automatisation

### Tâche cron pour generate_stats.sh

```bash
sudo crontab -e
```

Ajouter :
```cron
# Génération des statistiques toutes les heures
0 * * * * /usr/local/bin/generate_stats.sh >> /var/log/goaccess.log 2>&1
```

**Vérifier que le cron est actif** :
```bash
sudo crontab -l | grep generate_stats
```

---

## 📝 Logs

| Script | Fichier de log | Commande de visualisation |
|--------|----------------|---------------------------|
| `generate_stats.sh` | `/var/log/goaccess.log` | `sudo tail -f /var/log/goaccess.log` |
| `maintenance_on.sh` | stdout | aucun |
| `maintenance_off.sh` | stdout | aucun |

---

## 🧪 Tests

### Tester generate_stats.sh

```bash
# Exécution manuelle
sudo /usr/local/bin/generate_stats.sh

# Vérifier la sortie
ls -la /var/www/html/stats/

# Accès web
curl -u admin:password http://meteo-poelley50.fr/stats/
```

### Tester le mode maintenance

```bash
# Activer
sudo ./scripts/maintenance_on.sh

# Vérifier
curl http://observation-nids.meteo-poelley50.fr/
# Doit afficher la page de maintenance

# Désactiver
sudo ./scripts/maintenance_off.sh
```

---

## 🛠️ Dépannage

### generate_stats.sh échoue

**Erreur : "GoAccess n'est pas installé"**
```bash
sudo apt update
sudo apt install goaccess
```

**Erreur : "Fichier de log introuvable"**
```bash
# Vérifier les logs
ls -la /var/log/apache2/access.log
ls -la /var/log/apache2/django-access.log

# Vérifier les permissions
sudo chmod 644 /var/log/apache2/*.log
```

**Erreur : "Permission denied"**
```bash
# Vérifier les droits du script
sudo chmod +x /usr/local/bin/generate_stats.sh

# Vérifier les permissions du répertoire de sortie
sudo chown -R www-data:www-data /var/www/html/stats
```

---

## 📚 Documentation associée

- **[Déploiement Production](../docs/docs/deployment/production.md)** - Guide complet de déploiement
- **[GoAccess Multi-Sites](../docs/docs/learning/goaccess-multi-sites.md)** - Configuration avancée des statistiques
- **[Installation GoAccess](../docs/docs/learning/goaccess-installation.md)** - Installation de base
- **[Configuration Apache Stats](../docs/docs/learning/configuration-apache-stats.md)** - Configuration VirtualHost

---

## 🤝 Contribution

Pour ajouter un nouveau script :

1. Créer le script dans `scripts/`
2. Ajouter les commentaires d'en-tête :
   ```bash
   #!/bin/bash
   #
   # Description du script
   #
   # Usage: ./scripts/mon_script.sh
   #
   ```
3. Rendre le script exécutable : `chmod +x scripts/mon_script.sh`
4. Documenter dans ce README
5. Commiter avec le préfixe `feat(scripts): `

---

**Dernière mise à jour** : 26 octobre 2025
**Mainteneur** : Équipe Observations Nids
