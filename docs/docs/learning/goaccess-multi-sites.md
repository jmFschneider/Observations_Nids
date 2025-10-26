# Configuration GoAccess Multi-Sites

> **Guide avancé** : Statistiques séparées pour meteo-poelley50.fr et observation-nids.meteo-poelley50.fr

## Vue d'ensemble

Ce guide décrit la configuration avancée de GoAccess pour générer des **rapports séparés** pour chaque site hébergé sur le serveur, avec un **tableau de bord centralisé**.

### Fonctionnalités

✅ **Rapports séparés** par site (météo vs observations)
✅ **Tableau de bord** avec vue d'ensemble
✅ **Rapport global** combinant tous les sites
✅ **Génération automatique** via cron
✅ **Protection par authentification** HTTP Basic

### Structure des rapports

```
/stats/
├── index.html              ← Tableau de bord principal
├── meteo/
│   └── index.html          ← Stats meteo-poelley50.fr
├── observations/
│   └── index.html          ← Stats observation-nids.meteo-poelley50.fr
└── global/
    └── index.html          ← Stats combinées (tous sites)
```

### Données disponibles dans chaque rapport

GoAccess génère automatiquement les statistiques suivantes :

| Panneau | Description |
|---------|-------------|
| **Visiteurs uniques** | Nombre de visiteurs uniques par jour, heure |
| **Fichiers demandés** | Pages les plus consultées avec nombre de visites |
| **Pages statiques** | CSS, JS, images |
| **Codes HTTP** | 200, 404, 500, etc. |
| **Hôtes** | Adresses IP des visiteurs |
| **Systèmes d'exploitation** | Windows, Linux, macOS, Android, iOS |
| **Navigateurs** | Chrome, Firefox, Safari, Edge |
| **Temps de réponse** | Latence serveur |
| **Géolocalisation** | Pays d'origine (si GeoIP configuré) |
| **URLs référentes** | Sites sources du trafic |
| **Recherches** | Termes de recherche |
| **Bande passante** | Volume de données transférées |

---

## Installation

### Prérequis

- GoAccess installé : `sudo apt install goaccess`
- Logs Apache actifs
- Accès sudo au serveur

### Étape 1 : Transférer le script

Depuis votre machine de développement, transférez le script vers le serveur :

```bash
# Depuis votre PC (répertoire du projet)
scp scripts/generate_stats.sh pi@meteo-poelley50.fr:/tmp/

# Sur le serveur
ssh pi@meteo-poelley50.fr
sudo mv /tmp/generate_stats.sh /usr/local/bin/
sudo chmod +x /usr/local/bin/generate_stats.sh
```

### Étape 2 : Première génération manuelle

Testez le script pour vérifier qu'il fonctionne :

```bash
sudo /usr/local/bin/generate_stats.sh
```

**Sortie attendue :**

```
[2025-10-26 10:30:00] INFO: === Génération des statistiques GoAccess ===
[2025-10-26 10:30:00] INFO: Vérification des prérequis...
[2025-10-26 10:30:00] INFO: Prérequis OK
[2025-10-26 10:30:00] INFO: Création de la structure de répertoires...
[2025-10-26 10:30:00] INFO: Répertoires créés
[2025-10-26 10:30:01] INFO: Génération des statistiques du site météo...
[2025-10-26 10:30:05] INFO: ✓ Statistiques météo générées
[2025-10-26 10:30:05] INFO: Génération des statistiques Observations Nids...
[2025-10-26 10:30:09] INFO: ✓ Statistiques Observations Nids générées
[2025-10-26 10:30:09] INFO: Génération des statistiques globales...
[2025-10-26 10:30:15] INFO: ✓ Statistiques globales générées
[2025-10-26 10:30:15] INFO: Génération du tableau de bord...
[2025-10-26 10:30:15] INFO: ✓ Tableau de bord généré
[2025-10-26 10:30:15] INFO: === Génération terminée avec succès ===
```

### Étape 3 : Vérifier l'accès web

Accédez aux statistiques via votre navigateur :

- **Tableau de bord** : http://meteo-poelley50.fr/stats/
- **Site météo** : http://meteo-poelley50.fr/stats/meteo/
- **Observations** : http://meteo-poelley50.fr/stats/observations/
- **Vue globale** : http://meteo-poelley50.fr/stats/global/

L'authentification HTTP Basic sera demandée (voir [Configuration Apache](configuration-apache-stats.md)).

### Étape 4 : Automatisation avec cron

Modifiez la tâche cron existante pour utiliser le nouveau script :

```bash
sudo crontab -e
```

**Remplacez** l'ancienne ligne :
```
0 * * * * goaccess /var/log/apache2/access.log -o /var/www/html/stats/index.html --log-format=COMBINED
```

**Par** :
```
0 * * * * /usr/local/bin/generate_stats.sh >> /var/log/goaccess.log 2>&1
```

Cela génère les statistiques **toutes les heures** et enregistre les logs dans `/var/log/goaccess.log`.

**Variante : Mise à jour toutes les 30 minutes**
```
*/30 * * * * /usr/local/bin/generate_stats.sh >> /var/log/goaccess.log 2>&1
```

---

## Utilisation

### Tableau de bord

La page d'accueil (`/stats/`) affiche :

1. **Vue d'ensemble** : Nombre de requêtes par site aujourd'hui
2. **Liens vers les rapports** : Météo, Observations, Global
3. **Dernière mise à jour** : Horodatage de génération

### Rapports détaillés

Cliquez sur un des rapports pour accéder aux statistiques complètes :

#### 📊 Exemple : Pages les plus visitées

Dans le panneau **"Requested Files (URLs)"** :

| URL | Visites | Visiteurs uniques | Bande passante |
|-----|---------|-------------------|----------------|
| `/` | 1,234 | 456 | 2.3 MB |
| `/observations/liste/` | 567 | 123 | 890 KB |
| `/admin/` | 45 | 12 | 234 KB |

#### 👥 Exemple : Visiteurs par jour

Dans le panneau **"Unique visitors per day"** :

| Date | Visiteurs uniques |
|------|-------------------|
| 26/10/2025 | 78 |
| 25/10/2025 | 92 |
| 24/10/2025 | 65 |

#### 🌍 Exemple : Adresses IP

Dans le panneau **"Hosts"** :

| IP | Visites | Pays |
|----|---------|------|
| 192.168.1.50 | 234 | France |
| 84.123.45.67 | 45 | France |
| 185.234.12.8 | 12 | Belgique |

---

## Configuration avancée

### Personnalisation du script

Éditez `/usr/local/bin/generate_stats.sh` pour modifier :

#### Fréquence de mise à jour

Changez la tâche cron (voir Étape 4).

#### Ajout d'analyses historiques

Pour inclure les logs archivés (`.gz`) :

```bash
# Dans la fonction generate_meteo_stats()
zcat /var/log/apache2/access.log*.gz | \
goaccess /var/log/apache2/access.log - \
    -o "$METEO_HTML" \
    $GOACCESS_OPTS \
    --html-report-title="Statistiques meteo-poelley50.fr (historique)"
```

#### Filtres personnalisés

Exclure certaines IPs (ex: votre IP locale) :

```bash
# Dans la fonction generate_django_stats()
grep -v "192.168.1.50" "$DJANGO_LOG" | \
goaccess - \
    -o "$DJANGO_HTML" \
    $GOACCESS_OPTS
```

#### Rapport par période

Analyser uniquement les 7 derniers jours :

```bash
# Filtrer par date
awk -v d="$(date --date='7 days ago' +%d/%b/%Y)" '$4 > "["d' "$DJANGO_LOG" | \
goaccess - -o "$DJANGO_HTML" $GOACCESS_OPTS
```

### Configuration GoAccess

Le fichier `/goaccess/goaccess.conf` permet de personnaliser l'affichage.

**Exemple : Activer la géolocalisation**

```bash
sudo nano /goaccess/goaccess.conf
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

## Cas d'usage

### 1. Analyser les pages les plus visitées

**Objectif** : Identifier les pages populaires pour optimiser le contenu

1. Ouvrir `/stats/observations/`
2. Panneau **"Requested Files (URLs)"**
3. Trier par "Hits" (clics)

### 2. Identifier les utilisateurs actifs

**Objectif** : Voir combien d'utilisateurs reviennent régulièrement

1. Ouvrir `/stats/observations/`
2. Panneau **"Hosts"**
3. Les IPs avec le plus de visites = utilisateurs actifs

### 3. Détecter les erreurs 404

**Objectif** : Trouver les liens cassés

1. Ouvrir `/stats/global/`
2. Panneau **"HTTP Status Codes"**
3. Chercher "404 Not Found"
4. Voir quelles URLs génèrent des 404

### 4. Analyser les heures de pointe

**Objectif** : Savoir quand optimiser le serveur

1. Ouvrir `/stats/meteo/`
2. Panneau **"Hourly"**
3. Voir les heures avec le plus de trafic

### 5. Comparer les deux sites

**Objectif** : Voir quel site est le plus visité

1. Ouvrir `/stats/` (tableau de bord)
2. Comparer les chiffres "requêtes aujourd'hui"
3. Ouvrir `/stats/global/` pour analyse détaillée

---

## Dépannage

### Le script échoue

**Vérifier les permissions :**
```bash
ls -la /usr/local/bin/generate_stats.sh
sudo chmod +x /usr/local/bin/generate_stats.sh
```

**Vérifier les logs :**
```bash
sudo cat /var/log/goaccess.log
```

### Les rapports sont vides

**Vérifier que les logs existent :**
```bash
ls -lh /var/log/apache2/access.log
ls -lh /var/log/apache2/django-access.log
```

**Vérifier qu'ils contiennent des données :**
```bash
tail -20 /var/log/apache2/django-access.log
```

### L'authentification ne fonctionne pas

Voir [Configuration Apache pour /stats](configuration-apache-stats.md#5-protection-par-authentification).

### Le tableau de bord ne s'affiche pas correctement

**Vérifier les permissions :**
```bash
ls -la /var/www/html/stats/
sudo chown -R www-data:www-data /var/www/html/stats
```

### Les compteurs sont à zéro

Les compteurs du tableau de bord (`requêtes aujourd'hui`) comptent les lignes du fichier `access.log` actuel. Si le fichier a été rotaté (logrotate), le compteur repart de zéro.

Pour compter les dernières 24h, modifiez le script :

```bash
# Remplacer dans la fonction generate_dashboard()
METEO_VISITS=$(grep "$(date +'%d/%b/%Y')" "$METEO_LOG" 2>/dev/null | wc -l || echo "0")
```

---

## Optimisations

### Performance

Pour de gros logs (> 10 MB), GoAccess peut être lent. Optimisations :

1. **Filtrer par période** : Analyser seulement les 30 derniers jours
2. **Utiliser un cache** : GoAccess supporte `--persist` pour garder les données en mémoire
3. **Générer en arrière-plan** : Le cron le fait déjà

### Stockage

Les fichiers HTML générés peuvent être volumineux. Pour économiser de l'espace :

```bash
# Compresser les anciens rapports (si vous en sauvegardez)
find /var/www/html/stats/ -name "*.html" -mtime +30 -exec gzip {} \;
```

---

## Voir aussi

- **[Installation GoAccess](goaccess-installation.md)** - Installation de base
- **[Configuration Apache](configuration-apache-stats.md)** - Configuration VirtualHost

## Ressources externes

- [Documentation GoAccess officielle](https://goaccess.io/)
- [GoAccess sur GitHub](https://github.com/allinurl/goaccess)
- [Format de log Apache](https://httpd.apache.org/docs/current/logs.html)

---

**Date de création** : 26 octobre 2025
**Auteur** : Claude Code
**Version** : 1.0
