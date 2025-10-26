#!/bin/bash
#
# Script de génération des statistiques GoAccess avec filtrage bots
# Génère des rapports séparés : humains, bots, et total
#
# Usage: sudo ./generate_stats_v2.sh
#
# Auteur: Generated with Claude Code
# Date: 26 octobre 2025
# Version: 2.0 - Ajout filtrage bots
#

set -e  # Arrêter en cas d'erreur

# ========================================
# CONFIGURATION
# ========================================

# Répertoires
LOG_DIR="/var/log/apache2"
STATS_DIR="/var/www/html/stats"
TEMP_DIR="/tmp/goaccess"
GOACCESS_CONF="/goaccess/goaccess.conf"

# Fichiers de log
METEO_LOG="$LOG_DIR/access.log"
DJANGO_LOG="$LOG_DIR/django-access.log"

# Fichiers temporaires (logs filtrés)
METEO_HUMANS="$TEMP_DIR/meteo_humans.log"
METEO_BOTS="$TEMP_DIR/meteo_bots.log"
DJANGO_HUMANS="$TEMP_DIR/django_humans.log"
DJANGO_BOTS="$TEMP_DIR/django_bots.log"

# Fichiers de sortie HTML
METEO_HTML="$STATS_DIR/meteo/index.html"
METEO_BOTS_HTML="$STATS_DIR/meteo/bots.html"
DJANGO_HTML="$STATS_DIR/observations/index.html"
DJANGO_BOTS_HTML="$STATS_DIR/observations/bots.html"
COMBINED_HTML="$STATS_DIR/global/index.html"
COMBINED_BOTS_HTML="$STATS_DIR/global/bots.html"
DASHBOARD_HTML="$STATS_DIR/index.html"

# Options GoAccess
LOG_FORMAT="COMBINED"
GOACCESS_OPTS="--log-format=$LOG_FORMAT"

# Liste des patterns de bots (expressions régulières grep -E)
BOT_PATTERNS=(
    "bot|Bot|BOT"                          # Bots génériques
    "crawler|Crawler|spider|Spider"        # Crawlers
    "Go-http-client"                       # Go bots
    "Facebot|facebookexternalhit"         # Facebook
    "Twitterbot"                           # Twitter
    "abuse\.xmco\.fr"                      # Scanner sécurité XMCO
    "CensysInspect"                        # Censys scanner
    "zgrab"                                # ZGrab scanner
    "Keydrop\.io"                          # Keydrop scanner
    "Palo Alto Networks"                   # Palo Alto scanner
    "xfa1"                                 # Scanner xfa1
    "Googlebot|Bingbot|YandexBot"         # Moteurs de recherche
    "Slackbot|Discordbot|TelegramBot"     # Bots messaging
    "Applebot|AhrefsBot|SemrushBot"       # Autres crawlers connus
    "curl|wget|python-requests"            # Outils HTTP
    "Scrapy|Selenium"                      # Scraping
)

# Construire le pattern grep
BOT_PATTERN=$(IFS="|"; echo "${BOT_PATTERNS[*]}")

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

    if ! command -v goaccess &> /dev/null; then
        log_error "GoAccess n'est pas installé"
        exit 1
    fi

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

    mkdir -p "$TEMP_DIR"
    mkdir -p "$STATS_DIR/meteo"
    mkdir -p "$STATS_DIR/observations"
    mkdir -p "$STATS_DIR/global"

    chown -R www-data:www-data "$STATS_DIR"
    chmod -R 755 "$STATS_DIR"

    log_info "Répertoires créés"
}

filter_logs() {
    log_info "Filtrage des logs (humains vs bots)..."

    # Filtrer les logs météo
    grep -Ev "$BOT_PATTERN" "$METEO_LOG" > "$METEO_HUMANS" 2>/dev/null || touch "$METEO_HUMANS"
    grep -E "$BOT_PATTERN" "$METEO_LOG" > "$METEO_BOTS" 2>/dev/null || touch "$METEO_BOTS"

    # Filtrer les logs Django
    grep -Ev "$BOT_PATTERN" "$DJANGO_LOG" > "$DJANGO_HUMANS" 2>/dev/null || touch "$DJANGO_HUMANS"
    grep -E "$BOT_PATTERN" "$DJANGO_LOG" > "$DJANGO_BOTS" 2>/dev/null || touch "$DJANGO_BOTS"

    # Compter les lignes
    METEO_HUMAN_COUNT=$(wc -l < "$METEO_HUMANS" 2>/dev/null || echo "0")
    METEO_BOT_COUNT=$(wc -l < "$METEO_BOTS" 2>/dev/null || echo "0")
    DJANGO_HUMAN_COUNT=$(wc -l < "$DJANGO_HUMANS" 2>/dev/null || echo "0")
    DJANGO_BOT_COUNT=$(wc -l < "$DJANGO_BOTS" 2>/dev/null || echo "0")

    log_info "Météo: $METEO_HUMAN_COUNT humains, $METEO_BOT_COUNT bots"
    log_info "Django: $DJANGO_HUMAN_COUNT humains, $DJANGO_BOT_COUNT bots"
}

generate_meteo_stats() {
    log_info "Génération des statistiques du site météo (humains)..."

    if [ -s "$METEO_HUMANS" ]; then
        goaccess "$METEO_HUMANS" \
            -o "$METEO_HTML" \
            $GOACCESS_OPTS \
            --html-report-title="Statistiques meteo-poelley50.fr (Humains)" \
            2>&1 | grep -v "^$" || true
        log_info "✓ Statistiques météo (humains) générées"
    else
        log_info "⚠ Aucune donnée humaine pour météo"
    fi

    # Bots
    if [ -s "$METEO_BOTS" ]; then
        log_info "Génération des statistiques des bots météo..."
        goaccess "$METEO_BOTS" \
            -o "$METEO_BOTS_HTML" \
            $GOACCESS_OPTS \
            --html-report-title="Statistiques meteo-poelley50.fr (Bots)" \
            2>&1 | grep -v "^$" || true
        log_info "✓ Statistiques météo (bots) générées"
    fi
}

generate_django_stats() {
    log_info "Génération des statistiques Observations Nids (humains)..."

    if [ -s "$DJANGO_HUMANS" ]; then
        goaccess "$DJANGO_HUMANS" \
            -o "$DJANGO_HTML" \
            $GOACCESS_OPTS \
            --html-report-title="Statistiques observation-nids (Humains)" \
            2>&1 | grep -v "^$" || true
        log_info "✓ Statistiques Django (humains) générées"
    else
        log_info "⚠ Aucune donnée humaine pour Django"
    fi

    # Bots
    if [ -s "$DJANGO_BOTS" ]; then
        log_info "Génération des statistiques des bots Django..."
        goaccess "$DJANGO_BOTS" \
            -o "$DJANGO_BOTS_HTML" \
            $GOACCESS_OPTS \
            --html-report-title="Statistiques observation-nids (Bots)" \
            2>&1 | grep -v "^$" || true
        log_info "✓ Statistiques Django (bots) générées"
    fi
}

generate_combined_stats() {
    log_info "Génération des statistiques globales (humains)..."

    if [ -s "$METEO_HUMANS" ] || [ -s "$DJANGO_HUMANS" ]; then
        goaccess "$METEO_HUMANS" "$DJANGO_HUMANS" \
            -o "$COMBINED_HTML" \
            $GOACCESS_OPTS \
            --html-report-title="Statistiques globales (Humains)" \
            2>&1 | grep -v "^$" || true
        log_info "✓ Statistiques globales (humains) générées"
    fi

    # Bots
    if [ -s "$METEO_BOTS" ] || [ -s "$DJANGO_BOTS" ]; then
        log_info "Génération des statistiques globales bots..."
        goaccess "$METEO_BOTS" "$DJANGO_BOTS" \
            -o "$COMBINED_BOTS_HTML" \
            $GOACCESS_OPTS \
            --html-report-title="Statistiques globales (Bots)" \
            2>&1 | grep -v "^$" || true
        log_info "✓ Statistiques globales (bots) générées"
    fi
}

generate_dashboard() {
    log_info "Génération du tableau de bord..."

    # Calculer les totaux
    TOTAL_METEO=$((METEO_HUMAN_COUNT + METEO_BOT_COUNT))
    TOTAL_DJANGO=$((DJANGO_HUMAN_COUNT + DJANGO_BOT_COUNT))
    TOTAL_GLOBAL=$((TOTAL_METEO + TOTAL_DJANGO))
    TOTAL_HUMANS=$((METEO_HUMAN_COUNT + DJANGO_HUMAN_COUNT))
    TOTAL_BOTS=$((METEO_BOT_COUNT + DJANGO_BOT_COUNT))

    # Calculer les pourcentages
    if [ $TOTAL_METEO -gt 0 ]; then
        METEO_BOT_PERCENT=$((METEO_BOT_COUNT * 100 / TOTAL_METEO))
    else
        METEO_BOT_PERCENT=0
    fi

    if [ $TOTAL_DJANGO -gt 0 ]; then
        DJANGO_BOT_PERCENT=$((DJANGO_BOT_COUNT * 100 / TOTAL_DJANGO))
    else
        DJANGO_BOT_PERCENT=0
    fi

    if [ $TOTAL_GLOBAL -gt 0 ]; then
        GLOBAL_BOT_PERCENT=$((TOTAL_BOTS * 100 / TOTAL_GLOBAL))
    else
        GLOBAL_BOT_PERCENT=0
    fi

    LAST_UPDATE=$(date +'%d/%m/%Y à %H:%M:%S')

    cat > "$DASHBOARD_HTML" << 'EOFHTML'
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
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }

        .container {
            max-width: 1400px;
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
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-bottom: 30px;
        }

        .stat-card {
            background: white;
            border-radius: 12px;
            padding: 20px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            transition: transform 0.3s ease;
        }

        .stat-card:hover {
            transform: translateY(-5px);
        }

        .stat-card h3 {
            color: #667eea;
            font-size: 0.85em;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 10px;
        }

        .stat-card .number {
            font-size: 2em;
            font-weight: bold;
            color: #333;
        }

        .stat-card .detail {
            font-size: 0.9em;
            color: #666;
            margin-top: 5px;
        }

        .stat-card.bot {
            border-left: 4px solid #e74c3c;
        }

        .stat-card.human {
            border-left: 4px solid #2ecc71;
        }

        .bot-badge {
            display: inline-block;
            background: #e74c3c;
            color: white;
            padding: 2px 8px;
            border-radius: 12px;
            font-size: 0.75em;
            margin-left: 5px;
        }

        .human-badge {
            display: inline-block;
            background: #2ecc71;
            color: white;
            padding: 2px 8px;
            border-radius: 12px;
            font-size: 0.75em;
            margin-left: 5px;
        }

        .reports-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
            gap: 20px;
            margin-bottom: 40px;
        }

        .report-card {
            background: white;
            border-radius: 12px;
            overflow: hidden;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            transition: transform 0.3s ease;
        }

        .report-card:hover {
            transform: translateY(-5px);
        }

        .report-header {
            padding: 25px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }

        .report-header h2 {
            font-size: 1.4em;
            margin-bottom: 5px;
        }

        .report-header p {
            opacity: 0.9;
            font-size: 0.9em;
        }

        .report-body {
            padding: 20px;
        }

        .report-body ul {
            list-style: none;
            margin-bottom: 15px;
        }

        .report-body li {
            margin-bottom: 10px;
        }

        .report-body a {
            display: inline-flex;
            align-items: center;
            color: #667eea;
            text-decoration: none;
            font-weight: 500;
            transition: color 0.3s ease;
            padding: 5px 10px;
            border-radius: 5px;
        }

        .report-body a:hover {
            background: #f0f0f0;
            color: #764ba2;
        }

        .report-body a::before {
            content: "→";
            margin-right: 8px;
            font-size: 1.2em;
        }

        .report-body a.bot-link {
            color: #e74c3c;
        }

        .report-body a.bot-link:hover {
            color: #c0392b;
        }

        .legend {
            background: white;
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 30px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        }

        .legend h3 {
            color: #333;
            margin-bottom: 15px;
        }

        .legend-item {
            display: inline-flex;
            align-items: center;
            margin-right: 25px;
            margin-bottom: 10px;
        }

        .legend-color {
            width: 20px;
            height: 20px;
            border-radius: 4px;
            margin-right: 8px;
        }

        .legend-color.human {
            background: #2ecc71;
        }

        .legend-color.bot {
            background: #e74c3c;
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

        <div class="legend">
            <h3>🔍 Légende</h3>
            <div class="legend-item">
                <div class="legend-color human"></div>
                <span><strong>Humains</strong> - Visiteurs réels (navigateurs)</span>
            </div>
            <div class="legend-item">
                <div class="legend-color bot"></div>
                <span><strong>Bots</strong> - Robots (crawlers, scanners, monitoring)</span>
            </div>
        </div>

        <div class="stats-overview">
            <div class="stat-card human">
                <h3>👥 Total Humains</h3>
                <div class="number">TOTAL_HUMANS_PLACEHOLDER</div>
                <p class="detail">requêtes aujourd'hui</p>
            </div>

            <div class="stat-card bot">
                <h3>🤖 Total Bots</h3>
                <div class="number">TOTAL_BOTS_PLACEHOLDER</div>
                <p class="detail">requêtes aujourd'hui (GLOBAL_BOT_PERCENT_PLACEHOLDER%)</p>
            </div>

            <div class="stat-card">
                <h3>🌤️ Site Météo</h3>
                <div class="number">TOTAL_METEO_PLACEHOLDER</div>
                <p class="detail">
                    <span class="human-badge">METEO_HUMAN_COUNT_PLACEHOLDER humains</span>
                    <span class="bot-badge">METEO_BOT_COUNT_PLACEHOLDER bots (METEO_BOT_PERCENT_PLACEHOLDER%)</span>
                </p>
            </div>

            <div class="stat-card">
                <h3>🦅 Observations</h3>
                <div class="number">TOTAL_DJANGO_PLACEHOLDER</div>
                <p class="detail">
                    <span class="human-badge">DJANGO_HUMAN_COUNT_PLACEHOLDER humains</span>
                    <span class="bot-badge">DJANGO_BOT_COUNT_PLACEHOLDER bots (DJANGO_BOT_PERCENT_PLACEHOLDER%)</span>
                </p>
            </div>

            <div class="stat-card">
                <h3>🌍 Total Global</h3>
                <div class="number">TOTAL_GLOBAL_PLACEHOLDER</div>
                <p class="detail">tous sites confondus</p>
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
                        <li><a href="meteo/">Rapport humains</a></li>
                        <li><a href="meteo/bots.html" class="bot-link">Rapport bots</a></li>
                    </ul>
                </div>
            </div>

            <div class="report-card">
                <div class="report-header">
                    <h2>🦅 Observations Nids</h2>
                    <p>observation-nids.meteo-poelley50.fr</p>
                </div>
                <div class="report-body">
                    <ul>
                        <li><a href="observations/">Rapport humains</a></li>
                        <li><a href="observations/bots.html" class="bot-link">Rapport bots</a></li>
                    </ul>
                </div>
            </div>

            <div class="report-card">
                <div class="report-header">
                    <h2>🌍 Vue Globale</h2>
                    <p>Tous les sites combinés</p>
                </div>
                <div class="report-body">
                    <ul>
                        <li><a href="global/">Rapport humains</a></li>
                        <li><a href="global/bots.html" class="bot-link">Rapport bots</a></li>
                    </ul>
                </div>
            </div>
        </div>

        <footer>
            <p class="last-update">Dernière mise à jour : LAST_UPDATE_PLACEHOLDER</p>
            <p style="margin-top: 10px; font-size: 0.85em;">Généré par GoAccess avec filtrage bots</p>
        </footer>
    </div>
</body>
</html>
EOFHTML

    # Remplacer les placeholders
    sed -i "s/TOTAL_HUMANS_PLACEHOLDER/$TOTAL_HUMANS/g" "$DASHBOARD_HTML"
    sed -i "s/TOTAL_BOTS_PLACEHOLDER/$TOTAL_BOTS/g" "$DASHBOARD_HTML"
    sed -i "s/TOTAL_METEO_PLACEHOLDER/$TOTAL_METEO/g" "$DASHBOARD_HTML"
    sed -i "s/TOTAL_DJANGO_PLACEHOLDER/$TOTAL_DJANGO/g" "$DASHBOARD_HTML"
    sed -i "s/TOTAL_GLOBAL_PLACEHOLDER/$TOTAL_GLOBAL/g" "$DASHBOARD_HTML"
    sed -i "s/METEO_HUMAN_COUNT_PLACEHOLDER/$METEO_HUMAN_COUNT/g" "$DASHBOARD_HTML"
    sed -i "s/METEO_BOT_COUNT_PLACEHOLDER/$METEO_BOT_COUNT/g" "$DASHBOARD_HTML"
    sed -i "s/DJANGO_HUMAN_COUNT_PLACEHOLDER/$DJANGO_HUMAN_COUNT/g" "$DASHBOARD_HTML"
    sed -i "s/DJANGO_BOT_COUNT_PLACEHOLDER/$DJANGO_BOT_COUNT/g" "$DASHBOARD_HTML"
    sed -i "s/METEO_BOT_PERCENT_PLACEHOLDER/$METEO_BOT_PERCENT/g" "$DASHBOARD_HTML"
    sed -i "s/DJANGO_BOT_PERCENT_PLACEHOLDER/$DJANGO_BOT_PERCENT/g" "$DASHBOARD_HTML"
    sed -i "s/GLOBAL_BOT_PERCENT_PLACEHOLDER/$GLOBAL_BOT_PERCENT/g" "$DASHBOARD_HTML"
    sed -i "s/LAST_UPDATE_PLACEHOLDER/$LAST_UPDATE/g" "$DASHBOARD_HTML"

    log_info "✓ Tableau de bord généré"
}

cleanup() {
    log_info "Nettoyage des fichiers temporaires..."
    rm -f "$TEMP_DIR"/*.log
}

# ========================================
# MAIN
# ========================================

main() {
    log_info "=== Génération des statistiques GoAccess avec filtrage bots ==="

    check_requirements
    create_directories
    filter_logs

    # Génération des rapports
    generate_meteo_stats
    generate_django_stats
    generate_combined_stats
    generate_dashboard

    cleanup

    log_info "=== Génération terminée avec succès ==="
    log_info ""
    log_info "Statistiques:"
    log_info "  Humains: $TOTAL_HUMANS requêtes"
    log_info "  Bots:    $TOTAL_BOTS requêtes ($GLOBAL_BOT_PERCENT%)"
    log_info ""
    log_info "Accès:"
    log_info "  Dashboard: http://meteo-poelley50.fr/stats/"
}

# Exécution
main "$@"
