#!/bin/bash

# Ce script synchronise la base de données de production vers la base de données pilote.
#
# PRÉREQUIS :
# 1. Être exécuté sur le Raspberry Pi.
# 2. Avoir un fichier ~/.my.cnf configuré avec les identifiants de la base de données.
# 3. Avoir la même version de code (branche git) déployée sur les deux environnements.
#

# Arrête le script si une commande échoue
set -e

# --- CONFIGURATION ---
PROD_DB_NAME="NidsObservation_Production"
PILOTE_DB_NAME="NidsObservation"

PROD_PROJECT_DIR="/var/www/html/Observations_Nids/"
PILOTE_PROJECT_DIR="/var/www/observations_nids_pilote/"

# Fichiers temporaires
PROD_MIGRATIONS_LIST="/tmp/prod_migrations.txt"
PILOTE_MIGRATIONS_LIST="/tmp/pilote_migrations.txt"
BACKUP_FILE="/tmp/prod_dump.sql"
# ---------------------

echo "--- 1. Vérification de la concordance des schémas via les migrations ---"

# Génère la liste des migrations appliquées pour chaque environnement
(cd $PROD_PROJECT_DIR && python3 manage.py showmigrations | grep '\[X\]') > $PROD_MIGRATIONS_LIST
(cd $PILOTE_PROJECT_DIR && python3 manage.py showmigrations | grep '\[X\]') > $PILOTE_MIGRATIONS_LIST

# Compare les deux listes
if ! diff -q $PROD_MIGRATIONS_LIST $PILOTE_MIGRATIONS_LIST; then
    echo "ERREUR : Les schémas des bases de données ne sont pas identiques."
    echo "Les listes de migrations appliquées diffèrent entre la production et le pilote."
    echo "Veuillez vous assurer d'utiliser la même version de code et d'avoir lancé 'python3 manage.py migrate' sur les deux environnements."
    rm $PROD_MIGRATIONS_LIST $PILOTE_MIGRATIONS_LIST
    exit 1
else
    echo "OK : Les schémas sont identiques. Poursuite de la synchronisation."
fi

rm $PROD_MIGRATIONS_LIST $PILOTE_MIGRATIONS_LIST

echo -e "\n--- 2. Lancement de la synchronisation des données ---"
read -p "ATTENTION : Les données de '$PILOTE_DB_NAME' vont être écrasées. Continuer ? (o/N) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Oo]$ ]]
then
    exit 1
fi

echo "--- Sauvegarde de sécurité de la base pilote... ---"
mysqldump --single-transaction "$PILOTE_DB_NAME" > "/tmp/${PILOTE_DB_NAME}.$(date +%F-%H%M%S).bak.sql"
echo "Sauvegarde créée dans /tmp/"

echo "--- Export de la base de données de production ($PROD_DB_NAME)... ---"
mysqldump --single-transaction --routines --triggers "$PROD_DB_NAME" > "$BACKUP_FILE"
echo "Export terminé."

echo "--- Import dans la base de données pilote ($PILOTE_DB_NAME)... ---"
mysql "$PILOTE_DB_NAME" < "$BACKUP_FILE"
echo "Import pilote terminé."

echo "--- Nettoyage du fichier d'export... ---"
rm "$BACKUP_FILE"
echo "Nettoyage terminé."

echo -e "\n--- Synchronisation terminée avec succès ! ---"
