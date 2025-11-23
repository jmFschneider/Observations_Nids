#!/bin/bash

# Script de build de la documentation utilisateur
# Ce script construit la documentation MkDocs dans site-user/
# Les fichiers seront collectés par 'python manage.py collectstatic'

set -e  # Arrêter en cas d'erreur

echo "🔧 Construction de la documentation utilisateur..."

# Se placer dans le dossier docs
cd "$(dirname "$0")/../docs"

# Builder la documentation avec MkDocs
echo "📦 Build MkDocs..."
mkdocs build --config-file=mkdocs.yml --clean

echo "✅ Documentation buildée avec succès !"
echo "📍 Emplacement : site-user/"
echo ""
echo "ℹ️  Prochaine étape :"
echo "   python manage.py collectstatic"
echo ""
echo "ℹ️  Pour déployer en production :"
echo "   1. Committez les changements dans site-user/"
echo "   2. Poussez : git push"
echo "   3. Sur le serveur : git pull && python manage.py collectstatic"
echo "   4. Redémarrez : sudo systemctl restart gunicorn"
