#!/bin/bash
#
# Script de génération des statistiques GoAccess
# Génère des rapports séparés pour chaque site et un dashboard global
#
# Usage: sudo ./generate_stats.sh
#
# Auteur: Generated with Claude Code
# Date: 26 octobre 2025
#

set -e  # Arrêter en cas d'erreur

# ========================================
# CONFIGURATION
# ========================================

# Répertoires
LOG_DIR="/var/log/apache2"
STATS_DIR="/var/www/html/stats"
GOACCESS_CONF="/goaccess/goaccess.conf"

# Fichiers de log
METEO_LOG="$LOG_DIR/access.log"
DJANGO_LOG="$LOG_DIR/django-access.log"

# Fichiers de sortie
METEO_HTML="$STATS_DIR/meteo/index.html"
DJANGO_HTML="$STATS_DIR/observations/index.html"
COMBINED_HTML="$STATS_DIR/global/index.html"
DASHBOARD_HTML="$STATS_DIR/index.html"

# Options GoAccess
LOG_FORMAT="COMBINED"
GOACCESS_OPTS="--log-format=$LOG_FORMAT"

# Ajouter le fichier de config si il existe
if [ -f "$GOACCESS_CONF" ]; then
    GOACCESS_OPTS="$GOACCESS_OPTS --config-file=$GOACCESS_CONF"
fi

# ========================================
# FONCTIONS
# ========================================

log_info() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] INFO: $1"
}

log_error() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $1" >&2
}

check_requirements() {
    log_info "Vérification des prérequis..."

    # Vérifier que goaccess est installé
    if ! command -v goaccess &> /dev/null; then
        log_error "GoAccess n'est pas installé. Installez-le avec: sudo apt install goaccess"
        exit 1
    fi

    # Vérifier que les logs existent
    if [ ! -f "$METEO_LOG" ]; then
        log_error "Fichier de log météo introuvable: $METEO_LOG"
        exit 1
    fi

    if [ ! -f "$DJANGO_LOG" ]; then
        log_error "Fichier de log Django introuvable: $DJANGO_LOG"
        exit 1
    fi

    log_info "Prérequis OK"
}

create_directories() {
    log_info "Création de la structure de répertoires..."

    mkdir -p "$STATS_DIR/meteo"
    mkdir -p "$STATS_DIR/observations"
    mkdir -p "$STATS_DIR/global"

    # Permissions
    chown -R www-data:www-data "$STATS_DIR"
    chmod -R 755 "$STATS_DIR"

    log_info "Répertoires créés"
}

generate_meteo_stats() {
    log_info "Génération des statistiques du site météo..."

    goaccess "$METEO_LOG" \
        -o "$METEO_HTML" \
        $GOACCESS_OPTS \
        --html-report-title="Statistiques meteo-poelley50.fr" \
        2>&1 | grep -v "^$" || true

    log_info "✓ Statistiques météo générées: $METEO_HTML"
}

generate_django_stats() {
    log_info "Génération des statistiques Observations Nids..."

    goaccess "$DJANGO_LOG" \
        -o "$DJANGO_HTML" \
        $GOACCESS_OPTS \
        --html-report-title="Statistiques observation-nids.meteo-poelley50.fr" \
        2>&1 | grep -v "^$" || true

    log_info "✓ Statistiques Observations Nids générées: $DJANGO_HTML"
}

generate_combined_stats() {
    log_info "Génération des statistiques globales (tous sites)..."

    goaccess "$METEO_LOG" "$DJANGO_LOG" \
        -o "$COMBINED_HTML" \
        $GOACCESS_OPTS \
        --html-report-title="Statistiques globales - Tous sites" \
        2>&1 | grep -v "^$" || true

    log_info "✓ Statistiques globales générées: $COMBINED_HTML"
}

generate_dashboard() {
    log_info "Génération du tableau de bord..."

    # Compter les visites dans les logs
    METEO_VISITS=$(wc -l < "$METEO_LOG" 2>/dev/null || echo "0")
    DJANGO_VISITS=$(wc -l < "$DJANGO_LOG" 2>/dev/null || echo "0")
    TOTAL_VISITS=$((METEO_VISITS + DJANGO_VISITS))

    # Date de dernière mise à jour
    LAST_UPDATE=$(date +'%d/%m/%Y à %H:%M:%S')

    cat > "$DASHBOARD_HTML" << 'EOF'
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Tableau de bord - Statistiques Web</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }

        .container {
            max-width: 1200px;
            margin: 0 auto;
        }

        header {
            text-align: center;
            color: white;
            margin-bottom: 40px;
        }

        h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
        }

        .subtitle {
            font-size: 1.2em;
            opacity: 0.9;
        }

        .stats-overview {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 40px;
        }

        .stat-card {
            background: white;
            border-radius: 12px;
            padding: 25px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }

        .stat-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 15px 40px rgba(0,0,0,0.3);
        }

        .stat-card h3 {
            color: #667eea;
            font-size: 0.9em;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 10px;
        }

        .stat-card .number {
            font-size: 2.5em;
            font-weight: bold;
            color: #333;
        }

        .reports-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 40px;
        }

        .report-card {
            background: white;
            border-radius: 12px;
            overflow: hidden;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }

        .report-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 15px 40px rgba(0,0,0,0.3);
        }

        .report-header {
            padding: 25px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }

        .report-header h2 {
            font-size: 1.5em;
            margin-bottom: 5px;
        }

        .report-header p {
            opacity: 0.9;
            font-size: 0.9em;
        }

        .report-body {
            padding: 25px;
        }

        .report-body ul {
            list-style: none;
        }

        .report-body li {
            margin-bottom: 12px;
        }

        .report-body a {
            display: flex;
            align-items: center;
            color: #667eea;
            text-decoration: none;
            font-weight: 500;
            transition: color 0.3s ease;
        }

        .report-body a:hover {
            color: #764ba2;
        }

        .report-body a::before {
            content: "→";
            margin-right: 10px;
            font-size: 1.2em;
        }

        .btn {
            display: inline-block;
            padding: 12px 30px;
            background: white;
            color: #667eea;
            text-decoration: none;
            border-radius: 25px;
            font-weight: 600;
            transition: all 0.3s ease;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        }

        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 7px 20px rgba(0,0,0,0.2);
        }

        footer {
            text-align: center;
            color: white;
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid rgba(255,255,255,0.2);
        }

        .last-update {
            font-size: 0.9em;
            opacity: 0.8;
        }

        @media (max-width: 768px) {
            h1 {
                font-size: 2em;
            }

            .stats-overview {
                grid-template-columns: 1fr;
            }

            .reports-grid {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>📊 Tableau de bord des statistiques</h1>
            <p class="subtitle">Analyse du trafic web - meteo-poelley50.fr</p>
        </header>

        <div class="stats-overview">
            <div class="stat-card">
                <h3>Site Météo</h3>
                <div class="number">METEO_VISITS_PLACEHOLDER</div>
                <p>requêtes aujourd'hui</p>
            </div>

            <div class="stat-card">
                <h3>Observations Nids</h3>
                <div class="number">DJANGO_VISITS_PLACEHOLDER</div>
                <p>requêtes aujourd'hui</p>
            </div>

            <div class="stat-card">
                <h3>Total Global</h3>
                <div class="number">TOTAL_VISITS_PLACEHOLDER</div>
                <p>requêtes aujourd'hui</p>
            </div>
        </div>

        <div class="reports-grid">
            <div class="report-card">
                <div class="report-header">
                    <h2>🌤️ Site Météo</h2>
                    <p>meteo-poelley50.fr (WeeWX)</p>
                </div>
                <div class="report-body">
                    <ul>
                        <li><a href="meteo/">Rapport complet</a></li>
                    </ul>
                    <p style="margin-top: 15px; color: #666; font-size: 0.9em;">
                        Analyse des visites, pages consultées, navigateurs, géolocalisation des visiteurs
                    </p>
                </div>
            </div>

            <div class="report-card">
                <div class="report-header">
                    <h2>🦅 Observations Nids</h2>
                    <p>observation-nids.meteo-poelley50.fr</p>
                </div>
                <div class="report-body">
                    <ul>
                        <li><a href="observations/">Rapport complet</a></li>
                    </ul>
                    <p style="margin-top: 15px; color: #666; font-size: 0.9em;">
                        Statistiques d'utilisation de l'application Django, pages explorées, actions utilisateurs
                    </p>
                </div>
            </div>

            <div class="report-card">
                <div class="report-header">
                    <h2>🌍 Vue Globale</h2>
                    <p>Tous les sites combinés</p>
                </div>
                <div class="report-body">
                    <ul>
                        <li><a href="global/">Rapport combiné</a></li>
                    </ul>
                    <p style="margin-top: 15px; color: #666; font-size: 0.9em;">
                        Analyse consolidée des deux sites pour une vue d'ensemble du trafic total
                    </p>
                </div>
            </div>
        </div>

        <footer>
            <p class="last-update">Dernière mise à jour : LAST_UPDATE_PLACEHOLDER</p>
            <p style="margin-top: 10px; font-size: 0.85em;">Généré par GoAccess</p>
        </footer>
    </div>
</body>
</html>
EOF

    # Remplacer les placeholders
    sed -i "s/METEO_VISITS_PLACEHOLDER/$METEO_VISITS/g" "$DASHBOARD_HTML"
    sed -i "s/DJANGO_VISITS_PLACEHOLDER/$DJANGO_VISITS/g" "$DASHBOARD_HTML"
    sed -i "s/TOTAL_VISITS_PLACEHOLDER/$TOTAL_VISITS/g" "$DASHBOARD_HTML"
    sed -i "s/LAST_UPDATE_PLACEHOLDER/$LAST_UPDATE/g" "$DASHBOARD_HTML"

    log_info "✓ Tableau de bord généré: $DASHBOARD_HTML"
}

# ========================================
# MAIN
# ========================================

main() {
    log_info "=== Génération des statistiques GoAccess ==="

    check_requirements
    create_directories

    # Génération des rapports
    generate_meteo_stats
    generate_django_stats
    generate_combined_stats
    generate_dashboard

    log_info "=== Génération terminée avec succès ==="
    log_info ""
    log_info "Accès aux statistiques:"
    log_info "  - Tableau de bord : http://meteo-poelley50.fr/stats/"
    log_info "  - Site météo      : http://meteo-poelley50.fr/stats/meteo/"
    log_info "  - Observations    : http://meteo-poelley50.fr/stats/observations/"
    log_info "  - Vue globale     : http://meteo-poelley50.fr/stats/global/"
}

# Exécution
main "$@"
