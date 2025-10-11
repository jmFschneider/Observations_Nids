# Checklist Pull Request / Commit

Cette checklist permet de vérifier que toutes les fonctionnalités critiques fonctionnent correctement avant de merger sur `develop` ou `production`.

---

## 📋 Avant tout commit important

### Vérifications de base
- [ ] Le code compile sans erreur : `python manage.py check`
- [ ] Les migrations sont à jour : `python manage.py makemigrations --check`
- [ ] Les tests unitaires passent : `pytest`
- [ ] Ruff ne signale pas d'erreurs critiques : `ruff check .`
- [ ] Mypy ne signale pas d'erreurs de typage : `mypy .`

### Collecte des fichiers statiques
- [ ] Les fichiers statiques sont collectés : `python manage.py collectstatic --noinput`
- [ ] La version du cache JS/CSS est incrémentée si nécessaire (`?v=X.X`)

---

## 🧪 Tests fonctionnels critiques

### Module d'authentification
- [ ] Connexion utilisateur fonctionne (`/auth/login/`)
- [ ] Déconnexion fonctionne
- [ ] Permissions par rôle (observateur, correcteur, validateur, admin)

### Module observations - Liste et consultation
- [ ] Liste des observations s'affiche (`/observations/liste/`)
- [ ] Pagination fonctionne
- [ ] Détail d'une fiche s'affiche (`/observations/fiche/<id>/`)
- [ ] Historique des modifications visible

### Module observations - Saisie et modification
- [ ] **Nouvelle observation** (`/observations/`) :
  - [ ] Le formulaire s'affiche correctement
  - [ ] Tous les champs sont présents
  - [ ] La soumission enregistre correctement
  - [ ] Les formsets (observations multiples) fonctionnent
  - [ ] Les validations côté serveur fonctionnent

- [ ] **Modification d'observation** (`/observations/modifier/<id>/`) :
  - [ ] Le formulaire se charge avec les données existantes
  - [ ] Les modifications sont sauvegardées
  - [ ] L'historique est mis à jour

### Autocomplétion et auto-remplissage

#### Autocomplétion espèces
- [ ] Taper des lettres dans le champ "Espèce" affiche une liste déroulante
- [ ] Les espèces sont filtrées en temps réel (délai 800ms)
- [ ] Cliquer sur une espèce la sélectionne
- [ ] Navigation au clavier (↑↓ Enter Escape) fonctionne
- [ ] La recherche est insensible à la casse

#### Autocomplétion communes ⭐ CRITIQUE
- [ ] **Nouvelle saisie** :
  - [ ] Taper 2+ lettres dans "Commune" affiche une liste
  - [ ] Les communes sont filtrées par nom (pas par GPS)
  - [ ] Cliquer sur une commune remplit automatiquement :
    - [ ] Nom de la commune
    - [ ] Département (si vide ou = "00")
    - [ ] Latitude (si vide ou = "0.0")
    - [ ] Longitude (si vide ou = "0.0")
    - [ ] Altitude (popup confirmation si vide ou = "0")
  - [ ] La distance est affichée si des GPS sont disponibles

- [ ] **Modification d'observation** :
  - [ ] L'autocomplétion fonctionne
  - [ ] Les coordonnées GPS **existantes** (≠ 0) sont **conservées**
  - [ ] Seules les valeurs vides/par défaut sont remplies

- [ ] **Navigation clavier** :
  - [ ] ↑↓ pour naviguer
  - [ ] Enter pour sélectionner
  - [ ] Escape pour fermer

### Module transcription (OCR)
- [ ] Interface de sélection de répertoire (`/transcription/demarrer/`)
- [ ] Lancement du traitement (`/transcription/traiter-images/`)
- [ ] Progression en temps réel (`/transcription/verifier-progression/`)
- [ ] Affichage des résultats (`/transcription/resultats/`)
- [ ] Celery worker fonctionne (si activé)

### Module taxonomie
- [ ] Commande `charger_lof` fonctionne
- [ ] Commande `charger_taxref` fonctionne (alternative)
- [ ] Les espèces sont chargées en base
- [ ] Liens vers oiseaux.net présents (si récupérés)

### Module géocodage
- [ ] Commande `charger_communes_france` fonctionne
- [ ] ~35 000 communes chargées
- [ ] Recherche dans la base locale rapide
- [ ] Fallback Nominatim fonctionne (si base locale échoue)
- [ ] API `/geo/rechercher-communes/` retourne des résultats

### Module review (révision)
- [ ] Workflow de correction fonctionne
- [ ] États : nouveau → en_cours → corrigé → validé
- [ ] Soumission pour validation (`/observations/soumettre/<id>/`)

### Module audit
- [ ] Historique des modifications enregistré
- [ ] Traçabilité au niveau du champ
- [ ] Consultation de l'historique (`/observations/historique/<id>/`)

---

## 🎨 Interface utilisateur

### Responsive design
- [ ] Desktop (≥1200px) : affichage correct
- [ ] Tablette (768-1199px) : affichage correct
- [ ] Mobile (≤767px) : affichage correct

### Composants Bootstrap
- [ ] Navbar : liens fonctionnels, dropdown actif
- [ ] Cards : affichage correct
- [ ] Forms : styling cohérent
- [ ] Buttons : hover et active states
- [ ] Alerts : affichage correct

### JavaScript
- [ ] Pas d'erreurs dans la console développeur
- [ ] Les événements click fonctionnent
- [ ] Les animations sont fluides
- [ ] AJAX : gestion des erreurs réseau

---

## 🔒 Sécurité

### Authentification
- [ ] Pages protégées requièrent login
- [ ] Tokens CSRF présents dans les formulaires
- [ ] Sessions expirent après inactivité (défaut: 1h)

### Permissions
- [ ] Observateurs : peuvent créer/modifier leurs fiches
- [ ] Correcteurs : peuvent corriger les fiches
- [ ] Validateurs : peuvent valider les fiches
- [ ] Admins : accès complet

### Données sensibles
- [ ] Pas de secrets dans le code (utiliser .env)
- [ ] Pas de credentials en clair dans Git
- [ ] .env.example à jour

---

## 🚀 Performance

### Requêtes base de données
- [ ] Pas de N+1 queries (utiliser `select_related` / `prefetch_related`)
- [ ] Index sur les champs fréquemment filtrés
- [ ] Pagination sur les listes longues

### Fichiers statiques
- [ ] Minification CSS/JS (si activée)
- [ ] Cache busting avec versions (`?v=X.X`)
- [ ] Images optimisées

### Celery (si utilisé)
- [ ] Worker actif : `celery -A observations_nids worker`
- [ ] Redis/RabbitMQ accessible
- [ ] Tâches s'exécutent sans erreur

---

## 📝 Documentation

### Code
- [ ] Docstrings sur les fonctions complexes
- [ ] Commentaires explicatifs si logique non évidente
- [ ] Type hints (si mypy activé)

### Git
- [ ] Message de commit descriptif (format conventionnel : `feat:`, `fix:`, `docs:`, etc.)
- [ ] Référence aux issues/tickets si applicable

### Documentation projet
- [ ] README.md à jour
- [ ] FEATURES.md mis à jour avec nouvelles fonctionnalités
- [ ] Documentation technique dans `/Claude` ou `/docs`

---

## ⚠️ Avant merge sur `production`

### Tests approfondis
- [ ] **Test complet workflow** : création → correction → validation
- [ ] **Test avec données réelles** (pas seulement données de test)
- [ ] **Test sur plusieurs navigateurs** :
  - [ ] Chrome/Edge (Chromium)
  - [ ] Firefox
  - [ ] Safari (si possible)

### Vérifications finales
- [ ] Backup base de données effectué
- [ ] Migration plan préparé (si migrations DB)
- [ ] Rollback plan préparé
- [ ] Monitoring actif (logs, erreurs)

### Communication
- [ ] Équipe informée du déploiement
- [ ] Documentation de déploiement à jour
- [ ] Notes de version rédigées

---

## 🐛 Checklist de debugging

Si un problème est détecté :

### Console navigateur (F12)
- [ ] Vérifier les erreurs JavaScript
- [ ] Vérifier les requêtes AJAX (onglet Network)
- [ ] Vérifier que les fichiers statiques se chargent (status 200)

### Logs Django
- [ ] Vérifier les logs serveur : `tail -f logs/django.log`
- [ ] Vérifier les erreurs 404/500
- [ ] Vérifier les warnings

### Base de données
- [ ] Vérifier l'intégrité des données
- [ ] Vérifier les contraintes FK
- [ ] Vérifier les index

---

## 📊 Métriques de qualité

### Couverture de code
- [ ] Tests unitaires : ≥ 70%
- [ ] Tests d'intégration : fonctionnalités critiques couvertes

### Code quality
- [ ] Ruff : 0 erreur critique
- [ ] Mypy : erreurs de type résolues
- [ ] Complexité cyclomatique : < 10 par fonction

### Performance
- [ ] Temps de réponse API : < 200ms (moyenne)
- [ ] Temps de chargement page : < 2s
- [ ] Requêtes DB par page : < 20

---

## ✅ Validation finale

**Avant de cocher cette case, TOUTES les cases critiques ⭐ ci-dessus doivent être cochées.**

- [ ] **JE CONFIRME** avoir vérifié toutes les fonctionnalités critiques
- [ ] **JE CONFIRME** que l'autocomplétion communes fonctionne (nouvelle saisie + modification)
- [ ] **JE CONFIRME** que l'auto-remplissage respecte les GPS existants
- [ ] **JE CONFIRME** qu'aucune régression n'a été détectée

**Nom :** _______________
**Date :** _______________
**Branche :** _______________
**Commit :** _______________

---

*Cette checklist est un document vivant. N'hésitez pas à l'enrichir au fur et à mesure des besoins.*

*Dernière mise à jour : 2025-10-10*
