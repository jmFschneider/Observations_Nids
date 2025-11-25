#!/bin/bash
# Script pour activer le mode maintenance avec durée personnalisée
# Usage: ./scripts/maintenance_on.sh

set -e  # Arrêt en cas d'erreur

# Configuration
PROJECT_DIR="/var/www/html/Observations_Nids"
MAINTENANCE_FILE="$PROJECT_DIR/.maintenance"
MAINTENANCE_HTML="$PROJECT_DIR/maintenance.html"

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

# Menu interactif pour choisir la durée
echo "📅 Quelle est la durée estimée de la maintenance ?"
echo ""
echo "1) Quelques minutes (< 30 min)"
echo "2) Environ 1 heure"
echo "3) Quelques heures (2-4h)"
echo "4) Une demi-journée"
echo "5) Jusqu'à une date/heure précise"
echo "6) Durée indéterminée"
echo ""
read -p "Votre choix (1-6) : " choice
echo ""

# Définir le message de durée en fonction du choix
case $choice in
    1)
        duration_msg="Quelques minutes"
        ;;
    2)
        duration_msg="Environ 1 heure"
        ;;
    3)
        duration_msg="Quelques heures (2-4h)"
        ;;
    4)
        duration_msg="Une demi-journée"
        ;;
    5)
        read -p "Date et heure de fin (ex: 15/01/2025 à 14h30) : " custom_date
        duration_msg="Jusqu'au $custom_date"
        ;;
    6)
        duration_msg="Durée indéterminée"
        ;;
    *)
        echo "❌ Choix invalide"
        exit 1
        ;;
esac

# Demander la raison (optionnel)
echo ""
read -p "📋 Raison de la maintenance (optionnel, Entrée pour ignorer) : " reason
if [ -z "$reason" ]; then
    reason="Mise à jour et amélioration du site"
fi
echo ""

# Créer le fichier .maintenance
echo "📝 Création du fichier .maintenance..."
touch "$MAINTENANCE_FILE"

if [ -f "$MAINTENANCE_FILE" ]; then
    echo "✅ Fichier .maintenance créé"
else
    echo "❌ Erreur : Impossible de créer le fichier .maintenance"
    exit 1
fi

# Générer le fichier maintenance.html avec les informations personnalisées
echo "📄 Génération de la page maintenance.html..."
cat > "$MAINTENANCE_HTML" << 'EOF_HTML'
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Maintenance - Observations Nids</title>
    <meta http-equiv="refresh" content="60">
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #333;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            padding: 20px;
        }

        .container {
            background: white;
            border-radius: 20px;
            padding: 60px 40px;
            max-width: 600px;
            text-align: center;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
            animation: fadeIn 0.5s ease-in;
        }

        @keyframes fadeIn {
            from {
                opacity: 0;
                transform: translateY(-20px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }

        .icon {
            font-size: 80px;
            margin-bottom: 20px;
            animation: bounce 2s infinite;
        }

        @keyframes bounce {
            0%, 100% {
                transform: translateY(0);
            }
            50% {
                transform: translateY(-10px);
            }
        }

        h1 {
            font-size: 2.5em;
            margin-bottom: 20px;
            color: #667eea;
        }

        p {
            font-size: 1.2em;
            line-height: 1.6;
            color: #666;
            margin-bottom: 30px;
        }

        .info {
            background: #f8f9fa;
            border-left: 4px solid #667eea;
            padding: 20px;
            border-radius: 5px;
            margin-top: 30px;
            text-align: left;
        }

        .info p {
            margin-bottom: 10px;
            font-size: 1em;
        }

        .info p:last-child {
            margin-bottom: 0;
        }

        .info strong {
            color: #667eea;
        }

        .spinner {
            border: 4px solid #f3f3f3;
            border-top: 4px solid #667eea;
            border-radius: 50%;
            width: 50px;
            height: 50px;
            animation: spin 1s linear infinite;
            margin: 30px auto;
        }

        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }

        .contact {
            margin-top: 20px;
            font-size: 0.9em;
            color: #999;
        }

        .refresh-info {
            margin-top: 20px;
            padding: 15px;
            background: #e7f3ff;
            border-radius: 5px;
            font-size: 0.9em;
            color: #0066cc;
        }

        @media (max-width: 600px) {
            .container {
                padding: 40px 20px;
            }

            h1 {
                font-size: 2em;
            }

            .icon {
                font-size: 60px;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="icon">🔧</div>
        <h1>Maintenance en cours</h1>
        <p>
            Le site <strong>Observations Nids</strong> est actuellement en maintenance
            pour améliorer votre expérience.
        </p>

        <div class="spinner"></div>

        <div class="info">
            <p><strong>⏱️ Durée estimée :</strong> DURATION_PLACEHOLDER</p>
            <p><strong>📋 Raison :</strong> REASON_PLACEHOLDER</p>
            <p><strong>✨ Nous serons bientôt de retour !</strong></p>
        </div>

        <div class="refresh-info">
            🔄 Cette page se rafraîchit automatiquement toutes les 60 secondes
        </div>

        <div class="contact">
            En cas d'urgence, contactez l'administrateur du site.
        </div>
    </div>
</body>
</html>
EOF_HTML

# Remplacer les placeholders par les valeurs réelles
sed -i "s/DURATION_PLACEHOLDER/$duration_msg/g" "$MAINTENANCE_HTML"
sed -i "s/REASON_PLACEHOLDER/$reason/g" "$MAINTENANCE_HTML"

if [ -f "$MAINTENANCE_HTML" ]; then
    echo "✅ Page maintenance.html générée"
else
    echo "❌ Erreur : Impossible de créer maintenance.html"
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
echo "📋 Informations affichées :"
echo "   ⏱️  Durée : $duration_msg"
echo "   📝 Raison : $reason"
echo ""
echo "💡 Votre IP peut accéder au site normalement (whitelist)"
echo ""
echo "Pour désactiver la maintenance :"
echo "   sudo ./scripts/maintenance_off.sh"
echo ""
