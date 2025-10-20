# Sécurisation Raspberry Pi — Plan en 3 phases (checklist)

**Date :** 11 octobre 2025

Ce document te guide **pas à pas** pour durcir un Raspberry Pi hébergeant une application Django + MariaDB + Apache. Le but : actions immédiates, renforcement, et opérationnel/long terme.

---

## Mode d'emploi

1. Lis la section **Avant de commencer** et réalise la sauvegarde initiale.
2. Suis la **Phase 1** (obligatoire) en cochant les éléments au fur et à mesure.
3. Passe ensuite à la **Phase 2** puis à la **Phase 3**.
4. À chaque action : teste la vérification proposée avant de passer à la suivante.

> Astuce : ouvre ce fichier dans un éditeur Markdown ou viewer et coche les cases au fur et à mesure.

---

## Pré-requis

- Accès sudo sur le Raspberry Pi.
- Accès physique / console en secours si possible (utile en cas de perte d'accès SSH).
- Domaine DNS pointant vers le Pi (pour HTTPS via Let's Encrypt).
- Espace de stockage externe ou distant pour sauvegardes.

---

## Avant de commencer — sauvegarde **obligatoire**

**Sauvegarde DB (exemple pour une seule base)**

```bash
# remplace DB_NAME et DB_USER
sudo mysqldump -u DB_USER -p DB_NAME --single-transaction --routines --events > /root/DB_NAME-$(date +%F).sql
```

**Sauvegarde projet & médias**

```bash
# remplace /path/to/project et /path/to/media
sudo tar -czvf /root/backup_project_$(date +%F).tar.gz /path/to/project /path/to/media
```

**Vérification rapide**

- Vérifie que les fichiers `.sql` et `.tar.gz` sont lisibles et non corrompus (par ex. `tar -tzf` pour tester l'archive).
- Si possible, restaure un dump sur une VM ou autre machine de test pour vérifier.

---

# Phase 1 — Actions immédiates (faire **tout de suite**)

*Ordre recommandé : Mises à jour → Sauvegarde vérifiée → SSH & utilisateurs → MariaDB secure → Django settings → Pare-feu & Fail2Ban.*

### ✅ 1. Mise à jour du système

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install unattended-upgrades apt-listchanges -y
sudo dpkg-reconfigure --priority=low unattended-upgrades
```

**Vérifier** : `sudo apt list --upgradable` doit être vide après upgrade.

---

### ✅ 2. Sauvegarde (tu l'as déjà faite — vérifier à nouveau)

Si ce n'est pas fait, retourne à la section « Avant de commencer ».

---

### ✅ 3. Gestion des utilisateurs & SSH

1. **Créer un utilisateur admin (si **``** est encore utilisé)**

```bash
sudo adduser jmadmin
sudo usermod -aG sudo jmadmin
```

2. **Configurer l'accès par clé publique** (sur ta machine cliente) :

```bash
# côté client
ssh-keygen -t ed25519 -C "jm@tonton"
ssh-copy-id -i ~/.ssh/id_ed25519.pub jmadmin@ton.domaine.tld
```

3. **Sécuriser SSH** : édite `/etc/ssh/sshd_config` et place au minimum :

```
PermitRootLogin no
PasswordAuthentication no
# Optional: change Port 2222
# Port 2222
```

Redémarrer SSH :

```bash
sudo systemctl restart ssh
```

**Vérifier** : SSH depuis une autre machine avant de fermer la session actuelle.

---

### ✅ 4. `mysql_secure_installation` (MariaDB)

```bash
sudo mysql_secure_installation
```

Réponds OUI aux actions recommandées : supprimer comptes anonymes, désactiver accès root distant, supprimer DB test, recharger les privilèges.

**Vérifier** : dans MariaDB/MySQL :

```sql
SELECT user, host FROM mysql.user;
```

Aucun compte `root` ne devrait être autorisé sur `%`.

---

### ✅ 5. Désactiver `DEBUG` et protéger `settings`

- `DEBUG = False`
- `ALLOWED_HOSTS = ['ton.domaine.tld']`
- Stocke `SECRET_KEY` hors dépôt (variable d'environnement, fichier lu uniquement par l'app, ou service secret). Exemple minimal dans `settings.py` :

```python
import os
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY')
if not SECRET_KEY:
    raise Exception('DJANGO_SECRET_KEY not set')
```

**Vérifier** : redémarre Gunicorn/Apache et provoque une erreur contrôlée pour vérifier que l'application ne retourne pas la page DEBUG.

---

### ✅ 6. Pare-feu (UFW)

```bash
sudo apt install ufw -y
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
# si tu as gardé SSH sur le port 22
sudo ufw allow 22/tcp
sudo ufw enable
sudo ufw status verbose
```

**Vérifier** : `sudo ufw status` et tester l'accès web/SSH depuis l'extérieur.

---

### ✅ 7. Fail2Ban

```bash
sudo apt install fail2ban -y
```

Création d’un fichier local basique `/etc/fail2ban/jail.d/local.conf` :

```
[sshd]
enabled = true
port    = ssh
filter  = sshd
logpath = /var/log/auth.log
maxretry = 5

[apache-auth]
enabled = true
filter = apache-auth
logpath = /var/log/apache2/*error.log
maxretry = 6
```

Redémarrer : `sudo systemctl restart fail2ban`

**Vérifier** : `sudo fail2ban-client status` puis `sudo fail2ban-client status sshd`.

---

# Phase 2 — Renforcement (jours suivants)

### ✅ 1. HTTPS (Let's Encrypt / Certbot)

```bash
sudo apt install certbot python3-certbot-apache -y
sudo certbot --apache -d ton.domaine.tld
sudo certbot renew --dry-run
```

**Vérifier** : `sudo certbot certificates` et `curl -I https://ton.domaine.tld` pour vérifier le certificat et les en-têtes.

---

### ✅ 2. Hardening Apache

- Désactiver modules inutiles : `sudo a2dismod status cgi` etc.
- Protéger en-têtes (dans ta configuration Apache) :

```
ServerSignature Off
ServerTokens Prod
Header always set X-Frame-Options "DENY"
Header always set X-Content-Type-Options "nosniff"
Header always set Referrer-Policy "no-referrer-when-downgrade"
# HSTS : activer seulement si HTTPS stable
Header always set Strict-Transport-Security "max-age=63072000; includeSubDomains; preload"
```

- Limiter la taille des uploads si nécessaire : `LimitRequestBody 10485760` (10 MB) au niveau du VirtualHost.
- Envisager `mod_security` (WAF) et `mod_evasive`.

**Vérifier** : `apachectl configtest` puis redémarrer `sudo systemctl restart apache2`. Tester en-têtes : `curl -I https://ton.domaine.tld`.

---

### ✅ 3. Sécuriser MariaDB réseau & utilisateurs

- Forcer MariaDB à écouter seulement `127.0.0.1` : vérifie `bind-address` dans `/etc/mysql/mariadb.conf.d/50-server.cnf`.
- Créer un utilisateur Django minimal :

```sql
CREATE USER 'django'@'localhost' IDENTIFIED BY 'mot_de_passe_fort';
GRANT SELECT, INSERT, UPDATE, DELETE, CREATE, INDEX ON nom_bd.* TO 'django'@'localhost';
FLUSH PRIVILEGES;
```

**Vérifier** : connexion depuis la machine locale uniquement.

---

### ✅ 4. Logs & rotation

- Active `logrotate` pour Apache, MariaDB et logs Django.
- Configure la journalisation Django (niveau INFO/ERROR en prod) et enregistre dans `/var/log/observations`.

**Vérifier** : `sudo logrotate --debug /etc/logrotate.conf` pour tests.

---

### ✅ 5. Sécurité des dépendances Python

- Utilise un `venv` et un `requirements.txt` figé (versions exactes).
- Vérifie les vulnérabilités : `pip install pip-audit` puis `pip-audit`.

**Vérifier** : corriger ou isoler dépendances vulnérables.

---

# Phase 3 — Sécurité avancée & opérations (systématique / régulier)

### ✅ 1. Surveillance & détection

- Installer AIDE (ou équivalent) :

```bash
sudo apt install aide -y
sudo aideinit
# déplacer db créé si demandé
sudo mv /var/lib/aide/aide.db.new /var/lib/aide/aide.db
sudo aide --check
```

- Installer un outil de monitoring léger (ex: Netdata, ou exporter + Prometheus + Grafana si tu veux dashboards).

**Vérifier** : exécuter `aide --check` régulièrement via cron et vérifier les alertes.

---

### ✅ 2. Backups automatisés & chiffrés

Exemple de script simple (sauvegarde DB + médias) et cron :

```bash
#!/bin/bash
OUT=/root/backups
mkdir -p $OUT
mysqldump -u DB_USER -p'MDPP' DB_NAME > $OUT/db-$(date +%F).sql
tar -czf $OUT/media-$(date +%F).tar.gz /path/to/media
# Optionnel : chiffrer avec gpg et envoyer hors-site
```

Puis `crontab -e` (exemple journalier 3h) :

```
0 3 * * * /root/backups/script_sauvegarde.sh
```

**Vérifier** : restore d’un backup sur un serveur de test.

---

### ✅ 3. Accès admin via VPN

- Préférer WireGuard pour l’accès admin au réseau interne plutôt que laisser SSH ouvert sur Internet.
- Installer et configurer WireGuard, puis n’autoriser SSH que depuis l’IP VPN.

**Vérifier** : tentative d’accès SSH depuis l’extérieur sans VPN doit échouer.

---

### ✅ 4. Tests de vulnérabilité & revue

- Nmap en local pour voir ports ouverts : `sudo nmap -sS -Pn localhost`.
- Scanner web (Nikto, ou service en ligne). Corriger ce qui est trouvé.

**Vérifier** : corriger les vulnérabilités les plus critiques en priorité.

---

## Checklist de progression (coche au fur et à mesure)

### Phase 1 — immédiat

-

### Phase 2 — renforcement

-

### Phase 3 — opérations

-

---

## Annexes — extraits / templates rapides

### Extrait `jail.d/local.conf` pour Fail2Ban

```
[sshd]
enabled = true
port    = ssh
filter  = sshd
logpath = /var/log/auth.log
maxretry = 5

[apache-auth]
enabled = true
filter = apache-auth
logpath = /var/log/apache2/*error.log
maxretry = 6
```

### Exemple de règle Apache (VirtualHost) pour headers & limites

```
<VirtualHost *:443>
    ServerName ton.domaine.tld
    DocumentRoot /path/to/project

    # Limite d'upload
    <Directory /path/to/project>
        LimitRequestBody 10485760
    </Directory>

    # En-têtes de sécurité
    Header always set X-Frame-Options "DENY"
    Header always set X-Content-Type-Options "nosniff"
    Header always set Referrer-Policy "no-referrer-when-downgrade"
    Header always set Strict-Transport-Security "max-age=63072000; includeSubDomains; preload"

    # Autres directives (WSGI / proxy selon ta config)
</VirtualHost>
```

### Exemple de crontab (backup journalier)

```
0 3 * * * /root/backups/script_sauvegarde.sh >> /var/log/backup.log 2>&1
```

---

## Notes & bonnes pratiques finales

- **Teste avant** : chaque changement pouvant couper l’accès doit d’abord être testé (SSH par clé configuré, vérifié depuis une autre session).
- **Principe du moindre privilège** : utilisateurs, services et fichiers doivent avoir uniquement les droits nécessaires.
- **Documentation** : note les mots de passe temporaires, chemins, et p
