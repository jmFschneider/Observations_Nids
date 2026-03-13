# Déploiement Production — OVH Public Cloud

Guide complet pour déployer Observations Nids en production sur un VPS ou une instance OVH Public Cloud.
Rédigé à partir d'un déploiement réel effectué en mars 2026.

## Architecture

```
Internet (HTTPS :443)
    ↓
Nginx Docker  ← gère SSL directement (Let's Encrypt)
    ↓
Gunicorn (Django) :8000
    ↓
MariaDB / Redis / Celery  (réseau Docker interne : observations_network)
```

**Différences clés avec l'environnement pilote :**

| Pilote (home lab) | Production OVH |
|-------------------|----------------|
| Apache (.100) termine SSL → Nginx (.120:8010) | Nginx Docker gère SSL directement |
| Nginx écoute sur :8010 | Nginx écoute sur :80 et :443 |
| Flower exposé sur LAN (192.168.19.x) | Flower accessible uniquement via SSH tunnel |
| `SESSION_COOKIE_SECURE=False` | `SESSION_COOKIE_SECURE=True` |

---

## Authentification — Vue d'ensemble

Le système utilise plusieurs couches d'authentification indépendantes :

| Service | Couche | Credentials |
|---------|--------|-------------|
| SSH serveur | Clé SSH | Clé privée `~/.ssh/id_ed25519` sur le poste admin |
| Application Django | Login Django | Compte créé dans l'application |
| Admin Django `/admin/` | Login Django | Compte superuser (`DJANGO_SUPERUSER_*` dans `.env.prod`) |
| phpMyAdmin `/phpmyadmin/` | **1. HTTP Basic Auth** | Login/mdp choisi lors de `setup-phpmyadmin-auth.sh` |
| phpMyAdmin (interface) | **2. Login MariaDB** | `root` / `DB_ROOT_PASSWORD` du `.env.prod` |
| Flower (SSH tunnel) | Tunnel SSH | Clé SSH du poste admin |

> **phpMyAdmin = double authentification** : il faut passer la Basic Auth Nginx (premier écran navigateur),
> puis saisir les credentials MariaDB dans l'interface phpMyAdmin.

---

## Prérequis

- Instance OVH Public Cloud Ubuntu 22.04 LTS (B3-8 : 2 vCores, 8 Go RAM recommandés)
- Domaine pointant vers l'IP publique de l'instance (enregistrement A dans le gestionnaire DNS)
- Docker installé sur l'instance (voir section ci-dessous)
- Clé SSH configurée sur le poste de développement

> **Groupe de sécurité OVH** : le groupe de sécurité par défaut sur OVH Public Cloud autorise
> tout le trafic entrant (Ingress Any Any 0.0.0.0/0). Il n'y a pas de règles à ajouter.
> Il est visible dans l'interface **Horizon** (Project → Network → Security Groups),
> accessible depuis le Manager OVH → Public Cloud → Management Interface → Horizon.

---

## 1. Préparation du serveur

### Connexion SSH

```bash
ssh ubuntu@[IP-OVH]
```

### Installation de Docker

```bash
sudo apt update && sudo apt upgrade -y
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker ubuntu
# Se déconnecter puis se reconnecter pour que le groupe soit actif
exit
```

Vérifier :
```bash
docker --version
docker compose version
```

### Correction du réseau Docker (spécifique OVH Public Cloud)

Les instances OVH Public Cloud ont **deux interfaces réseau** :
- `ens3` → IP publique (ex: 135.125.72.x) — accès Internet
- `ens4` → IP privée OVH (ex: 10.1.0.x) — réseau interne OVH

Docker a deux problèmes sur cette configuration :

**Problème 1 — Build impossible** : pendant `docker compose build`, `apt-get update` échoue
("No route to host") car Docker route ses paquets aléatoirement entre `ens3` et `ens4`.
Quand les paquets passent par `ens4`, ils n'atteignent pas Internet.

**Problème 2 — Site inaccessible** : Docker Compose crée un bridge dédié pour le réseau
`observations_network` (ex: `br-85826af17032`). La chaîne FORWARD d'iptables a une
politique DROP par défaut et ne connaît pas ce bridge. Les réponses des conteneurs sont
donc bloquées avant d'atteindre le client.

**Vérifier les interfaces et identifier le bridge Docker :**
```bash
# Interfaces réseau
ip route | grep default
# Doit afficher deux routes : ens3 (IP publique) et ens4 (IP privée)

# Identifier le bridge du réseau Docker Compose (après démarrage du stack)
ip link show | grep br-
# Note le nom du bridge (ex: br-85826af17032)
```

**Correction complète :**

Remplacer `135.125.72.1` par le gateway de `ens3` affiché dans `ip route`,
et `br-XXXXXXXX` par le bridge identifié ci-dessus.

```bash
# 1. Configurer le daemon Docker
sudo nano /etc/docker/daemon.json
```

Contenu :
```json
{
    "dns": ["8.8.8.8", "1.1.1.1"],
    "ipv6": false
}
```

```bash
sudo systemctl restart docker

# 2. Forcer le routage du réseau par défaut (docker0) via ens3
sudo iptables -t nat -A POSTROUTING -s 172.17.0.0/16 ! -o docker0 -j MASQUERADE
sudo ip route add default via 135.125.72.1 dev ens3 table 200
sudo ip rule add from 172.17.0.0/16 table 200 pref 100

# 3. Forcer le routage du réseau observations_network (172.18.x.x) via ens3
#    (à faire APRÈS le premier démarrage du stack, une fois le bridge créé)
sudo iptables -I FORWARD 1 -i br-XXXXXXXX -o ens3 -j ACCEPT
sudo iptables -I FORWARD 2 -i ens3 -o br-XXXXXXXX -m conntrack --ctstate RELATED,ESTABLISHED -j ACCEPT
sudo iptables -t nat -A POSTROUTING -s 172.18.0.0/16 -o ens3 -j MASQUERADE
sudo ip route add default via 135.125.72.1 dev ens3 table 201
sudo ip rule add from 172.18.0.0/16 table 201 pref 101

# 4. Sauvegarder les règles iptables
sudo apt install iptables-persistent -y
sudo netfilter-persistent save

# 5. Persister les règles de routage (ip route / ip rule) dans /etc/rc.local
sudo nano /etc/rc.local
```

Contenu de `/etc/rc.local` (remplacer le gateway par celui de `ens3`) :
```bash
#!/bin/bash
# Routage politique pour Docker — forcer le trafic via ens3 (interface publique OVH)

# Table 200 : docker0 (172.17.0.0/16 — build Docker)
ip route replace default via 135.125.72.1 dev ens3 table 200
ip rule add from 172.17.0.0/16 lookup 200 pref 100 2>/dev/null || true

# Table 201 : br-* réseau Docker prod (172.18.0.0/16 — trafic runtime)
ip route replace default via 135.125.72.1 dev ens3 table 201
ip rule add from 172.18.0.0/16 lookup 201 pref 101 2>/dev/null || true

exit 0
```

```bash
sudo chmod +x /etc/rc.local
# Tester
sudo /etc/rc.local && echo "OK"
```

**Vérifier que le build peut accéder à Internet :**
```bash
docker run --rm alpine wget -qO- http://example.com 2>&1 | head -3
# Doit afficher le HTML d'example.com
```

> **Ordre des opérations** : la correction "Problème 1" (172.17.0.0/16) est nécessaire
> avant le build. La correction "Problème 2" (172.18.0.0/16, bridge `br-*`) est nécessaire
> après le premier démarrage du stack.

### Création des répertoires

```bash
sudo mkdir -p /opt/observations_nids/media /opt/observations_nids/logs
sudo chown -R ubuntu:ubuntu /opt/observations_nids
```

---

## 2. Déploiement du code

### Cloner le dépôt

```bash
# Cloner depuis /opt (pas depuis /opt/observations_nids)
cd /opt
sudo git clone https://github.com/jmFschneider/Observations_Nids.git observations_nids
sudo chown -R ubuntu:ubuntu /opt/observations_nids
mkdir -p /opt/observations_nids/media /opt/observations_nids/logs
```

> **Attention** : toujours cloner depuis `/opt` avec le nom de destination explicite.
> Ne jamais cloner depuis l'intérieur du répertoire cible (erreur "not an empty directory").

### Créer le fichier de configuration

```bash
cp /opt/observations_nids/docker/.env.prod.example /opt/observations_nids/.env.prod
nano /opt/observations_nids/.env.prod
```

Générer une `SECRET_KEY` :
```bash
python3 -c "import secrets; print(secrets.token_urlsafe(50))"
```

**Variables à renseigner obligatoirement :**

```env
SECRET_KEY=                    # Clé secrète Django (générée ci-dessus)
DB_PASSWORD=                   # Mot de passe fort pour l'utilisateur BDD
DB_ROOT_PASSWORD=              # Mot de passe root MariaDB (très fort)
DJANGO_SUPERUSER_PASSWORD=     # Mot de passe admin Django
GEMINI_API_KEY=                # Clé API Google Gemini
EMAIL_HOST_USER=               # Compte SMTP Brevo
EMAIL_HOST_PASSWORD=           # Mot de passe SMTP Brevo
```

**Point important — ALLOWED_HOSTS :**
```env
# Doit inclure à la fois le domaine ET localhost (pour le healthcheck Docker interne)
ALLOWED_HOSTS='["observation-nids.meteo-poelley50.fr","localhost"]'
```

**Variables pré-remplies dans le template :**
- `DEBUG=False`
- `SESSION_COOKIE_SECURE=True`
- `CSRF_COOKIE_SECURE=True`
- `CSRF_TRUSTED_ORIGINS` avec le domaine production

> Toutes les variables `DB_*`, `DJANGO_*`, etc. du `.env.prod` sont lues directement
> par `docker-compose.prod.yml` — pas besoin de modifier le `.yml`.

---

## 3. Certificat SSL (Let's Encrypt)

> **Important** : obtenir le certificat **avant** de démarrer le stack (Nginx doit être arrêté,
> le port 80 doit être libre). Utiliser `certbot` installé sur l'hôte, pas via Docker
> (les conteneurs ont un problème de connectivité IPv6 sortante sur OVH).

```bash
sudo apt install certbot -y
sudo certbot certonly --standalone \
  -d observation-nids.meteo-poelley50.fr \
  --email admin@meteo-poelley50.fr \
  --agree-tos --no-eff-email
```

Les certificats sont placés dans `/etc/letsencrypt/live/observation-nids.meteo-poelley50.fr/` :
```
cert.pem       # Certificat
chain.pem      # Chaîne intermédiaire
fullchain.pem  # Certificat + chaîne (utilisé par Nginx)
privkey.pem    # Clé privée
```

Ces fichiers appartiennent à `root` — c'est normal. Le conteneur Nginx peut les lire
via le volume mount `/etc/letsencrypt` car il tourne en `root` en interne.

---

## 4. Configuration des credentials phpMyAdmin

À effectuer une seule fois avant le premier démarrage :

```bash
cd /opt/observations_nids
bash docker/scripts/setup-phpmyadmin-auth.sh
```

Le script demande un **nom d'utilisateur** et un **mot de passe** — credentials propres
à la Basic Auth Nginx, indépendants de tout autre compte (Linux, Django, MariaDB).
**Retenir ces credentials** : ils seront demandés à chaque accès phpMyAdmin.

Le fichier `docker/nginx/auth/.htpasswd` est créé localement (non commité sur GitHub).

**Vérifier les permissions du fichier** (nginx doit pouvoir le lire) :
```bash
ls -la /opt/observations_nids/docker/nginx/auth/.htpasswd
# Doit afficher : -rw-r--r-- (644)
# Si 600, corriger avec :
sudo chmod 644 /opt/observations_nids/docker/nginx/auth/.htpasswd
```

---

## 5. Démarrage du stack

> **Important** : toujours utiliser `--env-file .env.prod` avec toutes les commandes
> `docker compose`. Sans ce flag, les variables `${DB_ROOT_PASSWORD}` etc. ne sont
> pas résolues et les conteneurs échouent au démarrage.

### Construction des images

```bash
cd /opt/observations_nids
docker compose -f docker/docker-compose.prod.yml --env-file .env.prod build
```

### Premier démarrage

```bash
docker compose -f docker/docker-compose.prod.yml --env-file .env.prod up -d
```

Le `docker-entrypoint.sh` exécute automatiquement au premier démarrage :
- `python manage.py migrate`
- `python manage.py collectstatic`
- Création du superuser Django (si `DJANGO_SUPERUSER_*` défini dans `.env.prod`)

### Après le premier démarrage — compléter la correction réseau

Une fois le stack démarré, identifier le bridge Docker et appliquer la correction Problème 2 :

```bash
# Identifier le bridge (ex: br-85826af17032)
ip link show | grep br-

# Appliquer les règles FORWARD pour ce bridge (remplacer br-XXXXXXXX)
sudo iptables -I FORWARD 1 -i br-XXXXXXXX -o ens3 -j ACCEPT
sudo iptables -I FORWARD 2 -i ens3 -o br-XXXXXXXX -m conntrack --ctstate RELATED,ESTABLISHED -j ACCEPT
sudo iptables -t nat -A POSTROUTING -s 172.18.0.0/16 -o ens3 -j MASQUERADE
sudo ip route add default via 135.125.72.1 dev ens3 table 201
sudo ip rule add from 172.18.0.0/16 table 201 pref 101

# Sauvegarder les règles iptables
sudo netfilter-persistent save
# Puis ajouter les règles ip route/ip rule dans /etc/rc.local (voir section 1)
```

### Vérification

```bash
# État des conteneurs (tous doivent être "healthy" ou "Up")
docker compose -f docker/docker-compose.prod.yml --env-file .env.prod ps

# Logs Django
docker compose -f docker/docker-compose.prod.yml --env-file .env.prod logs -f web

# Test depuis le serveur
curl -I https://observation-nids.meteo-poelley50.fr
```

L'application est accessible sur : **https://observation-nids.meteo-poelley50.fr**

---

## 6. Accès à phpMyAdmin (ponctuel)

phpMyAdmin est désactivé par défaut. Pour y accéder :

```bash
bash /opt/observations_nids/docker/scripts/enable-phpmyadmin.sh
```

Accès : **https://observation-nids.meteo-poelley50.fr/phpmyadmin/**

**Étape 1 — Basic Auth Nginx** (fenêtre navigateur) :
- Login/mot de passe définis lors de `setup-phpmyadmin-auth.sh`

**Étape 2 — Interface phpMyAdmin** :
- Utilisateur : `root`
- Mot de passe : `DB_ROOT_PASSWORD` du `.env.prod`

```bash
# Désactiver après utilisation (toujours faire !)
bash /opt/observations_nids/docker/scripts/disable-phpmyadmin.sh
```

---

## 7. Import des données depuis le pilote

Pour migrer la base de données depuis l'environnement pilote :

**Export depuis le pilote** (sur la machine pilote) :
```bash
docker compose exec db mysqldump -u root -p<DB_ROOT_PASSWORD_PILOTE> <DB_NAME_PILOTE> > dump_pilote.sql
```

**Import via phpMyAdmin** (le plus simple) :
1. Activer phpMyAdmin (`enable-phpmyadmin.sh`)
2. Se connecter à phpMyAdmin
3. Sélectionner la base `observations_nids` dans la colonne de gauche
4. Onglet **Importer** → choisir le fichier `.sql` → Go

**Import en ligne de commande** (pour les gros fichiers) :
```bash
docker compose -f docker/docker-compose.prod.yml --env-file .env.prod exec -T db \
  mysql -u root -p${DB_ROOT_PASSWORD} observations_nids \
  < dump_pilote.sql
```

Vérifier après import :
```bash
docker compose -f docker/docker-compose.prod.yml --env-file .env.prod exec web \
  python manage.py migrate --check
```

---

## 8. Accès à Flower (monitoring Celery)

Flower n'est pas exposé publiquement. Accès via tunnel SSH depuis le poste admin :

```bash
# Sur le poste local (Windows PowerShell ou Git Bash)
ssh -L 5555:localhost:5555 ubuntu@[IP-OVH]

# Puis ouvrir dans le navigateur : http://localhost:5555/flower
```

---

## 9. Renouvellement automatique SSL

```bash
sudo crontab -e
```

Ajouter (renouvellement chaque lundi à 3h du matin) :

```cron
0 3 * * 1 certbot renew --quiet && docker compose -f /opt/observations_nids/docker/docker-compose.prod.yml --env-file /opt/observations_nids/.env.prod exec nginx nginx -s reload >> /var/log/certbot-renew.log 2>&1
```

---

## 10. Mises à jour de l'application

```bash
cd /opt/observations_nids
sudo git pull
docker compose -f docker/docker-compose.prod.yml --env-file .env.prod build web celery_worker celery_beat
docker compose -f docker/docker-compose.prod.yml --env-file .env.prod up -d
docker compose -f docker/docker-compose.prod.yml --env-file .env.prod logs -f web
```

> **Important** : un simple `git pull` ne suffit pas. Les conteneurs contiennent une copie
> du code faite lors du build — un rebuild est nécessaire après chaque mise à jour.

---

## 11. Sauvegarde de la base de données

```bash
# Créer un dump SQL
docker compose -f docker/docker-compose.prod.yml --env-file .env.prod exec db \
  mysqldump -u root -p${DB_ROOT_PASSWORD} observations_nids \
  > /opt/observations_nids/backup_$(date +%Y%m%d_%H%M%S).sql

# Restaurer
docker compose -f docker/docker-compose.prod.yml --env-file .env.prod exec -T db \
  mysql -u root -p${DB_ROOT_PASSWORD} observations_nids \
  < /opt/observations_nids/backup_20260101_120000.sql
```

---

## 12. Snapshot OVH (sauvegarde serveur)

1. Manager OVH → Public Cloud → Instances → menu `...` (trois points) à côté de l'instance → **Créer un snapshot** (ou "Créer un instantané")
2. Le snapshot conserve le système complet (Docker, données, config, règles iptables)
3. Pour restaurer : créer une nouvelle instance depuis le snapshot

> Facturé ~0.04€/Go/mois. Supprimer les anciens snapshots après validation.

---

## 13. Commandes utiles

Alias pratique à ajouter dans `~/.bashrc` :

```bash
echo "alias dcp='docker compose -f /opt/observations_nids/docker/docker-compose.prod.yml --env-file /opt/observations_nids/.env.prod'" >> ~/.bashrc
source ~/.bashrc
```

Ensuite :
```bash
dcp ps                                    # État des conteneurs
dcp logs -f web                           # Logs Django
dcp logs -f nginx                         # Logs Nginx
dcp exec web python manage.py shell       # Shell Django
dcp restart nginx                         # Recharger Nginx
dcp down && dcp up -d                     # Redémarrage complet
```

---

## Checklist de déploiement initial

- [ ] Instance OVH créée (Ubuntu 22.04, B3-8)
- [ ] DNS mis à jour (enregistrement A → IP OVH, propagation vérifiée avec `nslookup`)
- [ ] Docker installé (`docker --version` et `docker compose version`)
- [ ] Daemon Docker configuré (`/etc/docker/daemon.json` avec DNS et ipv6 désactivé)
- [ ] Correction réseau Docker — Problème 1 (172.17.0.0/16 via ens3, test `alpine wget`)
- [ ] Répertoires `/opt/observations_nids/media` et `/opt/observations_nids/logs` créés
- [ ] Dépôt cloné dans `/opt/observations_nids/`
- [ ] Fichier `.env.prod` complété (`ALLOWED_HOSTS` inclut `localhost`)
- [ ] Certificat SSL obtenu (`sudo certbot certonly --standalone ...`)
- [ ] Credentials phpMyAdmin créés (`setup-phpmyadmin-auth.sh`)
- [ ] Permissions `.htpasswd` vérifiées (644)
- [ ] Stack construit (`docker compose ... --env-file .env.prod build`)
- [ ] Stack démarré (`docker compose ... --env-file .env.prod up -d`)
- [ ] Correction réseau Docker — Problème 2 (bridge `br-*`, FORWARD iptables)
- [ ] Règles iptables sauvegardées (`netfilter-persistent save`)
- [ ] Routage persisté dans `/etc/rc.local` (testé avec `sudo /etc/rc.local && echo OK`)
- [ ] Alias `dcp` configuré dans `~/.bashrc`
- [ ] Application accessible en HTTPS (cadenas dans le navigateur)
- [ ] Données importées depuis le pilote
- [ ] Cron renouvellement SSL configuré (`sudo crontab -e`)
- [ ] phpMyAdmin testé et désactivé après usage (`disable-phpmyadmin.sh`)
- [ ] Snapshot OVH de l'état initial créé

---

## Dépannage

### Build Docker échoue : "No route to host" ou "Unable to locate package"

Les conteneurs n'accèdent pas à Internet pendant le build (Problème 1).

```bash
# Vérifier les interfaces
ip route | grep default

# Appliquer la correction
sudo iptables -t nat -A POSTROUTING -s 172.17.0.0/16 ! -o docker0 -j MASQUERADE
sudo ip route add default via [GW-ENS3] dev ens3 table 200
sudo ip rule add from 172.17.0.0/16 table 200 pref 100

# Tester
docker run --rm alpine wget -qO- http://example.com 2>&1 | head -3
```

### Site inaccessible depuis l'extérieur (TCP timeout) malgré Nginx opérationnel

Nginx répond en local (`curl http://localhost` retourne 301) mais le navigateur externe
obtient un timeout. C'est le Problème 2 : les réponses des conteneurs sont bloquées
par la chaîne FORWARD (politique DROP) car le bridge `br-*` n'est pas autorisé.

```bash
# Identifier le bridge Docker Compose
ip link show | grep br-

# Appliquer les règles (remplacer br-XXXXXXXX et [GW-ENS3])
sudo iptables -I FORWARD 1 -i br-XXXXXXXX -o ens3 -j ACCEPT
sudo iptables -I FORWARD 2 -i ens3 -o br-XXXXXXXX -m conntrack --ctstate RELATED,ESTABLISHED -j ACCEPT
sudo iptables -t nat -A POSTROUTING -s 172.18.0.0/16 -o ens3 -j MASQUERADE
sudo ip route add default via [GW-ENS3] dev ens3 table 201
sudo ip rule add from 172.18.0.0/16 table 201 pref 101

# Sauvegarder
sudo netfilter-persistent save
```

### Container "web" unhealthy : "DisallowedHost: localhost:8000"

Le healthcheck Docker envoie `Host: localhost:8000` à Django. `ALLOWED_HOSTS` doit
inclure `localhost` :

```env
ALLOWED_HOSTS='["observation-nids.meteo-poelley50.fr","localhost"]'
```

Puis redémarrer le service web :
```bash
docker compose -f docker/docker-compose.prod.yml --env-file .env.prod up -d web
```

### Variables DB non résolues (WARN "variable is not set")

Toujours passer `--env-file .env.prod` aux commandes `docker compose` :
```bash
docker compose -f docker/docker-compose.prod.yml --env-file .env.prod [commande]
```
Ou utiliser l'alias `dcp` qui l'inclut automatiquement.

### Nginx ne démarre pas : certificat introuvable

```bash
ls /etc/letsencrypt/live/observation-nids.meteo-poelley50.fr/
# Si absent, arrêter Nginx puis obtenir le certificat
docker compose -f docker/docker-compose.prod.yml --env-file .env.prod stop nginx
sudo certbot certonly --standalone \
  -d observation-nids.meteo-poelley50.fr \
  --email admin@meteo-poelley50.fr --agree-tos --no-eff-email
docker compose -f docker/docker-compose.prod.yml --env-file .env.prod start nginx
```

### Erreur 500 sur /phpmyadmin/ au chargement

Deux causes possibles :

**Cause 1 — Permissions `.htpasswd`** : le fichier doit être lisible par nginx (644, pas 600).
```bash
ls -la /opt/observations_nids/docker/nginx/auth/.htpasswd
sudo chmod 644 /opt/observations_nids/docker/nginx/auth/.htpasswd
dcp exec nginx nginx -s reload
```

**Cause 2 — phpMyAdmin non démarré** : comportement normal quand désactivé (retourne 502).
```bash
bash /opt/observations_nids/docker/scripts/enable-phpmyadmin.sh
```

### phpMyAdmin : "Access denied" après le login MariaDB

`PMA_PASSWORD` est vide — le container a été démarré sans `--env-file .env.prod`.
Recréer le container :
```bash
docker stop observations_phpmyadmin && docker rm observations_phpmyadmin
docker compose -f /opt/observations_nids/docker/docker-compose.prod.yml \
  --env-file /opt/observations_nids/.env.prod --profile admin up -d phpmyadmin
```

Ou simplement relancer le script (qui inclut maintenant `--env-file`) :
```bash
bash /opt/observations_nids/docker/scripts/enable-phpmyadmin.sh
```

### Erreur CSRF 403

Vérifier dans `.env.prod` :
```env
CSRF_TRUSTED_ORIGINS='["https://observation-nids.meteo-poelley50.fr"]'
```
Puis redémarrer le stack.

### Clonage Git : "not an empty directory"

Toujours cloner depuis le répertoire parent :
```bash
cd /opt
sudo git clone https://github.com/jmFschneider/Observations_Nids.git observations_nids
```

---

*Dernière mise à jour : Mars 2026*
