#!/bin/bash

# Ce script synchronise la base de données OCR (ex-Pilote) vers la base de données Dev (Docker).
#
# PRÉREQUIS :
# 1. Accès à la base OCR (via MySQL local ou SSH)
# 2. Docker compose lancé sur l'environnement de développement
# 3. Avoir la même version de code (branche git) déployée sur les deux environnements
# 4. Variables d'environnement Docker configurées (.env)
#

# Arrête le script si une commande échoue
set -e

# --- CONFIGURATION ---
# Base source (OCR - anciennement Pilote)
# Note: Les répertoires et noms de bases peuvent encore contenir "pilote" dans leur nom
OCR_DB_NAME="pilote_observations_nids"
OCR_PROJECT_DIR="/opt/observations_nids_pilote"

# Base destination (Dev Docker)
DEV_DOCKER_DIR="/opt/observations_nids_pilote/docker"
DEV_CONTAINER_DB="observations_db"
DEV_CONTAINER_WEB="observations_web"

# Charger les variables d'environnement Docker
if [ -f "$DEV_DOCKER_DIR/../.env" ]; then
    source "$DEV_DOCKER_DIR/../.env"
else
    echo "ERREUR: Fichier .env introuvable dans $DEV_DOCKER_DIR/../"
    exit 1
fi

# Fichiers temporaires
OCR_MIGRATIONS_LIST="/tmp/ocr_migrations.txt"
DEV_MIGRATIONS_LIST="/tmp/dev_migrations.txt"
DUMP_FILE="/tmp/ocr_to_dev_dump_$(date +%F-%H%M%S).sql"
BACKUP_FILE="/tmp/dev_backup_$(date +%F-%H%M%S).sql"
# ---------------------

echo "=========================================="
echo "  Synchronisation OCR → Dev (Docker)"
echo "=========================================="
echo ""

# --- 1. Vérification de la concordance des schémas ---
echo "--- 1. Vérification de la concordance des schémas via les migrations ---"

# Migrations OCR
if [ -d "$OCR_PROJECT_DIR" ]; then
    (cd "$OCR_PROJECT_DIR" && python3 manage.py showmigrations | grep '\[X\]') > "$OCR_MIGRATIONS_LIST"
else
    echo "ERREUR: Répertoire OCR introuvable: $OCR_PROJECT_DIR"
    echo "Modifiez la variable OCR_PROJECT_DIR dans le script"
    exit 1
fi

# Migrations Dev (Docker)
docker exec "$DEV_CONTAINER_WEB" python manage.py showmigrations | grep '\[X\]' > "$DEV_MIGRATIONS_LIST"

# Comparaison
if ! diff -q "$OCR_MIGRATIONS_LIST" "$DEV_MIGRATIONS_LIST" > /dev/null 2>&1; then
    echo "AVERTISSEMENT : Les schémas des bases de données ne sont pas identiques."
    echo "Les listes de migrations appliquées diffèrent entre OCR et Dev."
    echo ""
    read -p "Continuer quand même ? (o/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Oo]$ ]]; then
        rm "$OCR_MIGRATIONS_LIST" "$DEV_MIGRATIONS_LIST"
        exit 1
    fi
else
    echo "✓ OK : Les schémas sont identiques."
fi

rm "$OCR_MIGRATIONS_LIST" "$DEV_MIGRATIONS_LIST"

# --- 2. Choix du mode de synchronisation ---
echo ""
echo "--- 2. Mode de synchronisation ---"
echo "1) Migration COMPLÈTE (avec utilisateurs)"
echo "2) Migration SÉLECTIVE (sans utilisateurs) - RECOMMANDÉ pour Dev"
echo ""
read -p "Votre choix (1/2) : " -n 1 -r MODE
echo ""

case $MODE in
    1)
        echo "Mode choisi: Migration COMPLÈTE (avec utilisateurs)"
        EXCLUDE_TABLES=""
        ;;
    2)
        echo "Mode choisi: Migration SÉLECTIVE (sans utilisateurs)"
        EXCLUDE_TABLES="--ignore-table=${OCR_DB_NAME}.accounts_utilisateur \
                        --ignore-table=${OCR_DB_NAME}.accounts_utilisateur_groups \
                        --ignore-table=${OCR_DB_NAME}.accounts_utilisateur_user_permissions \
                        --ignore-table=${OCR_DB_NAME}.auth_group \
                        --ignore-table=${OCR_DB_NAME}.auth_group_permissions"
        ;;
    *)
        echo "Choix invalide. Annulation."
        exit 1
        ;;
esac

# --- 3. Confirmation ---
echo ""
echo "--- 3. Confirmation ---"
echo "Source      : Base OCR ($OCR_DB_NAME)"
echo "Destination : Base Dev Docker ($DB_NAME)"
echo "Mode        : $([ "$MODE" = "1" ] && echo "COMPLET" || echo "SÉLECTIF (sans users)")"
echo ""
read -p "ATTENTION : Les données de Dev vont être écrasées. Continuer ? (o/N) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Oo]$ ]]; then
    echo "Synchronisation annulée."
    exit 1
fi

# --- 4. Sauvegarde de sécurité de la base Dev ---
echo ""
echo "--- 4. Sauvegarde de sécurité de la base Dev... ---"
docker exec "$DEV_CONTAINER_DB" mysqldump \
    -u"$DB_USER" -p"$DB_PASSWORD" \
    --single-transaction \
    "$DB_NAME" > "$BACKUP_FILE"
echo "✓ Sauvegarde créée: $BACKUP_FILE"

# --- 5. Export de la base OCR ---
echo ""
echo "--- 5. Export de la base OCR ($OCR_DB_NAME)... ---"
mysqldump --single-transaction --routines --triggers \
    $EXCLUDE_TABLES \
    "$OCR_DB_NAME" > "$DUMP_FILE"
echo "✓ Export terminé: $DUMP_FILE"

# --- 6. Import dans la base Dev (Docker) ---
echo ""
echo "--- 6. Import dans la base Dev (Docker - $DB_NAME)... ---"
docker exec -i "$DEV_CONTAINER_DB" mysql \
    -u"$DB_USER" -p"$DB_PASSWORD" \
    "$DB_NAME" < "$DUMP_FILE"
echo "✓ Import terminé."

# --- 7. Nettoyage ---
echo ""
echo "--- 7. Nettoyage des fichiers temporaires... ---"
read -p "Supprimer le dump OCR ($DUMP_FILE) ? (o/N) " -n 1 -r
echo
if [[ $REPLY =~ ^[Oo]$ ]]; then
    rm "$DUMP_FILE"
    echo "✓ Dump supprimé"
else
    echo "ℹ Dump conservé: $DUMP_FILE"
fi

echo ""
echo "=========================================="
echo "  ✓ Synchronisation terminée avec succès !"
echo "=========================================="
echo ""
echo "📋 Résumé:"
echo "  - Source : OCR ($OCR_DB_NAME)"
echo "  - Destination : Dev Docker ($DB_NAME)"
echo "  - Mode : $([ "$MODE" = "1" ] && echo "COMPLET" || echo "SÉLECTIF (sans users)")"
echo "  - Backup Dev : $BACKUP_FILE"
echo ""
echo "⚠️  Pour restaurer en cas de problème:"
echo "  docker exec -i $DEV_CONTAINER_DB mysql -u$DB_USER -p$DB_PASSWORD $DB_NAME < $BACKUP_FILE"
echo ""
