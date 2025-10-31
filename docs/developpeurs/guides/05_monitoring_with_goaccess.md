# Guide de Monitoring avec GoAccess

Ce guide complet vous accompagnera dans l'installation, la configuration et l'utilisation avancée de GoAccess pour le suivi des statistiques web de vos sites hébergés sur un serveur Linux (Raspberry Pi, Debian/Ubuntu).

## 📋 Table des matières

1.  [Installation de GoAccess](#1-installation-de-goaccess)
2.  [Configuration de base](#2-configuration-de-base)
3.  [Protection par authentification](#3-protection-par-authentification)
4.  [Configuration Apache pour /stats](#4-configuration-apache-pour-stats)
5.  [Configuration GoAccess Multi-Sites](#5-configuration-goaccess-multi-sites)
    *   [Filtrage Bots vs Humains](#filtrage-bots-vs-humains)
    *   [Installation du script Multi-Sites](#installation-du-script-multi-sites)
    *   [Utilisation du tableau de bord Multi-Sites](#utilisation-du-tableau-de-bord-multi-sites)
6.  [Options avancées et personnalisation](#6-options-avancées-et-personnalisation)
7.  [Dépannage](#7-dépannage)
8.  [Ressources externes](#8-ressources-externes)

---

## 1. Installation de GoAccess

### Prérequis

*   Serveur Linux (Raspberry Pi, Debian/Ubuntu) avec Apache2 ou Nginx installé.
*   Accès `sudo` au serveur.
*   Logs Apache/Nginx actifs dans `/var/log/apache2/` ou `/var/log/nginx/`.

### Procédure d'installation

```bash
sudo apt update
sudo apt install goaccess
```

---

## 2. Configuration de base

### 2.1. Création du répertoire pour les statistiques

Créez un dossier dédié dans votre arborescence web où les rapports HTML seront générés :

```bash
sudo mkdir -p /var/www/html/stats
sudo chown www-data:www-data /var/www/html/stats
```

### 2.2. Génération du rapport HTML initial

Générez le premier rapport à partir de vos logs Apache/Nginx. Adaptez le chemin du log et le format si nécessaire (par exemple, `COMBINED` pour Apache, ou un format Nginx spécifique).

```bash
sudo goaccess /var/log/apache2/access.log -o /var/www/html/stats/index.html --log-format=COMBINED
```

**Options :**

*   `/var/log/apache2/access.log` : fichier de log à analyser (remplacez par votre log Nginx si applicable).
*   `-o /var/www/html/stats/index.html` : fichier de sortie HTML.
*   `--log-format=COMBINED` : format des logs (par exemple, `COMBINED` pour Apache, ou `NCSA_COMBINED` pour Nginx).

### 2.3. Automatisation avec cron

Pour mettre à jour automatiquement les statistiques toutes les heures (ou à la fréquence désirée) :

```bash
sudo crontab -e
```

Ajoutez cette ligne à la fin du fichier (adaptez le chemin du log et le format) :

```
0 * * * * goaccess /var/log/apache2/access.log -o /var/www/html/stats/index.html --log-format=COMBINED
```

**Explication :** `0 * * * *` = à la minute 0 de chaque heure.

---

## 3. Protection par authentification

Il est crucial de protéger l'accès à vos rapports de statistiques. Cette section décrit comment mettre en place une authentification HTTP Basic avec Apache.

### 3.1. Créer un utilisateur avec mot de passe

```bash
sudo htpasswd -c /etc/apache2/.htpasswd admin
```

Entrez le mot de passe quand demandé. Pour ajouter d'autres utilisateurs (sans l'option `-c`, qui recrée le fichier) :

```bash
sudo htpasswd /etc/apache2/.htpasswd autre_utilisateur
```

### 3.2. Créer le fichier .htaccess

Créez le fichier `/var/www/html/stats/.htaccess` avec ce contenu :

```apache
AuthType Basic
AuthName "Statistiques du site"
AuthUserFile /etc/apache2/.htpasswd
Require valid-user
```

### 3.3. Activer .htaccess dans Apache (si nécessaire)

Vérifiez que `.htaccess` est autorisé dans votre configuration Apache. Éditez le fichier de configuration de votre VirtualHost (par exemple, `/etc/apache2/sites-available/000-default.conf` ou votre fichier de site spécifique) et assurez-vous que la directive `AllowOverride All` est présente pour le répertoire `/var/www/html/stats` :

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

---

## 4. Configuration Apache pour /stats

Ce document décrit la configuration Apache nécessaire pour accéder aux statistiques GoAccess via une URL spécifique, par exemple `http://votre-domaine.fr/stats/`.

### 4.1. Contexte

Si vous hébergez plusieurs sites ou applications (par exemple, un site principal et une application Django), vous devrez configurer Apache pour router correctement les requêtes vers le répertoire des statistiques.

### 4.2. Localiser le fichier de configuration de votre site

Les fichiers de configuration Apache se trouvent généralement dans `/etc/apache2/sites-available/`.

```bash
# Lister les configurations disponibles
ls -la /etc/apache2/sites-available/

# Voir les sites actifs
ls -la /etc/apache2/sites-enabled/

# Trouver le fichier de configuration de votre VirtualHost principal
```

### 4.3. Configuration à ajouter pour /stats

Dans le fichier de configuration de votre **VirtualHost principal**, ajoutez ces directives **avant la fermeture du `</VirtualHost>`** :

```apache
# Statistiques GoAccess
Alias /stats /var/www/html/stats
<Directory /var/www/html/stats>
    AllowOverride All
    Require all granted
</Directory>
```

### 4.4. Tester et appliquer la configuration

```bash
# Tester la syntaxe
sudo apache2ctl configtest

# Si OK, redémarrer Apache
sudo systemctl restart apache2
```

### 4.5. Vérifier l'accès

Accédez à `http://votre-domaine.fr/stats/` dans un navigateur. L'authentification vous sera demandée.

---

## 5. Configuration GoAccess Multi-Sites

Ce guide décrit la configuration avancée de GoAccess pour générer des **rapports séparés** pour chaque site hébergé sur le serveur, avec un **tableau de bord centralisé**.

### Fonctionnalités

✅ **Rapports séparés** par site (par exemple, site météo vs application Observations Nids)
✅ **Filtrage bots vs humains** - Statistiques distinctes pour visiteurs réels et robots
✅ **Tableau de bord** avec vue d'ensemble et statistiques humains/bots
✅ **Rapport global** combinant tous les sites
✅ **Génération automatique** via cron
✅ **Protection par authentification** HTTP Basic

### Structure des rapports

```
/stats/
├── index.html              ← Tableau de bord principal (avec stats humains/bots)
├── meteo/
│   ├── index.html          ← Stats meteo-poelley50.fr (humains uniquement)
│   └── bots.html           ← Stats meteo-poelley50.fr (bots uniquement)
├── observations/
│   ├── index.html          ← Stats observation-nids (humains uniquement)
│   └── bots.html           ← Stats observation-nids (bots uniquement)
└── global/
    ├── index.html          ← Stats combinées (humains uniquement)
    └── bots.html           ← Stats combinées (bots uniquement)
```

### Filtrage Bots vs Humains

Les bots peuvent représenter une part significative du trafic. Filtrer les bots permet de :

1.  **Voir le trafic réel** : Nombre de visiteurs humains.
2.  **Analyser le comportement utilisateur** : Pages consultées par de vraies personnes.
3.  **Identifier les bots problématiques** : Scanners agressifs, scrapers.

Le script `generate_stats_v2.sh` analyse le **User-Agent** de chaque requête HTTP pour distinguer les bots des humains. Il utilise une liste de patterns pour détecter les bots.

Pour chaque site, **2 rapports** sont créés :

1.  **`index.html`** (humains) : Visiteurs réels uniquement.
2.  **`bots.html`** (bots) : Robots uniquement.

### Installation du script Multi-Sites

#### Prérequis

*   GoAccess installé : `sudo apt install goaccess`
*   Logs Apache/Nginx actifs.
*   Accès `sudo` au serveur.
*   Le script `generate_stats_v2.sh` (disponible dans le répertoire `scripts/` du projet).

#### Procédure

1.  **Transférer le script**

    Depuis votre machine de développement, transférez le script `generate_stats_v2.sh` vers le serveur :

    ```bash
    # Depuis votre PC (répertoire du projet)
    scp scripts/generate_stats_v2.sh pi@votre-serveur:/tmp/

    # Sur le serveur
    ssh pi@votre-serveur
    sudo mv /tmp/generate_stats_v2.sh /usr/local/bin/
    sudo chmod +x /usr/local/bin/generate_stats_v2.sh

    # IMPORTANT : Convertir en format Unix (fin de lignes) si nécessaire
    sudo apt install dos2unix # Installer si non présent
    sudo dos2unix /usr/local/bin/generate_stats_v2.sh
    ```

2.  **Première génération manuelle**

    Testez le script pour vérifier qu'il fonctionne :

    ```bash
    sudo /usr/local/bin/generate_stats_v2.sh
    ```

    La sortie affichera le processus de génération des rapports pour chaque site et le résumé des requêtes humains/bots.

3.  **Automatisation avec cron**

    Modifiez la tâche cron existante pour utiliser le nouveau script :

    ```bash
sudo crontab -e
    ```

    **Remplacez** l'ancienne ligne (si elle existe) :

    ```
    0 * * * * goaccess /var/log/apache2/access.log -o /var/www/html/stats/index.html --log-format=COMBINED
    ```

    **Par** :

    ```
    0 * * * * /usr/local/bin/generate_stats_v2.sh >> /var/log/goaccess.log 2>&1
    ```

    Cela génère les statistiques **toutes les heures** et enregistre les logs dans `/var/log/goaccess.log`.

### Utilisation du tableau de bord Multi-Sites

Accédez aux statistiques via votre navigateur :

*   **Tableau de bord principal :** `http://votre-domaine.fr/stats/`
*   **Rapports par site (humains) :**
    *   `http://votre-domaine.fr/stats/meteo/` (exemple)
    *   `http://votre-domaine.fr/stats/observations/` (exemple)
    *   `http://votre-domaine.fr/stats/global/`
*   **Rapports bots :**
    *   `http://votre-domaine.fr/stats/meteo/bots.html`
    *   `http://votre-domaine.fr/stats/observations/bots.html`
    *   `http://votre-domaine.fr/stats/global/bots.html`

L'authentification HTTP Basic sera demandée (voir [Protection par authentification](#3-protection-par-authentification)).

---

## 6. Options avancées et personnalisation

### 6.1. Analyser plusieurs fichiers de log (y compris archives)

```bash
sudo zcat /var/log/apache2/access.log*.gz | goaccess /var/log/apache2/access.log - -o /var/www/html/stats/index.html --log-format=COMBINED
```

### 6.2. Mode temps réel (dans le terminal)

```bash
goaccess /var/log/apache2/access.log --log-format=COMBINED
```

### 6.3. Rapport en temps réel (WebSocket)

```bash
sudo goaccess /var/log/apache2/access.log -o /var/www/html/stats/index.html --log-format=COMBINED --real-time-html --ws-url=ws://votre-ip:7890
```

### 6.4. Personnalisation du script Multi-Sites

Éditez `/usr/local/bin/generate_stats_v2.sh` pour modifier :

*   **Fréquence de mise à jour** : Changez la tâche cron.
*   **Ajout d'analyses historiques** : Modifiez les commandes `goaccess` pour inclure les logs archivés (`.gz`).
*   **Filtres personnalisés** : Exclure certaines IPs (ex: votre IP locale) en utilisant `grep -v "<IP_A_EXCLURE>"`.
*   **Rapport par période** : Utilisez `awk` pour filtrer les logs par date.

### 6.5. Configuration GoAccess (fichier `goaccess.conf`)

Le fichier `/etc/goaccess/goaccess.conf` permet de personnaliser l'affichage et les fonctionnalités.

**Exemple : Activer la géolocalisation**

```bash
sudo nano /etc/goaccess/goaccess.conf
```

Ajoutez :

```conf
geoip-database /usr/share/GeoIP/GeoLite2-City.mmdb
```

Puis installez GeoIP :

```bash
sudo apt install geoip-database libmaxminddb0
```

---

## 7. Dépannage

### 7.1. Le script/GoAccess échoue

*   **Vérifier les permissions :** `ls -la /usr/local/bin/generate_stats_v2.sh` et `sudo chmod +x /usr/local/bin/generate_stats_v2.sh`.
*   **Vérifier les logs :** `sudo cat /var/log/goaccess.log` (pour le script multi-sites) ou les logs Apache/Nginx.

### 7.2. Les rapports sont vides ou ne s'affichent pas

*   **Vérifiez que le répertoire `/var/www/html/stats/` existe et a les bonnes permissions :** `ls -la /var/www/html/stats/` et `sudo chown -R www-data:www-data /var/www/html/stats`.
*   **Vérifiez que les fichiers de log existent et contiennent des données :** `ls -lh /var/log/apache2/access.log` et `tail -20 /var/log/apache2/access.log`.
*   **Vérifiez le format de log** utilisé par GoAccess (`--log-format`) correspond bien à celui de vos logs Apache/Nginx.

### 7.3. L'authentification ne fonctionne pas

*   Vérifiez que `AllowOverride All` est activé pour le répertoire `/var/www/html/stats` dans votre configuration Apache.
*   Vérifiez les permissions du fichier `.htpasswd` : `sudo chmod 644 /etc/apache2/.htpasswd`.

### 7.4. Les compteurs sont à zéro ou ne se mettent pas à jour

Les compteurs du tableau de bord (`requêtes aujourd'hui`) comptent les lignes du fichier `access.log` actuel. Si le fichier a été rotaté (logrotate), le compteur repart de zéro. Pour une analyse sur une période plus longue, configurez le script pour inclure les logs archivés (`.gz`).

---

## 8. Ressources externes

*   [Documentation officielle GoAccess](https://goaccess.io/)
*   [GoAccess sur GitHub](https://github.com/allinurl/goaccess)
*   [Documentation Apache VirtualHost](https://httpd.apache.org/docs/2.4/vhosts/)
*   [Format de log Apache](https://httpd.apache.org/docs/current/logs.html)

---

**Document créé le** : 31 octobre 2025
**Auteur** : Gemini
**Version** : 1.0 (Fusion des guides GoAccess)