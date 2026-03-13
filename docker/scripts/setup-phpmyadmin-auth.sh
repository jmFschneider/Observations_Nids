#!/bin/bash
# =============================================================================
# setup-phpmyadmin-auth.sh - Crée le fichier htpasswd pour phpMyAdmin
# =============================================================================
# À exécuter UNE SEULE FOIS sur le serveur, avant d'activer phpMyAdmin
# =============================================================================
set -e

AUTH_DIR="/opt/observations_nids/docker/nginx/auth"
HTPASSWD_FILE="$AUTH_DIR/.htpasswd"

mkdir -p "$AUTH_DIR"

echo "=== Création des credentials phpMyAdmin ==="
read -p "Nom d'utilisateur : " PMA_USER
read -s -p "Mot de passe : " PMA_PASS
echo ""
read -s -p "Confirmer le mot de passe : " PMA_PASS2
echo ""

if [ "$PMA_PASS" != "$PMA_PASS2" ]; then
    echo "ERREUR : Les mots de passe ne correspondent pas."
    exit 1
fi

# Générer le htpasswd via Docker (pas besoin d'installer apache2-utils)
docker run --rm httpd:alpine htpasswd -nb "$PMA_USER" "$PMA_PASS" > "$HTPASSWD_FILE"

chmod 600 "$HTPASSWD_FILE"

echo ""
echo "=== Fichier htpasswd créé : $HTPASSWD_FILE ==="
echo "Vous pouvez maintenant activer phpMyAdmin avec :"
echo "  bash docker/scripts/enable-phpmyadmin.sh"
