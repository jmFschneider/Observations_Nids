#!/bin/bash
# Script pour activer le mode maintenance
# Usage: ./scripts/maintenance_on.sh

set -e  # Arrêt en cas d'erreur

# Configuration
PROJECT_DIR="/var/www/observations_nids"
MAINTENANCE_FILE="$PROJECT_DIR/.maintenance"

echo "================================================"
echo "🔧 ACTIVATION DU MODE MAINTENANCE"
echo "================================================"
echo ""

# Vérifier que le script est exécuté avec sudo si nécessaire
if [ ! -w "$PROJECT_DIR" ]; then
    echo "⚠️  Ce script nécessite les permissions sudo"
    echo "   Relancez avec: sudo ./scripts/maintenance_on.sh"
    exit 1
fi

# Créer le fichier .maintenance
echo "📝 Création du fichier .maintenance..."
touch "$MAINTENANCE_FILE"

if [ -f "$MAINTENANCE_FILE" ]; then
    echo "✅ Fichier .maintenance créé"
else
    echo "❌ Erreur : Impossible de créer le fichier .maintenance"
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
echo "✅ MODE MAINTENANCE ACTIVÉ"
echo "================================================"
echo ""
echo "📍 Les visiteurs verront maintenant :"
echo "   https://observations.meteo-poelley50.fr/maintenance.html"
echo ""
echo "💡 Votre IP peut accéder au site normalement (whitelist)"
echo ""
echo "Pour désactiver la maintenance :"
echo "   ./scripts/maintenance_off.sh"
echo ""
