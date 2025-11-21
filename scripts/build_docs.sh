#!/bin/bash

# Script de build de la documentation utilisateur
# Ce script construit la documentation MkDocs et la copie dans staticfiles pour Apache

set -e  # Arrêter en cas d'erreur

echo "🔧 Construction de la documentation utilisateur..."

# Se placer dans le dossier docs
cd "$(dirname "$0")/../docs"

# Builder la documentation avec MkDocs
echo "📦 Build MkDocs..."
mkdocs build --config-file=mkdocs.yml --clean

# Créer le dossier de destination si nécessaire
STATIC_DOCS_DIR="../staticfiles/docs"
mkdir -p "$STATIC_DOCS_DIR"

# Copier les fichiers buildés vers staticfiles
echo "📂 Copie vers staticfiles/docs/..."
cp -r ../site-user/* "$STATIC_DOCS_DIR/"

echo "✅ Documentation buildée avec succès !"
echo "📍 Emplacement : staticfiles/docs/"
echo ""
echo "ℹ️  Pour déployer en production :"
echo "   1. Committez les changements dans staticfiles/docs/"
echo "   2. Déployez sur le Raspberry Pi"
echo "   3. Apache servira automatiquement /static/docs/"
