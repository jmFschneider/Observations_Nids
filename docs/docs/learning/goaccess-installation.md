# Installation de GoAccess pour le suivi des statistiques web

## Objectif
Mettre en place GoAccess pour analyser les logs Apache et générer des statistiques de visite accessibles via une page web protégée.

## Prérequis
- Raspberry Pi avec Apache2 installé
- Accès sudo au serveur
- Logs Apache actifs dans `/var/log/apache2/`

## 1. Installation de GoAccess

```bash
sudo apt update
sudo apt install goaccess
```

## 2. Création du répertoire pour les statistiques

Créez un dossier dédié dans votre arborescence web :

```bash
sudo mkdir -p /var/www/html/stats
sudo chown www-data:www-data /var/www/html/stats
```

## 3. Génération du rapport HTML initial

Générez le premier rapport à partir des logs Apache :

```bash
sudo goaccess /var/log/apache2/access.log -o /var/www/html/stats/index.html --log-format=COMBINED
```

**Options :**
- `/var/log/apache2/access.log` : fichier de log à analyser
- `-o /var/www/html/stats/index.html` : fichier de sortie HTML
- `--log-format=COMBINED` : format des logs Apache (format combiné standard)

## 4. Automatisation avec cron

Pour mettre à jour automatiquement les statistiques toutes les heures :

```bash
sudo crontab -e
```

Ajoutez cette ligne à la fin du fichier :

```
0 * * * * goaccess /var/log/apache2/access.log -o /var/www/html/stats/index.html --log-format=COMBINED
```

**Explication :** `0 * * * *` = à la minute 0 de chaque heure

## 5. Protection par authentification

### Créer un utilisateur avec mot de passe

```bash
sudo htpasswd -c /etc/apache2/.htpasswd admin
```

Entrez le mot de passe quand demandé. Pour ajouter d'autres utilisateurs (sans `-c`) :

```bash
sudo htpasswd /etc/apache2/.htpasswd autre_utilisateur
```

### Créer le fichier .htaccess

Créez `/var/www/html/stats/.htaccess` avec ce contenu :

```apache
AuthType Basic
AuthName "Statistiques du site"
AuthUserFile /etc/apache2/.htpasswd
Require valid-user
```

### Activer .htaccess dans Apache (si nécessaire)

Vérifiez que `.htaccess` est autorisé dans votre configuration Apache. Éditez `/etc/apache2/sites-available/000-default.conf` ou votre virtualhost :

```apache
<Directory /var/www/html/stats>
    AllowOverride All
    Require all granted
</Directory>
```

Puis redémarrez Apache :

```bash
sudo systemctl restart apache2
```

## 6. Accès aux statistiques

Accédez aux statistiques via votre navigateur :

```
http://votre-ip/stats/
```

Ou si vous avez un nom de domaine :

```
http://votre-domaine.com/stats/
```

## Options avancées

### Analyser plusieurs fichiers de log (y compris archives)

```bash
sudo zcat /var/log/apache2/access.log*.gz | goaccess /var/log/apache2/access.log - -o /var/www/html/stats/index.html --log-format=COMBINED
```

### Mode temps réel (dans le terminal)

```bash
goaccess /var/log/apache2/access.log --log-format=COMBINED
```

### Rapport en temps réel (WebSocket)

```bash
sudo goaccess /var/log/apache2/access.log -o /var/www/html/stats/index.html --log-format=COMBINED --real-time-html --ws-url=ws://votre-ip:7890
```

## Dépannage

### Les stats ne s'affichent pas
- Vérifiez les permissions : `ls -la /var/www/html/stats/`
- Vérifiez les logs Apache : `sudo tail -f /var/log/apache2/error.log`

### L'authentification ne fonctionne pas
- Vérifiez que `AllowOverride All` est activé
- Vérifiez les permissions du fichier `.htpasswd` : `sudo chmod 644 /etc/apache2/.htpasswd`

### Pas de données affichées
- Vérifiez que le fichier de log existe : `ls -lh /var/log/apache2/access.log`
- Vérifiez le format de log dans `/etc/apache2/apache2.conf` (devrait être LogFormat combined)

## Ressources

- Documentation officielle : https://goaccess.io/
- Configuration Apache : https://httpd.apache.org/docs/
