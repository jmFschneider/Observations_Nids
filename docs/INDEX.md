# Index de la Documentation - Observations Nids

**Date de dernière mise à jour :** 19 octobre 2025
**Branche actuelle :** `feature/reinitialisation_mdp`

---

## 📚 Table des Matières

1. [Vue d'ensemble du projet](#vue-densemble-du-projet)
2. [État actuel de la branche](#état-actuel-de-la-branche)
3. [Guide de navigation de la documentation](#guide-de-navigation-de-la-documentation)
4. [État des tests](#état-des-tests)
5. [Fonctionnalités implémentées](#fonctionnalités-implémentées)
6. [Prochaines étapes](#prochaines-étapes)

---

## Vue d'ensemble du projet

**Projet :** Application Django de gestion d'observations de nids d'oiseaux
**Version Django :** 5.2.7
**Python :** 3.12.5
**Base de données :** MariaDB (production) / SQLite (tests)
**Serveur :** Apache + mod_wsgi (Raspberry Pi)
**Technologies :** Django, Celery, Redis, Leaflet (cartographie)

### Architecture

```
observations_nids/
├── accounts/          # Gestion utilisateurs, authentification
├── observations/      # Fiches d'observation, saisie, validation
├── geo/              # Géolocalisation, communes, cartographie
├── audit/            # Logs et traçabilité
├── core/             # Fonctionnalités communes
├── docs/             # Documentation (vous êtes ici)
└── tests/            # Tests racine
```

---

## État actuel de la branche

### Branche : `feature/reinitialisation_mdp`

**Objectif :** Implémenter la fonctionnalité de réinitialisation de mot de passe et améliorer la gestion des utilisateurs.

### Commits sur cette branche (7 commits)

| Commit | Description | Fichiers modifiés |
|--------|-------------|-------------------|
| `19073c3` | **test: Tests critiques password reset** | +21 tests, +2067 lignes |
| `b5c6cd8` | style: Corrections Ruff | Formatage |
| `4a6a542` | docs: Documentation gestion utilisateurs | GESTION_UTILISATEURS.md |
| `a55ef5f` | **feat: Soft delete utilisateurs** | Interface admin améliorée |
| `38e0b03` | **feat: Contrainte email unique** | Migration DB |
| `fb43402` | **fix: Gestion emails doubles** | Bug MultipleObjectsReturned |
| `419bfed` | **feat: Réinitialisation mot de passe** | Workflow complet |

### Fonctionnalités ajoutées sur cette branche

1. ✅ **Réinitialisation de mot de passe**
   - Formulaire "Mot de passe oublié"
   - Email avec lien de réinitialisation (token 24h)
   - Formulaire de nouveau mot de passe
   - Sécurité : pas de révélation d'informations

2. ✅ **Contrainte email unique**
   - Migration DB pour unicité
   - Message d'erreur en français
   - Protection contre les doublons

3. ✅ **Soft Delete**
   - Suppression douce (is_active=False)
   - Affichage grisé dans liste utilisateurs
   - Bouton "Réactiver" pour admins
   - Conservation des données (observations)

4. ✅ **Suite de tests complète**
   - 21 nouveaux tests (password reset)
   - Couverture : accounts/views/auth.py 26% → 70%
   - Tous les cas de sécurité testés

### État des modifications

**Prêt pour merge :**
- ✅ 66 tests passants (100%)
- ✅ Ruff : 0 erreur
- ✅ MyPy : 0 erreur
- ✅ Documentation complète
- ⏳ Tests manuels utilisateur en cours

---

## Guide de navigation de la documentation

### 📖 Documentation utilisateur (Fonctionnalités)

| Document | Description | Statut | Utilité |
|----------|-------------|--------|---------|
| **[GESTION_UTILISATEURS.md](GESTION_UTILISATEURS.md)** | 📘 Guide complet de gestion des utilisateurs | ✅ À jour | **Lire en premier** pour comprendre inscription, rôles, permissions, soft delete |
| **[REINITIALISATION_MOT_DE_PASSE.md](REINITIALISATION_MOT_DE_PASSE.md)** | 🔑 Documentation réinitialisation MDP | ✅ À jour | Workflow détaillé, sécurité, configuration emails |

### 🧪 Documentation tests

| Document | Description | Statut | Utilité |
|----------|-------------|--------|---------|
| **[STRATEGIE_TESTS.md](STRATEGIE_TESTS.md)** | 📊 Audit complet et plan de tests | ✅ À jour | **Essentiel** : État des 66 tests actuels + plan pour atteindre 80% de couverture (149 tests à venir) |
| **[TESTS_REINITIALISATION_MDP.md](TESTS_REINITIALISATION_MDP.md)** | ✅ Tests password reset implémentés | ✅ À jour | Détail des 21 tests créés aujourd'hui |

### 📋 Reprise rapide après interruption

**Si vous revenez sur ce projet dans quelques jours/semaines, lire dans cet ordre :**

1. **INDEX.md** (ce document) → Vue d'ensemble 5 minutes
2. **STRATEGIE_TESTS.md** → Sections 1-3 → Comprendre l'état des tests (10 minutes)
3. **GESTION_UTILISATEURS.md** → Parcourir la table des matières → Fonctionnalités disponibles (5 minutes)

**Pour reprendre le développement des tests :**
- **STRATEGIE_TESTS.md** → Section 4 "Plan de Tests Prioritaires" → **Phase 1** (soft delete, permissions)

**Pour comprendre une fonctionnalité spécifique :**
- Chercher dans GESTION_UTILISATEURS.md (table des matières complète)
- Voir les exemples de code et workflows

---

## État des tests

### Vue d'ensemble

| Métrique | Valeur actuelle | Objectif | Statut |
|----------|-----------------|----------|--------|
| **Tests totaux** | 66 | 174+ | 38% ⏳ |
| **Couverture globale** | 41% | 80%+ | 51% ⏳ |
| **Couverture accounts** | ~50% | 75%+ | 67% ⏳ |
| **Couverture observations** | 28% | 75%+ | 37% ⏳ |
| **Couverture geo** | 99% | 99% | 100% ✅ |

### Répartition des tests actuels

```
Total : 66 tests (100% passants)

accounts/
├── test_models.py ...................... 20 tests ✅
└── test_password_reset.py .............. 21 tests ✅ (nouveau)

observations/
└── test_models.py ...................... 9 tests ✅

geo/
└── test_api_communes.py ................ 13 tests ✅

Racine/
├── test_geocoding.py ................... 1 test ✅
├── test_remarques_popup.py ............. 1 test ✅
└── test_database_fallback.py ........... 1 test ✅
```

### Tests à ajouter (Plan 4 phases)

Voir **STRATEGIE_TESTS.md** pour le détail complet :

- **Phase 1** (Sécurité) : 57 tests → soft delete, permissions, email
- **Phase 2** (Données) : 46 tests → workflow observations, validations
- **Phase 3** (Métier) : 32 tests → emails, recherche, Celery
- **Phase 4** (Compléments) : 14 tests → exports, non-régression

**Total à ajouter : 149 tests**
**Temps estimé : 45-59 heures**

---

## Fonctionnalités implémentées

### Module `accounts` (Gestion utilisateurs)

#### ✅ Authentification et inscription

| Fonctionnalité | URL | Tests | Doc |
|----------------|-----|-------|-----|
| Inscription publique | `/accounts/inscription-publique/` | 4 tests | GESTION_UTILISATEURS.md §1 |
| Validation par admin | `/accounts/utilisateurs/{id}/valider/` | 2 tests | GESTION_UTILISATEURS.md §3.3 |
| Login/Logout | `/login/`, `/logout/` | - | - |

#### ✅ Réinitialisation de mot de passe (NOUVEAU)

| Fonctionnalité | URL | Tests | Doc |
|----------------|-----|-------|-----|
| Mot de passe oublié | `/accounts/mot-de-passe-oublie/` | 7 tests | REINITIALISATION_MOT_DE_PASSE.md §2 |
| Réinitialisation | `/accounts/reinitialiser-mot-de-passe/{uid}/{token}/` | 9 tests | REINITIALISATION_MOT_DE_PASSE.md §3 |
| Email service | EmailService.envoyer_email_reinitialisation_mdp() | 5 tests | REINITIALISATION_MOT_DE_PASSE.md §4 |

**Sécurité :**
- ✅ Tokens expiration 24h
- ✅ Pas de révélation d'informations (énumération users)
- ✅ Validation mot de passe (8+ caractères)
- ✅ HTTPS en production

#### ✅ Gestion des utilisateurs (Admin)

| Fonctionnalité | URL | Tests | Doc |
|----------------|-----|-------|-----|
| Liste utilisateurs | `/accounts/utilisateurs/` | 2 tests | GESTION_UTILISATEURS.md §3.1 |
| Créer utilisateur | `/accounts/utilisateurs/creer/` | 0 tests ⚠️ | GESTION_UTILISATEURS.md §3.2 |
| Modifier utilisateur | `/accounts/utilisateurs/{id}/modifier/` | 0 tests ⚠️ | GESTION_UTILISATEURS.md §3.2 |
| **Soft Delete** (NOUVEAU) | `/accounts/utilisateurs/{id}/desactiver/` | 0 tests ⚠️ | GESTION_UTILISATEURS.md §5 |
| **Réactiver** (NOUVEAU) | `/accounts/utilisateurs/{id}/activer/` | 0 tests ⚠️ | GESTION_UTILISATEURS.md §5 |
| Détail utilisateur | `/accounts/utilisateurs/{id}/detail/` | 0 tests ⚠️ | GESTION_UTILISATEURS.md §3.1 |
| Mon profil | `/accounts/mon-profil/` | 0 tests ⚠️ | GESTION_UTILISATEURS.md §3.4 |

#### ✅ Notifications

| Fonctionnalité | Tests | Doc |
|----------------|-------|-----|
| Notification nouvelle demande | 1 test | GESTION_UTILISATEURS.md §7.1 |
| Notification compte validé | Indirect | GESTION_UTILISATEURS.md §7.1 |
| Badge admin (demandes en attente) | 1 test | GESTION_UTILISATEURS.md §3.1 |

#### ✅ Contraintes et validations (NOUVEAU)

| Contrainte | Migration | Tests | Doc |
|------------|-----------|-------|-----|
| **Email unique** | `0003_email_unique_et_lien_default` | 1 test | GESTION_UTILISATEURS.md §6.1 |
| Notification.lien default | `0003_email_unique_et_lien_default` | - | - |

### Module `observations` (Fiches d'observation)

**Note :** Ce module a une couverture de 28% et nécessite des tests (voir Phase 2 de STRATEGIE_TESTS.md).

| Fonctionnalité | Tests | Statut |
|----------------|-------|--------|
| Modèles (FicheObservation, Observation, etc.) | 9 tests | ✅ Testés |
| Saisie observation (vues) | 0 tests | ⚠️ **À tester (Phase 2)** |
| Transcription (workflow) | 0 tests | ⚠️ **À tester (Phase 2)** |
| Validation expert | 0 tests | ⚠️ **À tester (Phase 2)** |
| Exports (CSV, JSON) | 0 tests | ⚠️ **À tester (Phase 4)** |
| Tâches Celery (images) | 0 tests | ⚠️ **À tester (Phase 3)** |

### Module `geo` (Géolocalisation)

✅ **Excellemment testé (99% de couverture)**

| Fonctionnalité | Tests | Statut |
|----------------|-------|--------|
| Recherche communes | 7 tests | ✅ |
| Géocodage | 3 tests | ✅ |
| Auto-remplissage | 2 tests | ✅ |
| Régression | 1 test | ✅ |

---

## Structure des fichiers du projet

### Fichiers de tests

```
accounts/tests/
├── __init__.py
├── conftest.py .................. Fixtures (user_observateur, user_admin, etc.)
├── test_models.py ............... 20 tests (Notification, EmailService, etc.)
└── test_password_reset.py ....... 21 tests (NOUVEAU - password reset complet)

observations/tests/
├── __init__.py
├── conftest.py .................. Fixtures (fiche, espece, etc.)
└── test_models.py ............... 9 tests

geo/tests/
├── __init__.py
└── test_api_communes.py ......... 13 tests

Racine/
├── test_geocoding.py
├── test_remarques_popup.py
├── test_database_fallback.py
├── conftest.py .................. Fixtures globales
└── pytest.ini ................... Configuration pytest
```

### Fichiers de documentation

```
docs/
├── INDEX.md ............................. 📖 Ce document (vue d'ensemble)
├── GESTION_UTILISATEURS.md .............. 📘 Guide complet gestion users (27 KB, 895 lignes)
├── REINITIALISATION_MOT_DE_PASSE.md ..... 🔑 Doc password reset (9 KB, 301 lignes)
├── STRATEGIE_TESTS.md ................... 📊 Plan de tests complet (40 KB, stratégie)
└── TESTS_REINITIALISATION_MDP.md ........ ✅ Tests implémentés aujourd'hui (9 KB)
```

---

## Prochaines étapes

### 🎯 Avant le merge (Immédiat)

- [x] ✅ Implémenter 21 tests critiques password reset
- [x] ✅ Créer documentation complète
- [ ] ⏳ **Tests manuels utilisateur** (en cours)
  - [ ] Test en mode production simulé (SMTP réel)
  - [ ] Test workflow complet (oubli MDP → email → reset)
  - [ ] Test soft delete (désactiver/réactiver)
  - [ ] Test contrainte email unique (formulaire)
- [ ] ⏳ Revue de code (optionnel)
- [ ] ⏳ Créer Pull Request
- [ ] ⏳ Merger dans main

### 📅 Semaine prochaine (Phase 1 - Sécurité)

**Objectif :** Couvrir 100% des fonctionnalités de sécurité

**À implémenter (57 tests, 13-18h) :**

1. **Tests Soft Delete** (18 tests) - `accounts/tests/test_soft_delete.py`
   - Désactivation/réactivation
   - Permissions admin
   - Affichage grisé
   - Conservation des données

2. **Tests Permissions** (15 tests) - `accounts/tests/test_permissions.py`
   - Contrôle d'accès admin
   - Contrôle d'accès superuser
   - Tentatives d'accès non autorisées

3. **Tests Email Unique** (7 tests) - `accounts/tests/test_email_uniqueness.py`
   - Formulaire inscription
   - Formulaire admin
   - Messages d'erreur français

4. **Tests Email Service Étendus** (17 tests restants)
   - Configuration SMTP vs console
   - Templates HTML
   - Gestion d'erreurs

**Résultat attendu :**
- Couverture accounts : 50% → 70%+
- Total tests : 66 → 123

### 📅 Mois suivant (Phases 2-4)

Voir **STRATEGIE_TESTS.md** pour le plan détaillé.

**Phase 2** (Semaines 3-4) : Tests observations (46 tests)
**Phase 3** (Semaines 5-6) : Tests métier (32 tests)
**Phase 4** (Semaines 7-8) : Compléments (14 tests)

**Objectif final :** 80%+ de couverture globale, 174+ tests

---

## Commandes utiles

### Tests

```bash
# Tous les tests
pytest

# Tests avec couverture
pytest --cov=. --cov-report=html

# Tests d'un module
pytest accounts/ -v
pytest observations/ -v

# Tests d'un fichier
pytest accounts/tests/test_password_reset.py -v

# Tests les plus lents
pytest --durations=10
```

### Qualité du code

```bash
# Linting
ruff check .
ruff check --fix .

# Formatage
ruff format .

# Type checking
mypy accounts/ observations/ geo/
```

### Git

```bash
# État de la branche
git status
git log --oneline feature/reinitialisation_mdp

# Voir les différences
git diff main...feature/reinitialisation_mdp

# Commits sur cette branche
git log main..feature/reinitialisation_mdp --oneline
```

---

## Contacts et ressources

### Documentation Django
- Tests : https://docs.djangoproject.com/en/5.2/topics/testing/
- Auth : https://docs.djangoproject.com/en/5.2/topics/auth/

### Documentation pytest
- pytest : https://docs.pytest.org/
- pytest-django : https://pytest-django.readthedocs.io/
- coverage : https://coverage.readthedocs.io/

### Projet GitHub
- Repository : (à compléter)
- Issues : (à compléter)
- Pull Requests : (à compléter)

---

## Notes pour la reprise rapide

### Si je (Claude) reviens sur ce projet après une interruption :

**🎯 Lecture rapide (15 minutes) :**
1. Lire cet INDEX.md en entier
2. Parcourir STRATEGIE_TESTS.md §1-2 (état actuel)
3. Voir la section "Prochaines étapes" ci-dessus

**🔍 Comprendre une fonctionnalité :**
- Consulter GESTION_UTILISATEURS.md (table des matières)
- Voir les exemples de code inline

**🧪 Continuer les tests :**
- Aller à STRATEGIE_TESTS.md → Section 4 → Phase 1
- Commencer par `test_soft_delete.py` (18 tests)

**📊 Vérifier l'état actuel :**
```bash
pytest --cov=. --cov-report=term-missing
git log --oneline -10
git status
```

### Si l'utilisateur revient après une interruption :

**Questions à poser :**
1. "Où en es-tu avec les tests manuels de la réinitialisation de mot de passe ?"
2. "As-tu rencontré des problèmes ?"
3. "Veux-tu merger maintenant ou continuer avec la Phase 1 des tests ?"

**Rappels importants :**
- 7 commits sur feature/reinitialisation_mdp
- 66 tests passants (100%)
- Prêt pour merge après validation manuelle
- Phase 1 (sécurité) est la prochaine priorité

---

**Document créé le :** 19 octobre 2025
**Dernière mise à jour :** 19 octobre 2025
**Version :** 1.0
**Auteur :** Claude Code + Jean-Marie Schneider
