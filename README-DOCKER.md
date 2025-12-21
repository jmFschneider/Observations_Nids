# Déploiement Docker - Observations Nids

## 📦 Configuration Docker

Tous les fichiers de configuration Docker ont été organisés dans le répertoire `docker/` pour garder la racine du projet propre.

## 🚀 Démarrage rapide

### Sur Ubuntu (version pilote)

```bash
# 1. Créer un utilisateur dédié
sudo useradd -m -s /bin/bash observations
sudo usermod -aG docker observations
sudo su - observations

# 2. Cloner le dépôt (version pilote)
git clone https://github.com/jmFschneider/Observations_Nids.git observations_nids_pilote
cd observations_nids_pilote/docker

# 3. Copier et configurer les variables d'environnement
cp .env.example .env
nano .env

# 4. Démarrer avec le Makefile (recommandé)
make build
make up

# OU avec docker compose directement
docker compose up -d --build
```

## 📚 Documentation complète

➡️ **Consultez la documentation complète dans [`docker/README.md`](docker/README.md)**

Ce guide contient :
- Installation détaillée de Docker
- Configuration complète
- Commandes de gestion
- Dépannage
- Guide de production
- Architecture complète

## 🛠️ Commandes utiles (depuis le répertoire docker/)

```bash
# Avec le Makefile (plus simple)
make up          # Démarrer tous les services
make down        # Arrêter tous les services
make logs        # Voir les logs
make shell       # Shell Django
make migrate     # Appliquer les migrations
make ps          # Voir l'état des conteneurs

# Avec docker compose directement
docker compose up -d
docker compose down
docker compose logs -f
docker compose exec web python manage.py shell
```

## 📁 Structure Docker

```
docker/
├── docker-compose.yml          # Configuration production
├── docker-compose.dev.yml      # Configuration développement
├── Dockerfile                  # Image Django
├── docker-entrypoint.sh        # Script de démarrage
├── .dockerignore              # Exclusions build
├── Makefile                   # Commandes simplifiées
├── .env.example               # Template variables d'environnement
├── README.md                  # Documentation complète
├── nginx/                     # Configuration Nginx
│   ├── nginx.conf
│   └── conf.d/
├── mariadb/                   # Configuration MariaDB
│   └── conf.d/
└── radicale/                  # Configuration Radicale
    └── config/
```

## ⚙️ Services inclus

- **Django + Gunicorn** - Application web (port 8000)
- **MariaDB 10.11** - Base de données
- **Redis** - Cache et broker Celery
- **Celery Worker + Beat** - Tâches asynchrones
- **Flower** - Monitoring Celery (port 5555)
- **Nginx** - Reverse proxy (ports 80/443)
- **Radicale** - Serveur CalDAV

## 🎯 Avantages

✅ **Python 3.12** garanti (Django 6.0 fonctionne)
✅ **Isolation complète** (pas de conflit système)
✅ **Portabilité** (même environnement partout)
✅ **Déploiement simple** (`make up`)
✅ **Scalabilité** facile
✅ **Backup/Restore** intégrés

---

**Pour toute question**, consultez la [documentation complète](docker/README.md) ou créez une issue.
