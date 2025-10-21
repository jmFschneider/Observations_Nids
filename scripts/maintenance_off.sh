#!/bin/bash
# Script pour désactiver le mode maintenance
# Usage: ./scripts/maintenance_off.sh

set -e  # Arrêt en cas d'erreur

# Configuration
PROJECT_DIR="/var/www/observations_nids"
MAINTENANCE_FILE="$PROJECT_DIR/.maintenance"

echo "================================================"
echo "✨ DÉSACTIVATION DU MODE MAINTENANCE"
echo "================================================"
echo ""

# Vérifier que le script est exécuté avec sudo si nécessaire
if [ ! -w "$PROJECT_DIR" ]; then
    echo "⚠️  Ce script nécessite les permissions sudo"
    echo "   Relancez avec: sudo ./scripts/maintenance_off.sh"
    exit 1
fi

# Vérifier que le mode maintenance est activé
if [ ! -f "$MAINTENANCE_FILE" ]; then
    echo "⚠️  Le mode maintenance n'est pas activé"
    echo "   (fichier .maintenance introuvable)"
    echo ""
    echo "Le site est déjà accessible normalement."
    exit 0
fi

# Supprimer le fichier .maintenance
echo "🗑️  Suppression du fichier .maintenance..."
rm -f "$MAINTENANCE_FILE"

if [ ! -f "$MAINTENANCE_FILE" ]; then
    echo "✅ Fichier .maintenance supprimé"
else
    echo "❌ Erreur : Impossible de supprimer le fichier .maintenance"
    exit 1
fi

# Recharger Apache
echo ""
echo "🔄 Rechargement d'Apache..."
systemctl reload apache2

if [ $? -eq 0 ]; then
    echo "✅ Apache rechargé avec succès"
else
    echo "❌ Erreur lors du rechargement d'Apache"
    exit 1
fi

echo ""
echo "================================================"
echo "✅ MODE MAINTENANCE DÉSACTIVÉ"
echo "================================================"
echo ""
echo "📍 Le site est de nouveau accessible normalement :"
echo "   https://observations.meteo-poelley50.fr/"
echo ""
echo "🎉 Maintenance terminée avec succès !"
echo ""
