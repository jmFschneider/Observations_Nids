# Makefile pour Observations Nids Docker
# Simplifie les commandes Docker courantes

.PHONY: help build up down restart logs shell migrate makemigrations createsuperuser collectstatic test clean backup

# Commandes par défaut
DOCKER_COMPOSE = docker compose
DOCKER_COMPOSE_DEV = docker compose -f docker-compose.yml -f docker-compose.dev.yml

help: ## Afficher cette aide
	@echo "Commandes disponibles pour Observations Nids Docker:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# ============================================================================
# PRODUCTION
# ============================================================================

build: ## Construire les images Docker
	$(DOCKER_COMPOSE) build

up: ## Démarrer tous les services
	$(DOCKER_COMPOSE) up -d

down: ## Arrêter tous les services
	$(DOCKER_COMPOSE) down

restart: ## Redémarrer tous les services
	$(DOCKER_COMPOSE) restart

logs: ## Afficher les logs (CTRL+C pour quitter)
	$(DOCKER_COMPOSE) logs -f

ps: ## Voir l'état des conteneurs
	$(DOCKER_COMPOSE) ps

# ============================================================================
# DÉVELOPPEMENT
# ============================================================================

dev-build: ## Construire les images en mode dev
	$(DOCKER_COMPOSE_DEV) build

dev-up: ## Démarrer en mode développement
	$(DOCKER_COMPOSE_DEV) up

dev-down: ## Arrêter le mode développement
	$(DOCKER_COMPOSE_DEV) down

dev-logs: ## Logs en mode développement
	$(DOCKER_COMPOSE_DEV) logs -f

# ============================================================================
# DJANGO MANAGEMENT
# ============================================================================

shell: ## Ouvrir un shell Django
	$(DOCKER_COMPOSE) exec web python manage.py shell

bash: ## Ouvrir un shell bash dans le conteneur web
	$(DOCKER_COMPOSE) exec web bash

migrate: ## Appliquer les migrations
	$(DOCKER_COMPOSE) exec web python manage.py migrate

makemigrations: ## Créer de nouvelles migrations
	$(DOCKER_COMPOSE) exec web python manage.py makemigrations

createsuperuser: ## Créer un superuser
	$(DOCKER_COMPOSE) exec web python manage.py createsuperuser

collectstatic: ## Collecter les fichiers statiques
	$(DOCKER_COMPOSE) exec web python manage.py collectstatic --noinput

# ============================================================================
# TESTS & QUALITÉ
# ============================================================================

test: ## Lancer les tests
	$(DOCKER_COMPOSE) exec web pytest

test-cov: ## Tests avec couverture
	$(DOCKER_COMPOSE) exec web pytest --cov --cov-report=html

ruff: ## Vérifier le code avec ruff
	$(DOCKER_COMPOSE) exec web ruff check .

ruff-fix: ## Corriger automatiquement avec ruff
	$(DOCKER_COMPOSE) exec web ruff check . --fix

format: ## Formater le code avec ruff
	$(DOCKER_COMPOSE) exec web ruff format .

mypy: ## Vérifier les types avec mypy
	$(DOCKER_COMPOSE) exec web mypy .

# ============================================================================
# CELERY
# ============================================================================

celery-logs: ## Logs du worker Celery
	$(DOCKER_COMPOSE) logs -f celery_worker

celery-status: ## Statut des workers Celery
	$(DOCKER_COMPOSE) exec celery_worker celery -A observations_nids inspect active

celery-restart: ## Redémarrer Celery
	$(DOCKER_COMPOSE) restart celery_worker celery_beat

flower: ## Ouvrir Flower dans le navigateur
	@echo "Flower disponible sur http://localhost:5555"
	@command -v xdg-open >/dev/null 2>&1 && xdg-open http://localhost:5555 || echo "Ouvrez manuellement http://localhost:5555"

# ============================================================================
# BASE DE DONNÉES
# ============================================================================

db-shell: ## Ouvrir un shell MySQL
	$(DOCKER_COMPOSE) exec db mysql -u root -p$$DB_ROOT_PASSWORD $$DB_NAME

db-backup: ## Sauvegarder la base de données
	@echo "Création du backup..."
	$(DOCKER_COMPOSE) exec db mysqldump -u root -p$$DB_ROOT_PASSWORD $$DB_NAME > backup_$$(date +%Y%m%d_%H%M%S).sql
	@echo "Backup créé: backup_$$(date +%Y%m%d_%H%M%S).sql"

db-restore: ## Restaurer un backup (usage: make db-restore FILE=backup.sql)
	@if [ -z "$(FILE)" ]; then echo "Usage: make db-restore FILE=backup.sql"; exit 1; fi
	$(DOCKER_COMPOSE) exec -T db mysql -u root -p$$DB_ROOT_PASSWORD $$DB_NAME < $(FILE)

# ============================================================================
# MAINTENANCE
# ============================================================================

clean: ## Nettoyer les conteneurs, images et volumes inutilisés
	@echo "Attention: cela va supprimer les conteneurs arrêtés, images et volumes non utilisés"
	@read -p "Continuer? [y/N] " -n 1 -r; echo; if [[ $$REPLY =~ ^[Yy]$$ ]]; then docker system prune -a --volumes; fi

clean-volumes: ## Supprimer TOUS les volumes (ATTENTION: perte de données)
	@echo "ATTENTION: cela va supprimer TOUTES les données (DB, Redis, etc.)"
	@read -p "Êtes-vous SÛR? [y/N] " -n 1 -r; echo; if [[ $$REPLY =~ ^[Yy]$$ ]]; then $(DOCKER_COMPOSE) down -v; fi

rebuild: ## Reconstruire complètement (arrêt, nettoyage, rebuild, démarrage)
	$(DOCKER_COMPOSE) down
	$(DOCKER_COMPOSE) build --no-cache
	$(DOCKER_COMPOSE) up -d

update: ## Mettre à jour l'application (git pull + rebuild + migrate)
	git pull
	$(DOCKER_COMPOSE) build
	$(DOCKER_COMPOSE) up -d
	$(DOCKER_COMPOSE) exec web python manage.py migrate
	$(DOCKER_COMPOSE) exec web python manage.py collectstatic --noinput

# ============================================================================
# MONITORING
# ============================================================================

stats: ## Voir les statistiques des conteneurs
	docker stats

health: ## Vérifier le health check
	@curl -f http://localhost/health/ && echo "\n✓ Application en bonne santé" || echo "\n✗ Application en erreur"

# ============================================================================
# CONFIGURATION
# ============================================================================

init: ## Initialiser le projet (première installation)
	@echo "Initialisation du projet Observations Nids..."
	@if [ ! -f .env ]; then cp .env.example .env; echo "✓ Fichier .env créé"; else echo "✓ Fichier .env existe déjà"; fi
	@echo "✓ Veuillez éditer le fichier .env avec vos valeurs"
	@echo "✓ Ensuite, lancez: make build && make up"

env-check: ## Vérifier que le fichier .env existe
	@if [ ! -f .env ]; then echo "✗ Fichier .env manquant! Lancez 'make init'"; exit 1; else echo "✓ Fichier .env trouvé"; fi
