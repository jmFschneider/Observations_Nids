# TODO - Nettoyage et synchronisation

Ce document liste les tâches de nettoyage à effectuer après la phase de test utilisateurs.

---

## ⚠️ URGENT : Synchronisation serveur → local

### Problème

Des modifications ont été faites **directement sur le serveur Raspberry Pi** au lieu de passer par le workflow git normal :

```
Workflow normal :
Local (dev) → commit → push → Raspberry (pull)

Ce qui s'est passé :
Raspberry (modifications directes) → ??? → Local
```

### Fichiers concernés

1. **`observations_nids/settings_local.py`** sur le Raspberry Pi
   - Modification de `LOG_DIR` pour corriger Celery
   - **Contenu modifié** : `LOG_DIR = "/var/www/html/Observations_Nids/logs"` (au lieu de `/var/log/observations_nids`)

2. **`.env`** sur le Raspberry Pi (potentiellement)
   - Ajout de `DJANGO_LOG_DIR=/var/www/html/Observations_Nids/logs`

3. **Autres modifications possibles**
   - À vérifier avec `git status` sur le Raspberry

### Actions à faire

#### Étape 1 : Identifier les différences

Sur le Raspberry Pi :
```bash
cd /var/www/html/Observations_Nids

# Voir les fichiers modifiés
git status

# Voir les différences
git diff

# Voir les fichiers non trackés
git ls-files --others --exclude-standard
```

#### Étape 2 : Sauvegarder les modifications

```bash
# Créer une branche temporaire avec les modifs serveur
git checkout -b hotfix/raspberry-config
git add observations_nids/settings_local.py
git commit -m "fix: Configuration LOG_DIR pour Raspberry Pi en production"
```

#### Étape 3 : Synchroniser avec le dépôt

**Option A : Push depuis le Raspberry (recommandé)**
```bash
# Push la branche hotfix
git push origin hotfix/raspberry-config

# Sur la machine locale :
git fetch
git checkout hotfix/raspberry-config
git checkout main
git merge hotfix/raspberry-config
git push
```

**Option B : Exporter un patch**
```bash
# Sur Raspberry
git diff > ~/raspberry-changes.patch

# Transférer le fichier vers local (scp, email, etc.)
# Sur local :
git apply raspberry-changes.patch
git add .
git commit -m "fix: Appliquer les corrections de production Raspberry"
```

#### Étape 4 : Nettoyer le Raspberry

```bash
# Retour sur main et mise à jour
git checkout main
git pull origin main

# Supprimer la branche hotfix (si Option A)
git branch -d hotfix/raspberry-config
```

---

## 🧹 Nettoyage général du projet

### Fichiers de configuration à vérifier

- [ ] **`settings_local.py`** : Documenter son rôle et sa priorité sur `.env`
- [ ] **`.env`** : Vérifier cohérence local vs production
- [ ] **`deployment/`** : S'assurer que tous les fichiers sont committes

### Documentation à compléter

- [ ] Ajouter section dans README sur le déploiement Raspberry Pi
- [ ] Documenter les variables d'environnement requises


### Tests à ajouter (optionnel)

- [ ] Test de la configuration logging
- [ ] Test de la tâche Celery de transcription
- [ ] Test de l'upload et processing d'images

---

## 📝 Bonnes pratiques à établir

### Workflow git strict

```
1. Développement local UNIQUEMENT
2. Tests locaux
3. Commit + push
4. Pull sur le serveur
5. Restart des services si nécessaire
```

### Exceptions acceptables (modifications serveur directes)

- **Configuration d'urgence** (comme aujourd'hui avec LOG_DIR)
- **Debugging en production**
- **MAIS** : Toujours synchroniser vers git après

### Procédure en cas de hotfix serveur

1. Noter immédiatement les modifications dans un fichier texte
2. Créer une issue GitHub pour ne pas oublier
3. Synchroniser vers git dès que possible (dans la journée)
4. Documenter dans CHANGELOG.md

---

## 🔍 Audit à faire

### Comparer les environnements

```bash
# Sur Raspberry
tree -L 2 /var/www/html/Observations_Nids > raspberry-tree.txt
cat observations_nids/settings_local.py > raspberry-settings.txt
cat .env > raspberry-env.txt

# Sur local
tree -L 2 . > local-tree.txt
cat observations_nids/settings_local.py > local-settings.txt  # Si existe
cat .env > local-env.txt

# Comparer
diff local-settings.txt raspberry-settings.txt
diff local-env.txt raspberry-env.txt
```

### Vérifier les dépendances

```bash
# Vérifier que requirements.txt est à jour
pip freeze > requirements-frozen.txt
diff requirements.txt requirements-frozen.txt
```

---

## ⏰ Timeline suggéré

### Maintenant (aujourd'hui)
- ✅ Ce fichier TODO créé
- ✅ Application fonctionnelle en production
- ⏸️ **Pause** : Recueillir retours utilisateurs

### Semaine prochaine
- [ ] Audit des différences local/serveur
- [ ] Synchronisation git propre
- [ ] Documentation workflow de déploiement

### Plus tard
- [ ] Mise en place CI/CD (GitHub Actions) ?
- [ ] Scripts de déploiement automatisés
- [ ] Tests automatisés

---

## 🚨 Risques à éviter

### ❌ Ne JAMAIS faire

1. **Développer directement sur le serveur de production**
   - Risque de perte de code
   - Pas de versioning
   - Difficile à déboguer

2. **Ignorer les divergences git**
   - Conflits futurs garantis
   - Confusion sur la version "vraie"

3. **Commiter depuis le serveur sans pull avant**
   - Conflits de merge complexes

### ✅ Toujours faire

1. **Développer en local**
2. **Tester en local**
3. **Commit + push**
4. **Pull sur serveur**
5. **Documenter les changements**

---

## 📚 Ressources

- [Guide de déploiement Production](../deployment/production.md) (inclut configuration Celery)
- [Redis et Celery en production](../installation/redis-celery-production.md)
- [Optimisations futures](./OPTIMISATIONS_FUTURES.md)
- [Changelog](../CHANGELOG.md)

---

**Date de création** : 16 octobre 2025
**Statut** : En attente - Phase de recueil de retours utilisateurs
**Priorité** : Moyenne (urgent après phase de test)
