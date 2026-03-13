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

## Prérequis

- Instance OVH Ubuntu 22.04 LTS (B3-8 ou équivalent : 2 vCores, 8 Go RAM recommandés)
- Ports 22, 80, 443 ouverts dans le groupe de sécurité OVH
- Domaine pointant vers l'IP publique de l'instance (enregistrement A dans Hostinger)
- Docker installé sur l'instance (voir section Installation)
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

### Création des répertoires

```bash
sudo mkdir -p /opt/observations_nids/media
sudo mkdir -p /opt/observations_nids/logs
sudo chown -R ubuntu:ubuntu /opt/observations_nids
```

---

## 2. Déploiement du code

### Cloner le dépôt

```bash
cd /opt/observations_nids
git clone https://github.com/jmFschneider/Observations_Nids.git .
```

### Créer le fichier de configuration

```bash
cp docker/.env.prod.example .env.prod
nano .env.prod
```

**Variables à renseigner obligatoirement :**

```env
SECRET_KEY=           # Générer : python3 -c "import secrets; print(secrets.token_urlsafe(50))"
DB_PASSWORD=          # Mot de passe fort pour l'utilisateur BDD
DB_ROOT_PASSWORD=     # Mot de passe root MariaDB (très fort)
DJANGO_SUPERUSER_PASSWORD=   # Mot de passe admin Django
GEMINI_API_KEY=       # Clé API Google Gemini
EMAIL_HOST_USER=      # Compte SMTP Brevo
EMAIL_HOST_PASSWORD=  # Mot de passe SMTP Brevo
```

**Variables déjà pré-remplies pour la production :**
- `DEBUG=False`
- `SESSION_COOKIE_SECURE=True`
- `CSRF_COOKIE_SECURE=True`
- `ALLOWED_HOSTS='["observation-nids.meteo-poelley50.fr"]'`
- `CSRF_TRUSTED_ORIGINS='["https://observation-nids.meteo-poelley50.fr"]'`

---

## 3. Certificat SSL (Let's Encrypt)

À effectuer **avant** de démarrer le stack complet.
Le port 80 doit être libre (Nginx pas encore démarré).

```bash
cd /opt/observations_nids
bash docker/scripts/init-ssl.sh
```

Le script demande confirmation, puis obtient le certificat via certbot.
Les certificats sont stockés dans `/etc/letsencrypt/`.

> **En cas d'erreur "port 80 already in use"** : vérifier qu'aucun service n'écoute sur :80 avec `sudo ss -tlnp | grep :80`.

---

## 4. Configuration des credentials phpMyAdmin

À effectuer une seule fois, avant le premier démarrage :

```bash
bash docker/scripts/setup-phpmyadmin-auth.sh
```

Le script crée le fichier `docker/nginx/auth/.htpasswd` avec le login/mot de passe choisi.

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

# Accès : https://observation-nids.meteo-poelley50.fr/phpmyadmin/
# Login : credentials définis lors du setup-phpmyadmin-auth.sh

# Désactiver après utilisation
bash docker/scripts/disable-phpmyadmin.sh
```

**Double protection :**
1. Authentification HTTP Basic Auth (login/mot de passe)
2. Le container phpMyAdmin doit être démarré (sinon 502)

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

Configurer un cron job sur le serveur pour renouveler le certificat automatiquement :

```bash
crontab -e
```

Ajouter la ligne suivante (renouvellement chaque lundi à 3h du matin) :

```cron
0 3 * * 1 /opt/observations_nids/docker/scripts/renew-ssl.sh >> /var/log/certbot-renew.log 2>&1
```

Le script `renew-ssl.sh` renouvelle le certificat via certbot webroot et recharge Nginx.

---

## 9. Mises à jour de l'application

```bash
cd /opt/observations_nids

# Récupérer les modifications
git pull

# Rebuild des images concernées
docker compose -f docker/docker-compose.prod.yml build web celery_worker celery_beat

# Redémarrer
docker compose -f docker/docker-compose.prod.yml up -d

# Vérifier les logs
docker compose -f docker/docker-compose.prod.yml logs -f web
```

> **Important** : Un simple `git pull` ne suffit pas. Les conteneurs contiennent une copie du code faite lors du build — un rebuild est nécessaire.

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

1. Dans le Manager OVH → Instance → **Créer un snapshot**
2. Le snapshot conserve le système complet (Docker, données, config)
3. Pour restaurer : créer une nouvelle instance depuis le snapshot

> Le snapshot est facturé environ 0.04€/Go/mois. Supprimer les anciens snapshots après validation.

---

## 12. Commandes utiles

```bash
# Alias pratique (à ajouter dans ~/.bashrc)
alias dcp='docker compose -f /opt/observations_nids/docker/docker-compose.prod.yml'

# Ensuite :
dcp ps
dcp logs -f web
dcp exec web python manage.py shell
dcp restart nginx
```

---

## Checklist de déploiement initial

- [ ] Instance OVH créée (Ubuntu 22.04, B3-8)
- [ ] DNS mis à jour (enregistrement A → IP OVH)
- [ ] Docker installé
- [ ] Répertoires `/opt/observations_nids/` créés
- [ ] Dépôt cloné dans `/opt/observations_nids/`
- [ ] Fichier `.env.prod` complété
- [ ] Certificat SSL obtenu (`init-ssl.sh`)
- [ ] Credentials phpMyAdmin créés (`setup-phpmyadmin-auth.sh`)
- [ ] Stack démarré (`docker compose ... up -d`)
- [ ] Application accessible en HTTPS
- [ ] Cron renouvellement SSL configuré
- [ ] Snapshot OVH de l'état initial créé

---

## Dépannage

### Nginx ne démarre pas : certificat introuvable

```bash
# Vérifier que le certificat existe
ls /etc/letsencrypt/live/observation-nids.meteo-poelley50.fr/

# Si absent, relancer init-ssl.sh (Nginx doit être arrêté)
docker compose -f docker/docker-compose.prod.yml stop nginx
bash docker/scripts/init-ssl.sh
docker compose -f docker/docker-compose.prod.yml start nginx
```

### Erreur 502 sur /phpmyadmin/

phpMyAdmin n'est pas démarré — comportement normal.
```bash
bash docker/scripts/enable-phpmyadmin.sh
```

### Erreur CSRF 403

Vérifier dans `.env.prod` :
```env
CSRF_TRUSTED_ORIGINS='["https://observation-nids.meteo-poelley50.fr"]'
```
Puis redémarrer : `docker compose -f docker/docker-compose.prod.yml down && ... up -d`

### Consulter les logs Nginx

```bash
docker compose -f docker/docker-compose.prod.yml exec nginx cat /var/log/nginx/observations_error.log
```

---

*Dernière mise à jour : Mars 2026*
