# Déploiement Production — OVH Public Cloud

Guide complet pour déployer Observations Nids en production sur un VPS ou une instance OVH Public Cloud.

## Architecture

```
Internet (HTTPS :443)
    ↓
Nginx Docker  ← gère SSL directement (Let's Encrypt)
    ↓
Gunicorn (Django) :8000
    ↓
MariaDB / Redis / Celery  (réseau Docker interne)
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

- Instance OVH Ubuntu 22.04 LTS (B3-8 ou équivalent : 2 vCores, 8 Go RAM recommandés)
- Ports 22, 80, 443 ouverts dans le groupe de sécurité OVH
- Domaine pointant vers l'IP publique de l'instance (enregistrement A dans Hostinger)
- Docker installé sur l'instance (voir section ci-dessous)
- Clé SSH configurée sur le poste de développement

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
- `ens3` → IP publique (ex: 135.125.72.x) — celle qui donne accès à Internet
- `ens4` → IP privée OVH (ex: 10.1.0.x) — réseau interne OVH

Par défaut, Docker route ses paquets de façon aléatoire entre les deux interfaces.
Quand les paquets passent par `ens4`, ils n'atteignent pas Internet et le build échoue
(`apt-get update` : "No route to host").

**Vérifier les interfaces :**
```bash
ip route | grep default
# Doit afficher deux routes : une via ens3 (IP publique) et une via ens4 (IP privée)
```

**Correction : forcer le trafic Docker via `ens3` (interface publique) :**

Remplacer `135.125.72.1` par le gateway affiché pour `ens3` dans `ip route` :

```bash
# Configurer le DNS dans Docker daemon
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

# Forcer le routage Docker via l'interface publique
sudo iptables -t nat -A POSTROUTING -s 172.17.0.0/16 ! -o docker0 -j MASQUERADE
sudo ip route add default via 135.125.72.1 dev ens3 table 200
sudo ip rule add from 172.17.0.0/16 table 200 pref 100

# Rendre la configuration persistante au redémarrage
sudo apt install iptables-persistent -y
sudo netfilter-persistent save
echo "ip route add default via 135.125.72.1 dev ens3 table 200" | sudo tee -a /etc/rc.local
echo "ip rule add from 172.17.0.0/16 table 200 pref 100" | sudo tee -a /etc/rc.local
sudo chmod +x /etc/rc.local
```

**Vérifier que ça fonctionne :**
```bash
docker run --rm alpine wget -qO- http://example.com 2>&1 | head -3
# Doit afficher le HTML d'example.com
```

> **Note** : Cette correction est nécessaire avant tout `docker compose build`.
> Sans elle, `apt-get update` échoue dans les conteneurs pendant le build.

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

> **Attention** : cloner depuis `/opt` avec le nom de destination explicite `observations_nids`.
> Ne pas cloner depuis l'intérieur du répertoire `/opt/observations_nids/` (erreur "not an empty directory").

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
SECRET_KEY=           # Clé secrète Django (générée ci-dessus)
DB_PASSWORD=          # Mot de passe fort pour l'utilisateur BDD
DB_ROOT_PASSWORD=     # Mot de passe root MariaDB (très fort)
DJANGO_SUPERUSER_PASSWORD=   # Mot de passe admin Django
GEMINI_API_KEY=       # Clé API Google Gemini
EMAIL_HOST_USER=      # Compte SMTP Brevo
EMAIL_HOST_PASSWORD=  # Mot de passe SMTP Brevo
```

**Variables pré-remplies dans le template :**
- `DEBUG=False`
- `SESSION_COOKIE_SECURE=True`
- `CSRF_COOKIE_SECURE=True`
- `ALLOWED_HOSTS` et `CSRF_TRUSTED_ORIGINS` avec le domaine production

> Toutes les variables `DB_*`, `DJANGO_*`, etc. du `.env.prod` sont lues directement
> par `docker-compose.prod.yml` — pas besoin de modifier le `.yml`.

---

## 3. Certificat SSL (Let's Encrypt)

> **Important** : utiliser `certbot` installé directement sur le serveur (pas via Docker).
> Les conteneurs Docker ont un problème de connectivité IPv6 sortante qui empêche
> d'atteindre les serveurs Let's Encrypt depuis un conteneur.

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

Ces fichiers appartiennent à `root` — c'est normal. Le conteneur Nginx tourne en `root`
en interne et peut les lire via le volume mount `/etc/letsencrypt`.

---

## 4. Configuration des credentials phpMyAdmin

À effectuer une seule fois avant le premier démarrage :

```bash
cd /opt/observations_nids
bash docker/scripts/setup-phpmyadmin-auth.sh
```

Le script demande un **nom d'utilisateur** et un **mot de passe** — ce sont des credentials
propres à la Basic Auth Nginx, indépendants de tout autre compte (Linux, Django, MariaDB).

Le fichier `docker/nginx/auth/.htpasswd` est créé localement (non commité sur GitHub).

---

## 5. Démarrage du stack

### Construction des images

```bash
cd /opt/observations_nids
docker compose -f docker/docker-compose.prod.yml build
```

### Premier démarrage

```bash
docker compose -f docker/docker-compose.prod.yml up -d
```

Le `docker-entrypoint.sh` exécute automatiquement au premier démarrage :
- `python manage.py migrate`
- `python manage.py collectstatic`
- Création du superuser Django (si `DJANGO_SUPERUSER_*` défini dans `.env.prod`)

### Vérification

```bash
# État des conteneurs
docker compose -f docker/docker-compose.prod.yml ps

# Logs en temps réel
docker compose -f docker/docker-compose.prod.yml logs -f web

# Test HTTPS
curl -I https://observation-nids.meteo-poelley50.fr
```

L'application est accessible sur : **https://observation-nids.meteo-poelley50.fr**

---

## 6. Accès à phpMyAdmin (ponctuel)

phpMyAdmin est désactivé par défaut. Pour y accéder :

```bash
# Activer
bash docker/scripts/enable-phpmyadmin.sh
```

Accès : **https://observation-nids.meteo-poelley50.fr/phpmyadmin/**

**Étape 1 — Basic Auth Nginx** (fenêtre navigateur) :
- Login : défini lors de `setup-phpmyadmin-auth.sh`
- Mot de passe : défini lors de `setup-phpmyadmin-auth.sh`

**Étape 2 — Interface phpMyAdmin** :
- Utilisateur : `root`
- Mot de passe : `DB_ROOT_PASSWORD` du `.env.prod`

```bash
# Désactiver après utilisation (toujours faire !)
bash docker/scripts/disable-phpmyadmin.sh
```

---

## 7. Accès à Flower (monitoring Celery)

Flower n'est pas exposé publiquement. Accès via tunnel SSH depuis le poste admin :

```bash
# Sur le poste local (Windows PowerShell ou Git Bash)
ssh -L 5555:localhost:5555 ubuntu@[IP-OVH]

# Puis ouvrir dans le navigateur
# http://localhost:5555/flower
```

---

## 8. Renouvellement automatique SSL

Configurer un cron job pour renouveler le certificat automatiquement :

```bash
crontab -e
```

Ajouter (renouvellement chaque lundi à 3h du matin) :

```cron
0 3 * * 1 certbot renew --quiet && docker compose -f /opt/observations_nids/docker/docker-compose.prod.yml exec nginx nginx -s reload >> /var/log/certbot-renew.log 2>&1
```

---

## 9. Mises à jour de l'application

```bash
cd /opt/observations_nids
git pull
docker compose -f docker/docker-compose.prod.yml build web celery_worker celery_beat
docker compose -f docker/docker-compose.prod.yml up -d
docker compose -f docker/docker-compose.prod.yml logs -f web
```

> **Important** : Un simple `git pull` ne suffit pas. Les conteneurs contiennent une copie
> du code faite lors du build — un rebuild est nécessaire après chaque mise à jour.

---

## 10. Sauvegarde de la base de données

```bash
# Créer un dump SQL
docker compose -f docker/docker-compose.prod.yml exec db \
  mysqldump -u root -p${DB_ROOT_PASSWORD} observations_nids \
  > /opt/observations_nids/backup_$(date +%Y%m%d_%H%M%S).sql

# Restaurer
docker compose -f docker/docker-compose.prod.yml exec -T db \
  mysql -u root -p${DB_ROOT_PASSWORD} observations_nids \
  < /opt/observations_nids/backup_20260101_120000.sql
```

---

## 11. Snapshot OVH (sauvegarde serveur)

Pour sauvegarder l'état complet du serveur avant/après une opération importante :

1. Manager OVH → Instance → **Créer un snapshot**
2. Le snapshot conserve le système complet (Docker, données, config)
3. Pour restaurer : créer une nouvelle instance depuis le snapshot

> Le snapshot est facturé environ 0.04€/Go/mois. Supprimer les anciens snapshots après validation.

---

## 12. Commandes utiles

Alias pratique à ajouter dans `~/.bashrc` :

```bash
echo "alias dcp='docker compose -f /opt/observations_nids/docker/docker-compose.prod.yml'" >> ~/.bashrc
source ~/.bashrc
```

Ensuite :
```bash
dcp ps                          # État des conteneurs
dcp logs -f web                 # Logs Django
dcp logs -f nginx               # Logs Nginx
dcp exec web python manage.py shell   # Shell Django
dcp restart nginx               # Recharger Nginx
dcp down && dcp up -d           # Redémarrage complet
```

---

## Checklist de déploiement initial

- [ ] Instance OVH créée (Ubuntu 22.04, B3-8)
- [ ] Ports 22, 80, 443 ouverts dans le groupe de sécurité OVH
- [ ] DNS mis à jour (enregistrement A → IP OVH, propagation vérifiée)
- [ ] Docker installé (`docker --version`)
- [ ] Réseau Docker corrigé pour OVH (routage via ens3, persistance iptables)
- [ ] Répertoires `/opt/observations_nids/media` et `/opt/observations_nids/logs` créés
- [ ] Dépôt cloné dans `/opt/observations_nids/`
- [ ] Fichier `.env.prod` complété
- [ ] Certificat SSL obtenu (`sudo certbot certonly --standalone ...`)
- [ ] Credentials phpMyAdmin créés (`setup-phpmyadmin-auth.sh`)
- [ ] Stack démarré (`docker compose -f docker/docker-compose.prod.yml up -d`)
- [ ] Application accessible en HTTPS
- [ ] Cron renouvellement SSL configuré
- [ ] Snapshot OVH de l'état initial créé

---

## Dépannage

### Nginx ne démarre pas : certificat introuvable

```bash
ls /etc/letsencrypt/live/observation-nids.meteo-poelley50.fr/
# Si absent, obtenir le certificat (Nginx doit être arrêté)
docker compose -f docker/docker-compose.prod.yml stop nginx
sudo certbot certonly --standalone -d observation-nids.meteo-poelley50.fr --email admin@meteo-poelley50.fr --agree-tos --no-eff-email
docker compose -f docker/docker-compose.prod.yml start nginx
```

### Erreur 502 sur /phpmyadmin/

phpMyAdmin n'est pas démarré — comportement normal quand désactivé.
```bash
bash docker/scripts/enable-phpmyadmin.sh
```

### Erreur CSRF 403

Vérifier dans `.env.prod` :
```env
CSRF_TRUSTED_ORIGINS='["https://observation-nids.meteo-poelley50.fr"]'
```
Puis redémarrer le stack.

### Consulter les logs Nginx

```bash
docker compose -f docker/docker-compose.prod.yml exec nginx cat /var/log/nginx/observations_error.log
```

### Build Docker échoue : "No route to host" ou "Unable to locate package"

Les conteneurs Docker n'arrivent pas à accéder à Internet pendant le build.
Cause : OVH Public Cloud a deux interfaces réseau (`ens3` publique, `ens4` privée) et
Docker route parfois les paquets par `ens4` qui n'a pas accès à Internet.

```bash
# Vérifier les interfaces
ip route | grep default

# Appliquer la correction (voir section "Correction du réseau Docker")
sudo iptables -t nat -A POSTROUTING -s 172.17.0.0/16 ! -o docker0 -j MASQUERADE
sudo ip route add default via 135.125.72.1 dev ens3 table 200
sudo ip rule add from 172.17.0.0/16 table 200 pref 100

# Tester
docker run --rm alpine wget -qO- http://example.com 2>&1 | head -3
```

### Clonage Git : "not an empty directory"

Ne pas cloner depuis l'intérieur du répertoire cible. Toujours cloner depuis le parent :
```bash
cd /opt
sudo git clone https://github.com/jmFschneider/Observations_Nids.git observations_nids
```

---

*Dernière mise à jour : Mars 2026*
