# Tests de Réinitialisation de Mot de Passe

## Vue d'Ensemble

Ce document décrit les tests mis en place pour la fonctionnalité de réinitialisation de mot de passe.

**Fichier de tests :** `accounts/tests/test_password_reset.py`
**Nombre de tests :** 21 tests
**Couverture :**
- `accounts/forms.py` : 97% (était 0%)
- `accounts/views/auth.py` : 70% (était 26%) - **+44%**
- `accounts/utils/email_service.py` : 78% (était 18%) - **+60%**

---

## Tests Implémentés

### 1. Tests de Demande de Réinitialisation (`TestMotDePasseOublie`)

**7 tests couvrant la vue `mot_de_passe_oublie()` :**

#### test_affiche_formulaire_get
- **But :** Vérifier que la page affiche le formulaire en GET
- **Assertions :** Status 200, présence du formulaire, présence du texte "Mot de passe oublié"

#### test_email_existant_envoie_email
- **But :** Vérifier qu'un email est envoyé pour un utilisateur existant et actif
- **Assertions :**
  - Redirection vers login (302)
  - Un email dans la boîte d'envoi
  - Email envoyé à la bonne adresse
  - Sujet contient "Réinitialisation"

#### test_email_inexistant_pas_revelation
- **But :** **SÉCURITÉ** - Ne pas révéler si un email existe ou non
- **Assertions :**
  - Message générique identique
  - Aucun email envoyé
  - Pas d'information divulguée

#### test_utilisateur_inactif_ignore
- **But :** **SÉCURITÉ** - Les utilisateurs inactifs ne peuvent pas réinitialiser leur mot de passe
- **Assertions :**
  - Message générique (ne pas révéler que le compte est inactif)
  - Aucun email envoyé

#### test_contrainte_email_unique_active
- **But :** Vérifier que la contrainte d'unicité sur l'email est active en base de données
- **Assertions :**
  - Création du premier utilisateur réussit
  - Création du second avec même email lève `IntegrityError`
  - Message d'erreur contient "email" ou "Duplicate"

#### test_formulaire_email_invalide
- **But :** Validation côté formulaire des emails invalides
- **Assertions :**
  - Reste sur la page (200)
  - Formulaire contient des erreurs
  - Aucun email envoyé

#### test_redirection_apres_soumission_valide
- **But :** Vérifier le workflow après soumission valide
- **Assertions :**
  - Redirection vers login (302)
  - URL correcte

---

### 2. Tests de Réinitialisation avec Token (`TestReinitialiserMotDePasse`)

**9 tests couvrant la vue `reinitialiser_mot_de_passe()` :**

#### test_token_valide_affiche_formulaire
- **But :** Un token valide affiche le formulaire de nouveau mot de passe
- **Assertions :**
  - Status 200
  - Formulaire présent
  - `validlink` = True

#### test_token_invalide_affiche_erreur
- **But :** **SÉCURITÉ** - Token invalide refuse l'accès
- **Assertions :**
  - Status 200 (page d'erreur)
  - `validlink` = False
  - Pas de formulaire

#### test_uid_invalide_affiche_erreur
- **But :** **SÉCURITÉ** - UID malformé refuse l'accès
- **Assertions :**
  - Status 200
  - `validlink` = False

#### test_utilisateur_inexistant_affiche_erreur
- **But :** **SÉCURITÉ** - UID d'utilisateur inexistant refuse l'accès
- **Assertions :**
  - Status 200
  - `validlink` = False

#### test_mot_de_passe_court_refuse
- **But :** Validation : mot de passe < 8 caractères refusé
- **Assertions :**
  - Reste sur la page (200)
  - Formulaire contient erreurs
  - Mot de passe non changé

#### test_mots_de_passe_differents_refuse
- **But :** Validation : les deux mots de passe doivent correspondre
- **Assertions :**
  - Reste sur la page (200)
  - Erreur sur `password2` ou `__all__`
  - Mot de passe non changé

#### test_reset_reussi_sauvegarde_hash
- **But :** Un reset réussi sauvegarde le nouveau mot de passe hashé
- **Assertions :**
  - Redirection vers login (302)
  - Hash du mot de passe a changé
  - Nouveau mot de passe fonctionne (check_password)

#### test_reset_reussi_redirige_login
- **But :** Workflow complet : redirection vers login après succès
- **Assertions :**
  - Status 302
  - URL = reverse('login')

#### test_reset_reussi_affiche_message_succes
- **But :** Message de succès affiché après reset
- **Assertions :**
  - Message présent
  - Contient "réinitialisé" ou "succès"

---

### 3. Tests d'Envoi d'Email (`TestEmailReinitialisation`)

**5 tests couvrant le service email :**

#### test_email_contient_lien_valide
- **But :** L'email contient un lien de réinitialisation valide
- **Assertions :**
  - Un email envoyé
  - Body contient "reinitialiser-mot-de-passe"
  - URL complète présente

#### test_email_contient_uid_et_token
- **But :** Le lien contient un UID et un token
- **Assertions :**
  - Lien au format `/accounts/reinitialiser-mot-de-passe/{uid}/{token}/`
  - Au moins une ligne avec le lien

#### test_utilisateur_sans_email_gere
- **But :** Gestion des utilisateurs sans email
- **Assertions :**
  - Formulaire rejette email vide
  - Reste sur la page (200)
  - Mock vérifie que la méthode n'envoie pas d'email

#### test_email_html_et_texte
- **But :** L'email contient une version HTML et texte
- **Assertions :**
  - Email a des alternatives
  - Alternative HTML contient des balises HTML

#### test_protocole_url_correct
- **But :** **SÉCURITÉ** - URL utilise le bon protocole (HTTP dev, HTTPS prod)
- **Assertions :**
  - Si DEBUG=True : http://
  - Si DEBUG=False : https://

---

## Couverture de Code

### Avant les tests
```
accounts/forms.py                  0%
accounts/views/auth.py            26%
accounts/utils/email_service.py   18%
```

### Après les tests
```
accounts/forms.py                 97%  (+97%)
accounts/views/auth.py            70%  (+44%)
accounts/utils/email_service.py   78%  (+60%)
```

### Lignes non couvertes restantes

**accounts/views/auth.py (59 lignes non couvertes) :**
- Ligne 34 : Vérification est_admin (testé indirectement)
- Lignes 54-72 : Autres vues (creer_utilisateur, modifier_utilisateur, etc.) - **À tester en Phase 1**
- Lignes 91-102 : creer_utilisateur POST
- Lignes 109-122 : modifier_utilisateur
- Lignes 133-147 : desactiver_utilisateur
- Lignes 154-165 : activer_utilisateur
- Lignes 172-186 : detail_utilisateur
- Lignes 192-202 : mon_profil
- Lignes 249-264 : promouvoir_administrateur

**accounts/utils/email_service.py (18 lignes non couvertes) :**
- Lignes 62-66, 80-81, 111-115, 130-131, 162-166, 182-183, 222-226 : Gestion d'erreurs (blocs `except`)

**accounts/forms.py (1 ligne non couverte) :**
- Ligne 18 : save() avec commit=False (edge case)

---

## Fixtures Créées

### Dans `accounts/tests/conftest.py`

```python
@pytest.fixture
def user_observateur(db):
    """Utilisateur avec rôle observateur validé et actif."""

@pytest.fixture
def user_admin(db):
    """Utilisateur avec rôle administrateur."""

@pytest.fixture
def user_superuser(db):
    """Superuser pour tests de permissions."""

@pytest.fixture
def user_inactif(db):
    """Utilisateur désactivé (soft delete)."""

@pytest.fixture
def user_non_valide(db):
    """Utilisateur en attente de validation admin."""
```

Ces fixtures sont réutilisables pour tous les tests du module `accounts`.

---

## Cas de Sécurité Testés

### ✅ Protection contre les attaques

1. **Énumération d'utilisateurs** :
   - Message générique identique que l'email existe ou non
   - Pas de révélation d'informations sur les comptes inactifs

2. **Tokens invalides** :
   - Token manipulé refusé
   - UID invalide refusé
   - Utilisateur inexistant refusé

3. **Mots de passe faibles** :
   - Minimum 8 caractères
   - Correspondance des deux champs

4. **Contrainte unicité email** :
   - Impossible de créer deux comptes avec le même email
   - Protection au niveau base de données

5. **Protocole HTTPS** :
   - URLs de réinitialisation en HTTPS en production
   - HTTP seulement en développement

---

## Exécution des Tests

### Lancer tous les tests de réinitialisation
```bash
pytest accounts/tests/test_password_reset.py -v
```

### Lancer avec couverture
```bash
pytest accounts/tests/test_password_reset.py --cov=accounts --cov-report=term-missing
```

### Lancer un test spécifique
```bash
pytest accounts/tests/test_password_reset.py::TestMotDePasseOublie::test_email_existant_envoie_email -v
```

### Lancer tous les tests du module accounts
```bash
pytest accounts/ -v
```

---

## Améliorations Futures (Phase 1 - Stratégie de Tests)

Ces tests couvrent la réinitialisation de mot de passe. Les tests suivants sont recommandés :

1. **Tests de soft delete** (18 tests) :
   - Désactivation/réactivation utilisateurs
   - Affichage grisé dans liste
   - Permissions admin

2. **Tests de permissions** (15 tests) :
   - Contrôle d'accès admin
   - Contrôle d'accès superuser
   - Profils utilisateurs

3. **Tests de service email étendus** (12 tests) :
   - Configuration email (console vs SMTP)
   - Templates HTML
   - Gestion d'erreurs

Voir `docs/STRATEGIE_TESTS.md` pour le plan complet.

---

## Résultats

✅ **21 tests passent**
✅ **0 erreur de linting (Ruff)**
✅ **0 erreur de typage (MyPy)**
✅ **Couverture accounts/views/auth.py : 70%** (objectif Phase 1 : 50%+ atteint)
✅ **Couverture accounts/forms.py : 97%**
✅ **Couverture accounts/utils/email_service.py : 78%**

**Total tests projet :** 66 (était 45)
**Couverture globale :** 41% (était 40%)

---

**Date de création :** 19 octobre 2025
**Auteur :** Claude Code
**Version :** 1.0
