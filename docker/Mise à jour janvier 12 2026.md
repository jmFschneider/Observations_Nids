  Tu as raison, ce n'est pas juste un rebuild. Il y a des migrations personnalisées pour le renommage
  pilot → ocr qui nécessitent un processus spécifique.

---
  🔧 Processus Complet de Mise à Jour

  1️⃣ Backup Complet AVANT Toute Modification

  # Arrêter les services
  cd ~/Observations_Nids  # ou ton répertoire projet
  docker compose down

  # Backup de la base de données
  docker compose run --rm web python manage.py dumpdata > backup_$(date +%Y%m%d_%H%M%S).json

  # OU backup MySQL direct (préférable)
  docker compose exec db mysqldump -u root -p observations_nids > backup_db_$(date +%Y%m%d_%H%M%S).sql

  # Backup des fichiers media
  tar -czf backup_media_$(date +%Y%m%d_%H%M%S).tar.gz media/

---
  2️⃣ Récupérer les Derniers Changements GitHub

  # Vérifier l'état actuel
  git status
  git branch

  # Stash les changements locaux si nécessaire
  git stash

  # Récupérer les changements
  git fetch origin
  git pull origin main

  # Vérifier les fichiers récupérés
  ls -la ocr/  # La nouvelle app doit être là
  ls -la pilot/  # L'ancienne peut encore être là

---
  3️⃣ Vérifier les Migrations Disponibles

  # Lister les migrations de l'app ocr
  ls -la ocr/migrations/

  # Tu dois voir :
  # 0001_initial.py
  # 0002_alter_transcriptionocr_fiche.py
  # 0003_update_gemini_models.py
  # 0004_rename_pilot_tables_to_ocr.py  ← CRITIQUE
  # 0005_update_related_name.py          ← CRITIQUE

---
  4️⃣ Mettre à Jour les Fichiers Docker

  # Rebuild les images avec les nouveaux requirements
  docker compose build --no-cache

---
  5️⃣ Appliquer les Migrations dans l'Ordre

  # Démarrer UNIQUEMENT la base de données
  docker compose up -d db

  # Attendre que la DB soit prête (5-10 secondes)
  sleep 10

  # Vérifier l'état des migrations AVANT
  docker compose run --rm web python manage.py showmigrations

  # Appliquer les migrations dans l'ordre CRITIQUE
  docker compose run --rm web python manage.py migrate ocr 0001_initial
  docker compose run --rm web python manage.py migrate ocr 0002_alter_transcriptionocr_fiche
  docker compose run --rm web python manage.py migrate ocr 0003_update_gemini_models

  # CRITIQUE : Migration de renommage des tables pilot → ocr
  docker compose run --rm web python manage.py migrate ocr 0004_rename_pilot_tables_to_ocr

  # CRITIQUE : Mise à jour des related_name
  docker compose run --rm web python manage.py migrate ocr 0005_update_related_name

  # Appliquer toutes les autres migrations
  docker compose run --rm web python manage.py migrate

---
  6️⃣ Mettre à Jour les Dépendances Python

  # Si tu as ajouté de nouveaux packages
  docker compose run --rm web pip install -r requirements-prod.txt

  # OU rebuild complet (déjà fait à l'étape 4)

---
  7️⃣ Collecter les Fichiers Statiques

  docker compose run --rm web python manage.py collectstatic --no-input

---
  8️⃣ Démarrer Tous les Services

  # Démarrer tous les services
  docker compose up -d

  # Vérifier les logs
  docker compose logs -f --tail=100

  # Vérifier que tout fonctionne
  docker compose ps

---
  9️⃣ Vérifications Post-Déploiement

  # Vérifier l'état des migrations
  docker compose exec web python manage.py showmigrations

  # Vérifier que l'app ocr est reconnue
  docker compose exec web python manage.py shell
  >>> from ocr.models import TranscriptionOCR
  >>> TranscriptionOCR.objects.count()
  >>> exit()

  # Tester l'accès au site
  curl http://localhost:8000/

---
  ⚠️ Points d'Attention Critiques

  Migration 0004 : Renommage des Tables

  Cette migration fait :
  # Renomme pilot_transcriptionocr → ocr_transcriptionocr
  operations = [
      migrations.RenameModel(
          old_name='TranscriptionOCR',
          new_name='TranscriptionOCR',
      ),
  ]

  Si cette migration échoue :
  # Vérifier que les tables pilot_ existent
  docker compose exec db mysql -u root -p observations_nids -e "SHOW TABLES LIKE 'pilot_%';"

  # Si les tables n'existent pas, la migration est déjà passée ou l'app n'a jamais été utilisée
  # Tu peux alors faire un fake :
  docker compose run --rm web python manage.py migrate ocr 0004_rename_pilot_tables_to_ocr --fake

---
  🚨 En Cas de Problème

  Rollback Complet

  # Arrêter tout
  docker compose down

  # Restaurer la base de données
  docker compose up -d db
  docker compose exec -T db mysql -u root -p observations_nids < backup_db_YYYYMMDD_HHMMSS.sql

  # Revenir au commit précédent
  git reset --hard HEAD~1  # ou le commit avant la mise à jour

  # Redémarrer
  docker compose up -d

---
  📝 Checklist Finale

  - Backup fait (DB + media)
  - Code récupéré depuis GitHub
  - Images Docker rebuiltées
  - Migrations appliquées dans l'ordre
  - showmigrations ne montre aucune migration en attente
  - Logs Docker sans erreurs
  - Site accessible
  - Fonctionnalités OCR testées

---
  💡 Note Importante sur pilot vs ocr

  Si ton serveur Ubuntu n'avait jamais l'app pilot en production, les migrations de renommage vont
  être marquées comme "fake" automatiquement car Django détectera qu'il n'y a rien à renommer.

  Pour vérifier :
  docker compose exec db mysql -u root -p observations_nids -e "SHOW TABLES LIKE 'pilot_%';"

  - Si aucune table : Les migrations 0004 et 0005 seront skip/fake automatiquement ✅
  - Si tables présentes : Les migrations vont les renommer correctement ✅

---
  Commence par l'étape 1 (backup) puis donne-moi le retour de la commande SHOW TABLES pour que je
  t'aide à adapter la suite ! 🚀