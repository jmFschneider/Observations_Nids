# Guide de Mise à Jour - Serveur OCR (ex-Pilote)

> **Contexte** : Guide complet pour mettre à jour le serveur OCR (anciennement Pilote) - mises à jour standard et migrations majeures

---

## 🔄 Script de Synchronisation Automatique

Le script `scripts/sync_ocr_to_dev.sh` (anciennement `sync_pilote_to_dev.sh`) permet de **synchroniser automatiquement** la base de données OCR vers l'environnement de développement Docker. Il vérifie la concordance des schémas via les migrations, effectue un backup de sécurité, et propose deux modes : migration complète (avec utilisateurs) ou sélective (sans utilisateurs, recommandé pour dev). Ce script est particulièrement utile pour tester les changements en local avant de les déployer en production. Il inclut également des vérifications de sécurité et des possibilités de rollback en cas de problème.

---

## 📋 Prérequis Généraux

- Accès SSH au serveur Ubuntu
- Droits sudo/docker
- Base de données existante
- Docker et Docker Compose installés

---

## 🚀 Mise à Jour Standard (Code Python, CSS, Templates)

> **Quand l'utiliser** : Modifications de code Python, ajout/modification de CSS, templates, fichiers statiques **SANS changement de schéma de base de données** (pas de migration)

### 1. Backup Préventif (Recommandé)

```bash
cd /opt/observations_nids_pilote/docker

# Backup rapide de la base (optionnel mais recommandé)
docker compose exec db mysqldump -u root -p observations_nids > backup_quick_$(date +%Y%m%d_%H%M%S).sql
```

---

### 2. Récupération du Code

```bash
# Stash les modifications locales si nécessaire
git stash

# Récupérer les derniers changements
git fetch origin
git pull origin main

# Vérifier la branche actuelle
git status
```

---

### 3. Rebuild et Redémarrage (Méthode Simple)

**Si modifications Python uniquement :**

```bash
# Rebuild et redémarrer les services
docker compose up -d --build

# Vérifier les logs
docker compose logs web --tail=50
```

**Si modifications de fichiers statiques (CSS, JS) :**

```bash
# Recollecte des fichiers statiques
docker compose exec web python manage.py collectstatic --no-input

# Redémarrer pour charger les nouveaux statiques
docker compose restart web
```

---

### 4. Vérifications Post-Déploiement

```bash
# Vérifier l'état des services
docker compose ps

# Tester l'accès au site
curl -I http://localhost:8000/

# Vider le cache Redis (si problèmes de cache)
docker compose exec redis redis-cli FLUSHALL
```

**Dans le navigateur** :
- Vider le cache : `Ctrl+Shift+R` ou `Cmd+Shift+R`
- Vérifier que les changements sont visibles
- Tester les fonctionnalités modifiées

---

### 5. Checklist Rapide

- [ ] Code récupéré depuis GitHub
- [ ] Services rebuildés et redémarrés
- [ ] Fichiers statiques collectés (si modif CSS/JS)
- [ ] Services démarrés sans erreur
- [ ] Site accessible et fonctionnel
- [ ] Cache navigateur vidé
- [ ] Changements visibles et testés

---

## 🔧 Mise à Jour Majeure (Avec Migrations de Base de Données)

> **Quand l'utiliser** : Modifications nécessitant des **migrations de base de données** (ajout/modification de tables, colonnes, relations) ou changements structurels majeurs

### 1. Backup Complet

```bash
cd /opt/observations_nids_pilote/docker

# Arrêter les services
docker compose down

# Backup de la base de données
docker compose up -d db
docker compose exec db mysqldump -u root -p observations_nids > backup_$(date +%Y%m%d_%H%M%S).sql

# Backup des media
tar -czf backup_media_$(date +%Y%m%d_%H%M%S).tar.gz media/

# Arrêter la base
docker compose down
```

---

### 2. Récupération du Code

```bash
# Stash les modifications locales si nécessaire
git stash

# Récupérer les derniers changements
git fetch origin
git pull origin main

# Vérifier que l'app ocr est présente
ls -la ocr/
```

---

### 3. Rebuild des Images Docker

```bash
# Rebuild avec les nouveaux requirements
docker compose build --no-cache
```

---

### 4. Application des Migrations

```bash
# Démarrer UNIQUEMENT db et redis
docker compose up -d db redis
sleep 10

# Appliquer les migrations
docker compose exec web python manage.py migrate

# Vérifier les migrations appliquées
docker compose exec web python manage.py showmigrations
```

#### 📌 Cas Spécial : Migration pilot → ocr (Première Migration Uniquement)

> **Note** : Cette section ne s'applique que lors de la **première migration** de `pilot` vers `ocr`. Pour les mises à jour normales, utiliser la procédure ci-dessus.

**Si vous migrez pour la première fois de pilot → ocr :**

```bash
# Entrer dans le conteneur SANS script d'entrée
docker compose run --rm --entrypoint="" web bash

# Dans le conteneur :
# Fake les 3 premières migrations (tables existent déjà sous pilot_*)
python manage.py migrate ocr 0001_initial --fake
python manage.py migrate ocr 0002_alter_transcriptionocr_fiche --fake
python manage.py migrate ocr 0003_update_gemini_models --fake

# Appliquer les migrations de renommage (RÉEL)
python manage.py migrate ocr 0004_rename_pilot_tables_to_ocr
python manage.py migrate ocr 0005_update_related_name

# Appliquer toutes les autres migrations
python manage.py migrate

# Sortir du conteneur
exit
```

---

### 5. Collecte des Fichiers Statiques

```bash
# Recollecte forcée des statiques
docker compose run --rm web python manage.py collectstatic --clear --no-input
```

---

### 6. Démarrage des Services

```bash
# Démarrer tous les services
docker compose up -d

# Vérifier les logs
docker compose logs web --tail=30

# Vérifier l'état des services
docker compose ps
```

---

### 7. Vérifications Post-Déploiement

```bash
# Vérifier les migrations appliquées
docker compose exec web python manage.py showmigrations

# Vérifier les tables en base
docker compose exec db mysql -u root -p observations_nids -e "SHOW TABLES;"

# Tester l'accès au site
curl -I http://localhost:8000/

# Vérifier les logs d'erreur
docker compose logs web --tail=100 | grep -i error
```

**Dans le navigateur** :
- Vider le cache navigateur : `Ctrl+Shift+R` ou `Cmd+Shift+R`
- Vérifier que le site fonctionne
- Tester les fonctionnalités modifiées
- Vérifier l'interface d'administration Django

#### 📌 Vérifications Spécifiques : Migration pilot → ocr

**Si vous avez effectué la migration pilot → ocr :**

```bash
# Vérifier que les tables ocr_* existent
docker compose exec db mysql -u root -p observations_nids -e "SHOW TABLES LIKE 'ocr_%';"

# Vérifier que les anciennes tables pilot_* n'existent plus
docker compose exec db mysql -u root -p observations_nids -e "SHOW TABLES LIKE 'pilot_%';"
```

---

## ⚠️ En Cas de Problème

### Rollback Complet

```bash
# Arrêter tout
docker compose down

# Restaurer la base
docker compose up -d db
docker compose exec -T db mysql -u root -p observations_nids < backup_YYYYMMDD_HHMMSS.sql

# Revenir au commit précédent
git reset --hard HEAD~1

# Redémarrer
docker compose up -d
```

### Logs de Débogage

```bash
# Voir les logs détaillés
docker compose logs -f web

# Voir les logs d'erreur uniquement
docker compose logs web | grep -i error

# Entrer dans le conteneur pour diagnostiquer
docker compose exec web bash

# Tester les commandes Django manuellement
docker compose exec web python manage.py shell
```

---

## 📝 Checklists de Validation

### Checklist Mise à Jour Standard

- [ ] Backup préventif effectué (recommandé)
- [ ] Code récupéré depuis GitHub
- [ ] Services rebuildés et redémarrés
- [ ] Fichiers statiques collectés (si modif CSS/JS)
- [ ] Services démarrés sans erreur
- [ ] Site accessible et fonctionnel
- [ ] Cache navigateur vidé
- [ ] Changements visibles et testés

### Checklist Mise à Jour Majeure

- [ ] Backup complet effectué (DB + media)
- [ ] Code récupéré depuis GitHub
- [ ] Images Docker rebuildées
- [ ] Migrations appliquées correctement
- [ ] Fichiers statiques collectés
- [ ] Services démarrés sans erreur
- [ ] Migrations vérifiées (`showmigrations`)
- [ ] Tables en base vérifiées
- [ ] Site accessible et fonctionnel
- [ ] Cache navigateur vidé
- [ ] Tests fonctionnels effectués

---

## 🎯 Points Clés à Retenir

### Pour Toutes les Mises à Jour

1. **Toujours faire un backup** avant toute intervention
2. **Vérifier les logs** après chaque redémarrage
3. **Recollect les statiques** après mise à jour du code frontend
4. **Vider tous les caches** (Django, Redis, navigateur)
5. **Tester les fonctionnalités** affectées par les changements

### Pour les Migrations de Base de Données

1. **Ne jamais fake une migration** sauf cas spécial documenté
2. **Toujours vérifier** les migrations appliquées avec `showmigrations`
3. **Tester en local/dev** avant de déployer en production
4. **Garder le backup** jusqu'à validation complète en production

---

## 📞 Support

En cas de problème non résolu, vérifier :
- Les logs Docker : `docker compose logs web`
- La console navigateur (F12)
- Les permissions des fichiers statiques
- La configuration des variables d'environnement
