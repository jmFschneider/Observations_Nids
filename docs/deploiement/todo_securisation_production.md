# TODO — Sécurisation et finalisation du déploiement production OVH

> Document de travail issu de l'audit de sécurité réalisé en mars 2026.
> À traiter avant la mise en production définitive.
> **Règle** : une modification à la fois, testée sur une instance OVH bac à sable (depuis le snapshot) avant déploiement définitif.
> ⚠️ Ne jamais tester sur le pilote (= pré-production en cours d'utilisation).

---

## PRIORITÉ 0 — Suppression de Flower (avant toute sécurisation)

**Contexte** : Flower n'apporte pas d'information supplémentaire par rapport à ce que l'application affiche déjà (progression OCR en temps réel). Il consomme des ressources inutilement et ajoute une surface d'attaque.

**Méthode de test** : instance OVH bac à sable créée depuis le snapshot (sans toucher au snapshot de référence, sans mettre à jour le DNS Hostinger).

**Travail à faire :**

- [ ] Préparer les modifications en local (code) :
  - [ ] Supprimer le service `flower` de `docker-compose.prod.yml`
  - [ ] Supprimer le service `flower` de `docker-compose.yml`
  - [ ] Nettoyer les liens `/flower` dans `ocr/templates/ocr/selection_images.html`
  - [ ] Nettoyer les liens `/flower` dans `ocr/templates/ocr/selection_repertoire_ocr.html`
  - [ ] Nettoyer les liens `/flower` dans `taxonomy/templates/taxonomy/administration_donnees.html`
  - [ ] Supprimer `flower` des dépendances dans `requirements-base.txt` (si présent)
  - [ ] Commit + push

- [ ] Créer une instance OVH bac à sable depuis le snapshot (via Horizon → Launch)
  - Ne pas modifier le DNS Hostinger
  - Accès via IP directement : `https://[IP-BAC-A-SABLE]`

- [ ] Sur l'instance bac à sable :
  - [ ] `git pull`
  - [ ] `dcp build && dcp up -d`
  - [ ] Vérifier que le stack démarre sans Flower
  - [ ] Tester le lancement d'une transcription OCR (progression affichée ?)
  - [ ] Tester le lancement d'un import JSON
  - [ ] Vérifier qu'il n'y a pas d'erreur JS dans la console navigateur (liens /flower cassés ?)

- [ ] Si tout est bon :
  - [ ] Supprimer l'instance bac à sable
  - [ ] Prendre un nouveau snapshot de référence depuis l'instance principale (après `git pull`)

---

## Gestion du serveur OVH (coûts)

### Fermer le serveur (arrêter la facturation)

1. Désactiver phpMyAdmin si actif :
   ```bash
   bash /opt/observations_nids/docker/scripts/disable-phpmyadmin.sh
   ```
2. **Prendre un snapshot** avant de supprimer (Manager OVH → Public Cloud → Instances → `...` → Créer un snapshot)
3. **Supprimer l'instance** (Manager OVH → Public Cloud → Instances → `...` → Supprimer)
   - La facturation s'arrête immédiatement
   - Le snapshot est conservé (facturé ~0.04€/Go/mois)
   - L'IP publique est libérée

> ⚠️ Ne pas oublier de mettre à jour le DNS chez Hostinger après suppression
> (pointer l'enregistrement A vers l'IP du pilote ou le désactiver).

---

### Remettre le serveur en service

1. Manager OVH → Public Cloud → Instances → **Créer une instance**
   - Onglet **Depuis un snapshot** → sélectionner le dernier snapshot
   - Même modèle (B3-8) et même région
2. Récupérer la nouvelle IP publique
3. Mettre à jour l'enregistrement A chez Hostinger (TTL 300s → propagation ~5 min)
4. Se connecter en SSH :
   ```bash
   ssh ubuntu@[NOUVELLE-IP]
   ```
5. Vérifier que le stack a redémarré automatiquement :
   ```bash
   dcp ps
   ```
6. Si les règles iptables ne sont plus actives (rare) :
   ```bash
   sudo /etc/rc.local
   ```
7. Faire un `git pull` pour récupérer les derniers commits :
   ```bash
   cd /opt/observations_nids && sudo git pull
   ```

> Le stack Docker redémarre automatiquement grâce à `restart: unless-stopped`.
> La base de données, les médias et la configuration sont tous persistés.

---

## TODO Sécurisation — Par ordre de priorité

---

### PRIORITÉ 1 — En-têtes HTTP de sécurité (Nginx)

**Risque si absent** : Clickjacking, XSS, MIME-sniffing
**Impact sur le site** : Aucun risque de casser quoi que ce soit
**Fichier à modifier** : `docker/nginx/conf.d/prod.conf`

Ajouter dans le bloc `server { listen 443... }` :
```nginx
add_header X-Frame-Options "SAMEORIGIN" always;
add_header X-Content-Type-Options "nosniff" always;
add_header X-XSS-Protection "1; mode=block" always;
add_header Referrer-Policy "strict-origin-when-cross-origin" always;
```

**Test** : Vérifier avec [securityheaders.com](https://securityheaders.com) après déploiement.

- [ ] Modifier `prod.conf`
- [ ] Tester sur pilote
- [ ] Déployer sur OVH (`git pull` + `dcp restart nginx`)

---

### PRIORITÉ 2 — HSTS (Strict-Transport-Security)

**Risque si absent** : Downgrade HTTP possible
**Impact sur le site** : ⚠️ Attention — une fois activé, les navigateurs forcent HTTPS pendant `max-age` secondes. Commencer avec 1 heure, pas 1 an.
**Fichier à modifier** : `docker/nginx/conf.d/prod.conf`

```nginx
# Commencer avec max-age court (1 heure = 3600s) pour tester
add_header Strict-Transport-Security "max-age=3600" always;
# Après validation, passer à 1 an :
# add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
```

**Test** : Vérifier que le site reste accessible en HTTPS, puis augmenter progressivement.

- [ ] Ajouter HSTS avec `max-age=3600`
- [ ] Tester sur pilote pendant quelques jours
- [ ] Passer à `max-age=604800` (1 semaine)
- [ ] Passer à `max-age=31536000` (1 an) en production définitive

---

### PRIORITÉ 3 — Rate limiting (Nginx)

**Risque si absent** : Brute-force sur `/admin/`, `/phpmyadmin/`
**Impact sur le site** : ⚠️ Peut bloquer des utilisateurs légitimes si mal calibré
**Fichier à modifier** : `docker/nginx/conf.d/prod.conf`

Ajouter dans le bloc `http {}` (dans `nginx.conf`) :
```nginx
limit_req_zone $binary_remote_addr zone=login:10m rate=5r/m;
```

Puis dans `prod.conf`, appliquer sur les routes sensibles :
```nginx
location /admin/ {
    limit_req zone=login burst=3 nodelay;
    proxy_pass http://django_app;
    ...
}
```

**Test** : Vérifier que la navigation normale n'est pas affectée, tenter un accès rapide répété.

- [ ] Ajouter `limit_req_zone` dans `nginx.conf`
- [ ] Appliquer sur `/admin/` et `/phpmyadmin/`
- [ ] Tester sur pilote (connexion normale + test brute-force)
- [ ] Déployer sur OVH

---

### PRIORITÉ 4 — Vérification du renouvellement SSL

**Risque si absent** : Certificat expiré silencieusement
**Impact sur le site** : Aucun risque de casser quoi que ce soit
**Fichier à modifier** : `docker/scripts/renew-ssl.sh`

Ajouter une vérification du succès et une notification :
```bash
if ! certbot renew --quiet; then
    echo "[$(date)] ERREUR : renouvellement certbot échoué" >> /var/log/certbot-renew.log
    # Optionnel : envoyer un email d'alerte
fi

# Afficher la date d'expiration après renouvellement
openssl x509 -in /etc/letsencrypt/live/observation-nids.meteo-poelley50.fr/cert.pem \
    -noout -enddate >> /var/log/certbot-renew.log
```

- [ ] Modifier `renew-ssl.sh`
- [ ] Configurer logrotate pour `/var/log/certbot-renew.log`
- [ ] Tester manuellement le script

---

### PRIORITÉ 5 — phpMyAdmin avec utilisateur MariaDB dédié (non root)

**Risque si absent** : Accès root MariaDB si phpMyAdmin compromis
**Impact sur le site** : ⚠️ Nécessite de créer un compte MariaDB dédié
**Fichier à modifier** : `docker/docker-compose.prod.yml` + création compte MariaDB

Créer un compte MariaDB avec droits limités :
```sql
CREATE USER 'pma_user'@'%' IDENTIFIED BY 'MOT_DE_PASSE_FORT';
GRANT SELECT, INSERT, UPDATE, DELETE ON observations_nids.* TO 'pma_user'@'%';
FLUSH PRIVILEGES;
```

Puis dans `docker-compose.prod.yml`, remplacer :
```yaml
PMA_USER: root
PMA_PASSWORD: ${DB_ROOT_PASSWORD}
```
par :
```yaml
PMA_USER: pma_user
PMA_PASSWORD: ${PMA_PASSWORD}
```

Et ajouter `PMA_PASSWORD` dans `.env.prod`.

- [ ] Créer le compte MariaDB dédié via phpMyAdmin ou CLI
- [ ] Modifier `docker-compose.prod.yml`
- [ ] Ajouter `PMA_PASSWORD` dans `.env.prod.example` et `.env.prod`
- [ ] Tester phpMyAdmin avec le nouveau compte

---

### PRIORITÉ 6 — Limites mémoire/CPU Docker

**Risque si absent** : Un container peut monopoliser toutes les ressources (DoS)
**Impact sur le site** : ⚠️ Nécessite de connaître la consommation réelle d'abord
**Fichier à modifier** : `docker/docker-compose.prod.yml`

Avant de fixer des limites, surveiller la consommation réelle :
```bash
docker stats --no-stream
```

Puis ajouter par service (exemple) :
```yaml
web:
  deploy:
    resources:
      limits:
        cpus: '2.0'
        memory: 512M
      reservations:
        memory: 256M
```

- [ ] Observer `docker stats` en charge normale pendant 1 semaine
- [ ] Définir les limites en fonction des mesures
- [ ] Modifier `docker-compose.prod.yml`
- [ ] Tester que les containers ne sont pas OOM-killed

---

### PRIORITÉ 7 — Healthchecks Celery

**Risque si absent** : Workers Celery peuvent échouer silencieusement
**Impact sur le site** : Aucun risque de casser quoi que ce soit
**Fichier à modifier** : `docker/docker-compose.prod.yml`

```yaml
celery_worker:
  healthcheck:
    test: ["CMD", "celery", "-A", "observations_nids", "inspect", "ping", "-d", "celery@$$HOSTNAME"]
    interval: 30s
    timeout: 10s
    retries: 3
    start_period: 30s
```

- [ ] Ajouter healthcheck sur `celery_worker`
- [ ] Ajouter healthcheck sur `celery_beat`
- [ ] Tester sur pilote

---

### PRIORITÉ 8 — Logrotate pour les logs certbot

**Risque si absent** : `/var/log/certbot-renew.log` croît indéfiniment
**Impact sur le site** : Aucun

```bash
sudo nano /etc/logrotate.d/certbot-renew
```

Contenu :
```
/var/log/certbot-renew.log {
    monthly
    rotate 6
    compress
    missingok
    notifempty
}
```

- [ ] Créer `/etc/logrotate.d/certbot-renew` sur le serveur OVH
- [ ] Tester avec `sudo logrotate --debug /etc/logrotate.d/certbot-renew`

---

## Récapitulatif

| # | Modification | Priorité | Risque | Statut |
|---|-------------|----------|--------|--------|
| 1 | En-têtes HTTP (X-Frame, X-Content-Type...) | Critique | Aucun | ⬜ |
| 2 | HSTS (commencer avec max-age=3600) | Critique | Faible | ⬜ |
| 3 | Rate limiting Nginx | Important | Moyen | ⬜ |
| 4 | Vérification renouvellement SSL | Important | Aucun | ⬜ |
| 5 | phpMyAdmin utilisateur non-root | Important | Moyen | ⬜ |
| 6 | Limites mémoire/CPU Docker | Important | Moyen | ⬜ |
| 7 | Healthchecks Celery | Mineur | Aucun | ⬜ |
| 8 | Logrotate certbot | Mineur | Aucun | ⬜ |

---

*Créé : Mars 2026 — issu de l'audit de sécurité post-déploiement test OVH*
