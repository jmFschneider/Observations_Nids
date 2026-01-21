# Script PowerShell pour gérer l'environnement Docker de développement
# Usage: .\docker-dev.ps1 [commande]
#
# Commandes disponibles:
#   up        - Démarrer les services
#   down      - Arrêter les services
#   restart   - Redémarrer les services
#   logs      - Afficher les logs (Ctrl+C pour quitter)
#   build     - Reconstruire les images
#   shell     - Ouvrir un shell Django
#   bash      - Ouvrir un shell Bash dans le container web
#   migrate   - Appliquer les migrations
#   test      - Exécuter les tests
#   collectstatic - Collecter les fichiers statiques

param(
    [Parameter(Position=0)]
    [string]$Command = "up"
)

$ComposeFiles = "-f docker-compose.yml -f docker-compose.dev.yml -f docker-compose.windows.yml"

switch ($Command) {
    "up" {
        Write-Host "🚀 Démarrage des services..." -ForegroundColor Green
        docker compose $ComposeFiles.Split() up -d
        Write-Host ""
        Write-Host "✅ Services démarrés!" -ForegroundColor Green
        Write-Host "   Application: http://localhost:8010" -ForegroundColor Cyan
        Write-Host "   Django direct: http://localhost:8000" -ForegroundColor Cyan
        Write-Host "   phpMyAdmin: http://localhost:8081" -ForegroundColor Cyan
        Write-Host "   Flower: http://localhost:5555" -ForegroundColor Cyan
    }
    "down" {
        Write-Host "🛑 Arrêt des services..." -ForegroundColor Yellow
        docker compose $ComposeFiles.Split() down
        Write-Host "✅ Services arrêtés!" -ForegroundColor Green
    }
    "restart" {
        Write-Host "🔄 Redémarrage des services..." -ForegroundColor Yellow
        docker compose $ComposeFiles.Split() restart
        Write-Host "✅ Services redémarrés!" -ForegroundColor Green
    }
    "logs" {
        Write-Host "📋 Affichage des logs (Ctrl+C pour quitter)..." -ForegroundColor Cyan
        docker compose $ComposeFiles.Split() logs -f
    }
    "build" {
        Write-Host "🔨 Reconstruction des images..." -ForegroundColor Yellow
        docker compose $ComposeFiles.Split() build
        Write-Host "✅ Images reconstruites!" -ForegroundColor Green
    }
    "shell" {
        Write-Host "🐍 Ouverture du shell Django..." -ForegroundColor Cyan
        docker compose exec web python manage.py shell
    }
    "bash" {
        Write-Host "💻 Ouverture du shell Bash..." -ForegroundColor Cyan
        docker compose exec web bash
    }
    "migrate" {
        Write-Host "🗄️  Application des migrations..." -ForegroundColor Cyan
        docker compose exec web python manage.py migrate
        Write-Host "✅ Migrations appliquées!" -ForegroundColor Green
    }
    "test" {
        Write-Host "🧪 Exécution des tests..." -ForegroundColor Cyan
        docker compose exec web python manage.py test
    }
    "collectstatic" {
        Write-Host "📁 Collecte des fichiers statiques..." -ForegroundColor Cyan
        docker compose exec web python manage.py collectstatic --noinput
        Write-Host "✅ Fichiers statiques collectés!" -ForegroundColor Green
    }
    default {
        Write-Host "❌ Commande inconnue: $Command" -ForegroundColor Red
        Write-Host ""
        Write-Host "Commandes disponibles:" -ForegroundColor Yellow
        Write-Host "  up           - Démarrer les services"
        Write-Host "  down         - Arrêter les services"
        Write-Host "  restart      - Redémarrer les services"
        Write-Host "  logs         - Afficher les logs"
        Write-Host "  build        - Reconstruire les images"
        Write-Host "  shell        - Ouvrir un shell Django"
        Write-Host "  bash         - Ouvrir un shell Bash"
        Write-Host "  migrate      - Appliquer les migrations"
        Write-Host "  test         - Exécuter les tests"
        Write-Host "  collectstatic- Collecter les fichiers statiques"
    }
}
