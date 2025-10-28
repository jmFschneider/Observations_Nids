# Configuration Apache pour l'accès à /stats

## Contexte

Ce document décrit la configuration Apache nécessaire pour accéder aux statistiques GoAccess via `http://meteo-poelley50.fr/stats/`.

## Architecture du serveur

Le serveur héberge **deux VirtualHosts distincts** :

### 1. Site météo principal (meteo-poelley50.fr)
- **Racine `/`** → WeeWX (Belchertown) dans `/var/www/html/weewx`
- **`/phpmyadmin/`** → phpMyAdmin
- **`/stats/`** → GoAccess (à configurer)

### 2. Application Django (observation-nids.meteo-poelley50.fr)
- Application Observations_Nids avec WSGI
- Configuration séparée avec son propre VirtualHost

## Fichiers de configuration sur le serveur

Les fichiers de configuration se trouvent dans `/etc/apache2/sites-available/`

### Localiser le fichier du site principal

```bash
# Lister les configurations disponibles
ls -la /etc/apache2/sites-available/

# Voir les sites actifs
ls -la /etc/apache2/sites-enabled/

# Trouver celui qui contient "weewx"
grep -r "weewx" /etc/apache2/sites-available/
```

## Configuration à ajouter pour /stats

Dans le fichier de configuration du **site météo principal**, ajouter ces directives **avant la fermeture du `</VirtualHost>`** :

```apache
# Statistiques GoAccess
Alias /stats /var/www/html/stats
<Directory /var/www/html/stats>
    AllowOverride All
    Require all granted
</Directory>
```

### Exemple de configuration complète du site principal

```apache
<VirtualHost *:80>
    ServerName meteo-poelley50.fr
    ServerAlias www.meteo-poelley50.fr
    ServerAdmin webmaster@localhost
    DocumentRoot /var/www/html/weewx

    # Répertoire principal WeeWX
    <Directory /var/www/html/weewx>
        Options Indexes FollowSymLinks
        AllowOverride None
        Require all granted
    </Directory>

    # Statistiques GoAccess
    Alias /stats /var/www/html/stats
    <Directory /var/www/html/stats>
        AllowOverride All
        Require all granted
    </Directory>

    # phpMyAdmin (si pas déjà configuré via conf.d)
    Alias /phpmyadmin /usr/share/phpmyadmin
    <Directory /usr/share/phpmyadmin>
        Options SymLinksIfOwnerMatch
        DirectoryIndex index.php
        AllowOverride All
        Require all granted
    </Directory>

    # Logs
    ErrorLog ${APACHE_LOG_DIR}/weewx-error.log
    CustomLog ${APACHE_LOG_DIR}/weewx-access.log combined

    # Redirection HTTP vers HTTPS (si SSL configuré)
    # RewriteEngine on
    # RewriteCond %{SERVER_NAME} =meteo-poelley50.fr [OR]
    # RewriteCond %{SERVER_NAME} =www.meteo-poelley50.fr
    # RewriteRule ^ https://%{SERVER_NAME}%{REQUEST_URI} [END,NE,R=permanent]
</VirtualHost>
```

## Procédure d'installation

### 1. Éditer la configuration Apache

```bash
# Remplacer 'XXX.conf' par le nom réel du fichier
sudo nano /etc/apache2/sites-available/XXX.conf
```

### 2. Ajouter les directives pour /stats

Copier le bloc suivant dans le fichier, avant `</VirtualHost>` :

```apache
# Statistiques GoAccess
Alias /stats /var/www/html/stats
<Directory /var/www/html/stats>
    AllowOverride All
    Require all granted
</Directory>
```

### 3. Tester et appliquer la configuration

```bash
# Tester la syntaxe
sudo apache2ctl configtest

# Si OK, redémarrer Apache
sudo systemctl restart apache2
```

### 4. Vérifier l'accès

Accéder à `http://meteo-poelley50.fr/stats/` dans un navigateur.

## Amélioration : Analyse des logs combinés

Actuellement, GoAccess analyse uniquement le log WeeWX. Pour analyser **les deux sites** (WeeWX et Observations_Nids), modifier la tâche cron :

```bash
sudo crontab -e
```

Remplacer la ligne existante par :

```bash
0 * * * * goaccess /var/log/apache2/weewx-access.log /var/log/apache2/observations-nids-access.log -o /var/www/html/stats/index.html --log-format=COMBINED
```

**Note** : Vérifier les noms exacts des fichiers de log avec :

```bash
ls -la /var/log/apache2/
```

## Points importants

1. **AllowOverride All** : Permet au fichier `.htaccess` dans `/stats` de fonctionner pour l'authentification HTTP Basic
2. **Ordre des directives** : Dans le VirtualHost Django, les `Alias` doivent être avant `WSGIScriptAlias /`
3. **DocumentRoot différent** : Le site météo a `DocumentRoot /var/www/html/weewx`, le site Django a `DocumentRoot /var/www/html`
4. **Logs séparés** : Chaque VirtualHost a ses propres fichiers de log pour faciliter le débogage

## Dépannage

### /stats renvoie une erreur 404

```bash
# Vérifier que le répertoire existe
ls -la /var/www/html/stats/

# Vérifier les permissions
sudo chown -R www-data:www-data /var/www/html/stats
```

### L'authentification ne fonctionne pas

```bash
# Vérifier que le fichier .htpasswd existe
ls -la /etc/apache2/.htpasswd

# Vérifier le fichier .htaccess
cat /var/www/html/stats/.htaccess
```

### Les statistiques ne se mettent pas à jour

```bash
# Vérifier les tâches cron
sudo crontab -l

# Tester la génération manuelle
sudo goaccess /var/log/apache2/weewx-access.log -o /var/www/html/stats/index.html --log-format=COMBINED
```

## Voir aussi

- **[Installation GoAccess](goaccess-installation.md)** - Guide complet d'installation et configuration
- **[GoAccess Multi-Sites](goaccess-multi-sites.md)** - Configuration avancée avec rapports séparés par site

## Ressources externes

- Documentation Apache VirtualHost : https://httpd.apache.org/docs/2.4/vhosts/
