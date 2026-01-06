# Configuration du serveur distant
$REMOTE_USER = "utilisateur"       # Votre user SSH sur Ubuntu (ex: ubuntu, root...)
$REMOTE_HOST = "192.168.1.X"       # L'IP de votre serveur Ubuntu
$REMOTE_PATH = "/chemin/vers/observations_nids" # Dossier où se trouve le docker-compose.yml sur le serveur
$CONTAINER_NAME = "observations_nids-web-1"     # Nom du conteneur Django (vérifiez avec 'docker ps')

# Configuration locale
$LOCAL_DUMP_FILE = "prod_dump.json"

Write-Host "--- Etape 1 : Generation du dump sur le serveur distant (Docker) ---" -ForegroundColor Cyan
# On execute la commande via SSH.
# Note : docker compose exec -T (sans tty) est important pour les redirections
$cmd_dump = "cd $REMOTE_PATH && docker compose exec -T web python manage.py dumpdata --exclude auth.permission --exclude contenttypes --exclude admin.logentry --exclude sessions --indent 2 > dump_temp.json"
ssh $REMOTE_USER@$REMOTE_HOST $cmd_dump

if ($LASTEXITCODE -ne 0) {
    Write-Host "Erreur lors de la generation du dump sur le serveur." -ForegroundColor Red
    exit
}

Write-Host "--- Etape 2 : Telechargement du fichier JSON ---" -ForegroundColor Cyan
scp "$($REMOTE_USER)@$($REMOTE_HOST):$($REMOTE_PATH)/dump_temp.json" ./$LOCAL_DUMP_FILE

Write-Host "--- Etape 3 : (Optionnel) Voulez-vous telecharger les medias ? (o/n) ---" -ForegroundColor Yellow
$response = Read-Host
if ($response -eq 'o') {
    Write-Host "Telechargement des images (cela peut etre long)..." -ForegroundColor Cyan
    # Crée le dossier media s'il n'existe pas
    New-Item -ItemType Directory -Force -Path ".\media" | Out-Null
    # Copie récursive
    scp -r "$($REMOTE_USER)@$($REMOTE_HOST):$($REMOTE_PATH)/media/*" .\media\
}

Write-Host "--- Etape 4 : Nettoyage local et Importation ---" -ForegroundColor Cyan

# Attention : On vide la base locale pour éviter les conflits d'ID
Write-Host "ATTENTION : Cela va supprimer les données de votre base de développement locale actuelle." -ForegroundColor Red
Write-Host "Voulez-vous continuer ? (o/n)" -ForegroundColor Yellow
$confirm = Read-Host
if ($confirm -eq 'o') {
    # 1. On vide la base (flush)
    python manage.py flush --no-input

    # 2. On importe les données
    # On ignore contenttypes lors du load pour éviter les erreurs d'intégrité car flush les recrée parfois
    python manage.py loaddata $LOCAL_DUMP_FILE
    
    if ($?) {
        Write-Host "Succès ! Les données de production sont maintenant en local." -ForegroundColor Green
    } else {
        Write-Host "Erreur lors de l'importation." -ForegroundColor Red
    }
} else {
    Write-Host "Importation annulée." -ForegroundColor Yellow
}

# Nettoyage du fichier temporaire sur le serveur (optionnel, via une autre commande ssh)
# ssh $REMOTE_USER@$REMOTE_HOST "rm $REMOTE_PATH/dump_temp.json"
