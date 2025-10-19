# Stratégie de Tests - Observations Nids

## Date d'Analyse : 19 octobre 2025

---

## 1. État Actuel des Tests

### 1.1 Vue d'Ensemble

**Statistiques globales :**
- **25 tests** actuellement dans le projet, tous passant ✅
- **Couverture globale : 40%** (1059 lignes couvertes sur 2644)
- **3 modules testés** : `geo`, `observations`, `accounts`

**Répartition des tests :**
```
├── accounts/tests.py ..................... 20 tests
│   ├── TestNotificationModel ............ 4 tests
│   ├── TestEmailService ................. 4 tests
│   ├── TestInscriptionPubliqueView ...... 4 tests
│   ├── TestValiderUtilisateurView ....... 2 tests
│   ├── TestHomePageNotifications ........ 4 tests
│   └── TestListeUtilisateursView ........ 2 tests
│
├── observations/tests/test_models.py ..... 9 tests
│   ├── TestFicheObservation ............. 3 tests
│   ├── TestObservation .................. 2 tests
│   ├── TestResumeObservation ............ 2 tests
│   └── TestLocalisation ................. 2 tests
│
├── geo/tests/test_api_communes.py ........ 13 tests
│   ├── TestRechercherCommunes ........... 7 tests
│   ├── TestAutoRemplissageGeo ........... 2 tests
│   ├── TestGeocodageManuel .............. 3 tests
│   └── TestRegressionAutocompletion ..... 1 test
│
└── Tests racine .......................... 3 tests
    ├── test_geocoding.py
    ├── test_remarques_popup.py
    └── test_database_fallback.py
```

### 1.2 Couverture par Module

| Module | Couverture | Lignes couvertes / Total | État |
|--------|-----------|--------------------------|------|
| **geo** | **99%** | 169/171 | ✅ Excellent |
| **accounts** | **9%** | 147/1580 | ⚠️ Critique |
| **observations** | **28%** | 743/2644 | ⚠️ Insuffisant |
| **audit** | **89%** | 16/18 | ✅ Bon |
| **core** | **86%** | 18/21 | ✅ Bon |

---

## 2. Analyse Détaillée par Module

### 2.1 Module `accounts` - PRIORITÉ CRITIQUE ⚠️

**Couverture actuelle : 9%**

#### Zones NON testées (critiques pour la sécurité) :

**A. Vues d'authentification (`accounts/views/auth.py` - 194 lignes, 0% couvert) :**

❌ **Fonctionnalités critiques sans tests :**

1. **Réinitialisation de mot de passe** (nouvellement implémentée) :
   - `mot_de_passe_oublie()` - lignes 301-340
   - `reinitialiser_mot_de_passe()` - lignes 343-384
   - **Risques** : Tokens invalides, emails multiples, failles de sécurité

2. **Gestion des utilisateurs** :
   - `creer_utilisateur()` - lignes 89-102
   - `modifier_utilisateur()` - lignes 107-126
   - `desactiver_utilisateur()` (soft delete) - lignes 131-147
   - `activer_utilisateur()` - lignes 152-165
   - **Risques** : Permissions, intégrité des données

3. **Détails et profils** :
   - `detail_utilisateur()` - lignes 170-186
   - `mon_profil()` - lignes 190-202
   - **Risques** : Fuites d'informations, requêtes AJAX

4. **Promotion administrateur** :
   - `promouvoir_administrateur()` - lignes 246-264
   - **Risques** : Élévation de privilèges non autorisée

**B. Service d'emails (`accounts/utils/email_service.py` - 82 lignes, 0% couvert) :**

❌ **Méthode critique sans tests :**
- `envoyer_email_reinitialisation_mdp()` - lignes 169-226
- **Risques** : URLs incorrectes, protocole HTTP/HTTPS, tokens non transmis

**C. Formulaires (`accounts/forms.py` - 35 lignes, 0% couvert) :**

❌ **Validations non testées :**
- `MotDePasseOublieForm` - validation d'email
- `NouveauMotDePasseForm` - validation de mot de passe (8+ caractères, correspondance)
- **Risques** : Mots de passe faibles acceptés, validations bypassées

#### Zones TESTÉES (couverture partielle) :

✅ **Tests existants (20 tests) couvrent :**
- Modèle Notification (création, lecture, tri)
- Service email de base (nouvelle demande, validation, refus)
- Inscription publique (workflow complet)
- Validation utilisateur par admin
- Notifications page d'accueil
- Liste utilisateurs (filtres basiques)

**Couverture models : 84%** - Bon, quelques méthodes manquantes (lignes 86, 92-95)

---

### 2.2 Module `observations` - PRIORITÉ ÉLEVÉE ⚠️

**Couverture actuelle : 28%**

#### Zones NON testées :

**A. Vue principale de saisie (`observations/views/saisie_observation_view.py` - 363 lignes, 9% couvert) :**

❌ **Fonctionnalités complexes sans tests :**
- Création de fiche avec transcription (lignes 33-97)
- Mise à jour fiche complète (lignes 104-121)
- Logique de verrouillage/déverrouillage (lignes 126-146)
- Validation et soumission (lignes 157-588) - **425 lignes non testées !**
- Système de corrections (lignes 593-614)
- Clonage de fiches (lignes 623-633)
- Export CSV/JSON (lignes 641-646)
- Suppression (lignes 657-674)
- Gestion des permissions (lignes 680-727)

**B. Vue de transcription (`observations/views/view_transcription.py` - 120 lignes, 29% couvert) :**

❌ **Workflow de transcription non testé :**
- Liste des fiches à transcrire (lignes 25-53)
- Saisie transcription (lignes 58-65)
- Mise à jour transcription (lignes 71-102)
- Validation transcripteur (lignes 127-205)

**C. Tâches Celery (`observations/tasks.py` - 86 lignes, 15% couvert) :**

❌ **Tâches asynchrones non testées :**
- `verifier_et_traiter_images_manquantes()` (lignes 29-181)
- **Risques** : Pertes de données, traitements échoués silencieusement

**D. Formulaires (`observations/forms.py` - 73 lignes, 64% couvert) :**

⚠️ **Validations partiellement testées :**
- Formulaires de recherche (lignes 30-43)
- Formulaires de date (lignes 89-91, 119-123)
- Formulaires de localisation (lignes 132-135, 183-196)

**E. Modèles (`observations/models.py` - 140 lignes, 56% couvert) :**

⚠️ **Méthodes métier non testées :**
- Propriétés calculées (lignes 239, 249, 258)
- Méthodes de validation (lignes 295, 299-301)
- Logique de statut (lignes 305-362)
- Signal handlers (lignes 366-369)

---

### 2.3 Module `geo` - EXCELLENT ✅

**Couverture actuelle : 99%**

✅ **Points forts :**
- API de recherche de communes exhaustivement testée
- Géocodage manuel et automatique couverts
- Tests de régression présents
- Validations de coordonnées testées
- Gestion des distances et limites testée

⚠️ **Améliorations mineures :**
- 2 lignes non couvertes (lignes 343-344 dans test_api_communes.py)
- Commandes de management non testées (charger_altitudes, charger_communes_france, reset_*)

---

### 2.4 Modules `core` et `audit` - BON ✅

**core : 86%** - Bonne couverture, exceptions personnalisées non testées (14 lignes)
**audit : 89%** - Bon, quelques méthodes du modèle AuditLog manquantes

---

## 3. Zones Critiques Sans Tests

### 3.1 SÉCURITÉ (Priorité : CRITIQUE)

#### A. Authentification et Autorisations

❌ **Tests manquants :**

1. **Réinitialisation de mot de passe** (feature/reinitialisation_mdp) :
   ```
   - Test token expiré (> 24h)
   - Test token invalide / manipulé
   - Test utilisateur inexistant
   - Test utilisateur désactivé
   - Test emails multiples pour même adresse
   - Test URL de reset correcte (HTTP vs HTTPS)
   - Test validation mot de passe faible
   - Test non-correspondance mots de passe
   ```

2. **Contrôle d'accès** :
   ```
   - Test utilisateur non-admin tente d'accéder /accounts/utilisateurs/
   - Test utilisateur non-admin tente de créer/modifier utilisateur
   - Test utilisateur non-superuser tente promouvoir_administrateur
   - Test utilisateur tente de voir profil d'un autre utilisateur
   - Test utilisateur désactivé tente de se connecter
   - Test utilisateur non validé tente de se connecter
   ```

3. **Soft Delete** (nouvellement implémenté) :
   ```
   - Test désactivation conserve les données
   - Test utilisateur désactivé ne peut plus se connecter
   - Test réactivation restaure l'accès
   - Test observateur désactivé : ses fiches restent visibles
   - Test message de confirmation utilisateur
   - Test affichage grisé dans liste utilisateurs
   - Test filtre statut (actifs/inactifs)
   ```

4. **Unicité email** (contrainte DB récente) :
   ```
   - Test création utilisateur avec email existant
   - Test modification email vers email existant
   - Test message d'erreur français correct
   - Test formulaire inscription publique rejette doublon
   ```

#### B. Gestion des Permissions

❌ **Tests manquants :**
```
- Test est_admin() avec utilisateur role='observateur'
- Test est_admin() avec utilisateur anonyme
- Test est_superuser() avec admin non-superuser
- Test LoginRequiredMixin sur toutes les vues protégées
- Test UserPassesTestMixin sur vues admin-only
```

---

### 3.2 INTÉGRITÉ DES DONNÉES (Priorité : ÉLEVÉE)

#### A. Workflow Observations

❌ **Tests manquants :**

1. **Cycle de vie d'une fiche** :
   ```
   - Test création fiche → saisie → validation → envoi
   - Test correction par expert → renvoi observateur → resoumission
   - Test verrouillage pendant édition
   - Test déverrouillage après 30 minutes
   - Test blocage édition si fiche verrouillée par autre user
   - Test soft delete fiche conserve observations liées
   ```

2. **Validation des données** :
   ```
   - Test contrainte oeufs_eclos <= oeufs_pondus (partiellement testé)
   - Test dates cohérentes (début < fin, année valide)
   - Test nombres positifs (déjà testé pour Observation)
   - Test jour/mois ensemble ou NULL (déjà testé)
   - Test altitudes valides (-500m à 9000m)
   - Test coordonnées GPS valides (lat/lon)
   ```

3. **Relations entre objets** :
   ```
   - Test cascade delete : fiche → observations/localisation/nid/resume
   - Test observateur supprimé → fiches conservées avec référence
   - Test espèce supprimée → comportement sur fiches existantes
   ```

#### B. Transcription

❌ **Tests manquants :**
```
- Test workflow complet : import CSV → transcription → validation
- Test statuts transcription (en_attente, en_cours, validee, refusee)
- Test transcripteur ne peut modifier que fiches non validées
- Test expert valide/refuse transcription
- Test notification observateur après validation
```

---

### 3.3 FONCTIONNALITÉS MÉTIER (Priorité : MOYENNE)

#### A. Emails

❌ **Tests manquants :**
```
- Test envoi email réinitialisation mdp (nouveau)
- Test email avec utilisateur sans adresse email
- Test email en mode console vs SMTP
- Test templates HTML rendus correctement
- Test contexte email contient toutes les variables
- Test fallback texte brut si HTML échoue
```

#### B. Notifications

✅ **Déjà testés :**
- Création notification
- Marquage comme lu
- Tri par date

❌ **Tests manquants :**
```
- Test notification supprimée si utilisateur concerné supprimé
- Test notification cliquée redirige vers bon lien
- Test badge compte notifications non lues
- Test notification admin pour nouvelle inscription
```

#### C. Recherche et Filtres

❌ **Tests manquants :**
```
- Test recherche utilisateurs (username, nom, email)
- Test filtres liste utilisateurs (role, validé, actif)
- Test pagination (20 utilisateurs par page)
- Test tri par date d'inscription décroissante
- Test recherche observations par critères multiples
- Test export CSV observations filtrées
```

---

### 3.4 UI/UX (Priorité : BASSE)

❌ **Tests manquants :**
```
- Test requêtes AJAX (détail utilisateur)
- Test affichage conditionnel boutons (Supprimer/Réactiver)
- Test messages de confirmation JavaScript
- Test CSS inactive users (opacité, line-through)
- Test responsive design
- Test accessibilité (ARIA, contraste)
```

---

## 4. Plan de Tests Prioritaires

### Phase 1 : SÉCURITÉ CRITIQUE (Semaines 1-2)

**Objectif : Couvrir 100% des fonctionnalités de sécurité**

#### 4.1 Tests de Réinitialisation de Mot de Passe

**Fichier : `accounts/tests/test_password_reset.py`** (nouveau)

```python
class TestMotDePasseOublie:
    """Tests pour la demande de réinitialisation"""

    def test_email_existant_envoie_email()
    def test_email_inexistant_message_generique()  # Sécurité : pas de révélation
    def test_utilisateur_inactif_pas_email()
    def test_utilisateurs_multiples_meme_email_tous_recevant()
    def test_formulaire_email_invalide()
    def test_redirection_apres_soumission()

class TestReinitialiserMotDePasse:
    """Tests pour la réinitialisation avec token"""

    def test_token_valide_affiche_formulaire()
    def test_token_invalide_affiche_erreur()
    def test_token_expire_affiche_erreur()  # Simuler > 24h
    def test_uid_invalide_affiche_erreur()
    def test_utilisateur_inexistant_affiche_erreur()
    def test_mot_de_passe_court_rejete()  # < 8 caractères
    def test_mots_de_passe_differents_rejete()
    def test_reset_reussi_sauvegarde_hash()
    def test_reset_reussi_redirige_login()
    def test_reset_reussi_logue_action()
    def test_url_reset_protocole_correct()  # HTTP dev, HTTPS prod

class TestEmailReinitialisation:
    """Tests pour l'envoi d'email de reset"""

    def test_email_contient_lien_correct()
    def test_email_contient_uid_et_token()
    def test_email_html_et_texte_brut()
    def test_email_pas_envoye_si_utilisateur_sans_email()
    def test_email_logue_envoi()
```

**Estimation : 17 tests, 4-6 heures**

#### 4.2 Tests de Soft Delete

**Fichier : `accounts/tests/test_soft_delete.py`** (nouveau)

```python
class TestDesactiverUtilisateur:
    """Tests pour la suppression (soft delete)"""

    def test_admin_peut_desactiver()
    def test_observateur_ne_peut_pas_desactiver()
    def test_utilisateur_anonyme_ne_peut_pas_desactiver()
    def test_desactivation_met_is_active_false()
    def test_desactivation_conserve_donnees()
    def test_desactivation_conserve_fiches_observateur()
    def test_desactivation_logue_action()
    def test_desactivation_affiche_message_succes()
    def test_desactivation_require_post()

class TestActiverUtilisateur:
    """Tests pour la réactivation"""

    def test_admin_peut_reactiver()
    def test_reactivation_met_is_active_true()
    def test_reactivation_logue_action()
    def test_reactivation_affiche_message_succes()

class TestUtilisateurDesactive:
    """Tests pour comportement utilisateur désactivé"""

    def test_utilisateur_desactive_ne_peut_pas_login()
    def test_utilisateur_desactive_affiche_grise_dans_liste()
    def test_filtre_statut_actifs_exclut_desactives()
    def test_filtre_statut_inactifs_montre_desactives()
    def test_badge_compte_exclut_desactives()
```

**Estimation : 18 tests, 4-5 heures**

#### 4.3 Tests de Contrôle d'Accès

**Fichier : `accounts/tests/test_permissions.py`** (nouveau)

```python
class TestPermissionsAdmin:
    """Tests pour les permissions administrateur"""

    def test_admin_peut_lister_utilisateurs()
    def test_observateur_ne_peut_pas_lister_utilisateurs()
    def test_admin_peut_creer_utilisateur()
    def test_observateur_ne_peut_pas_creer_utilisateur()
    def test_admin_peut_modifier_utilisateur()
    def test_observateur_ne_peut_pas_modifier_utilisateur()
    def test_anonyme_redirige_login()

class TestPermissionsSuperuser:
    """Tests pour les permissions superuser"""

    def test_superuser_peut_promouvoir_admin()
    def test_admin_non_superuser_ne_peut_pas_promouvoir()
    def test_observateur_ne_peut_pas_promouvoir()

class TestPermissionsProfil:
    """Tests pour les profils utilisateurs"""

    def test_utilisateur_peut_voir_son_profil()
    def test_utilisateur_ne_peut_pas_voir_profil_autre()
    def test_admin_peut_voir_detail_utilisateur()
    def test_requete_ajax_retourne_partial_template()
```

**Estimation : 15 tests, 3-4 heures**

#### 4.4 Tests de Contrainte Email Unique

**Fichier : `accounts/tests/test_email_uniqueness.py`** (nouveau)

```python
class TestEmailUnique:
    """Tests pour la contrainte d'unicité email"""

    def test_creation_utilisateur_email_unique_ok()
    def test_creation_utilisateur_email_existant_erreur()
    def test_modification_email_vers_existant_erreur()
    def test_message_erreur_francais()
    def test_inscription_publique_email_existant_erreur()
    def test_formulaire_admin_email_existant_erreur()
    def test_case_insensitive_email()  # test@TEST.com vs test@test.com
```

**Estimation : 7 tests, 2-3 heures**

**TOTAL PHASE 1 : 57 tests, 13-18 heures**

---

### Phase 2 : INTÉGRITÉ DONNÉES (Semaines 3-4)

**Objectif : Couvrir 80% des vues observations**

#### 4.5 Tests de Workflow Observations

**Fichier : `observations/tests/test_workflow_fiche.py`** (nouveau)

```python
class TestCreationFiche:
    """Tests pour la création de fiche"""

    def test_creation_fiche_observateur()
    def test_creation_fiche_transcription()
    def test_creation_fiche_cree_objets_lies()  # Déjà testé partiellement
    def test_creation_fiche_sans_permission()
    def test_auto_increment_num_fiche()

class TestEditionFiche:
    """Tests pour l'édition de fiche"""

    def test_edition_fiche_observateur_proprietaire()
    def test_edition_fiche_autre_observateur_refuse()
    def test_edition_fiche_admin_autorise()
    def test_edition_fiche_statut_brouillon()
    def test_edition_fiche_statut_validee_refuse()

class TestVerrouillageFiche:
    """Tests pour le système de verrouillage"""

    def test_verrouillage_edition_user()
    def test_autre_user_bloque_si_verrouille()
    def test_deverrouillage_apres_30_minutes()
    def test_deverrouillage_manuel()
    def test_message_fiche_verrouillee()

class TestValidationFiche:
    """Tests pour la soumission et validation"""

    def test_soumission_fiche_change_statut()
    def test_soumission_fiche_notifie_expert()
    def test_validation_expert_marque_validee()
    def test_demande_correction_renvoie_observateur()
    def test_correction_observateur_resoumission()

class TestSuppressionFiche:
    """Tests pour la suppression"""

    def test_soft_delete_fiche()
    def test_suppression_conserve_observations_liees()
    def test_suppression_admin_autorise()
    def test_suppression_autre_observateur_refuse()
```

**Estimation : 25 tests, 8-10 heures**

#### 4.6 Tests de Validation Données

**Fichier : `observations/tests/test_validations.py`** (nouveau)

```python
class TestValidationsDates:
    """Tests pour les validations de dates"""

    def test_annee_future_refusee()
    def test_annee_ancienne_acceptee()
    def test_date_debut_avant_date_fin()
    def test_date_observation_coherente()

class TestValidationsNombres:
    """Tests pour les validations de nombres"""

    def test_nombres_negatifs_refuses()  # Déjà testé pour Observation
    def test_oeufs_eclos_superieur_pondus_refuse()  # Déjà testé
    def test_altitude_valide()
    def test_coordonnees_gps_valides()

class TestValidationsRelations:
    """Tests pour les contraintes relationnelles"""

    def test_cascade_delete_fiche_observations()
    def test_observateur_supprime_fiches_conservees()
    def test_espece_supprimee_comportement()
    def test_jour_mois_ensemble_ou_null()  # Déjà testé
```

**Estimation : 13 tests, 4-5 heures**

#### 4.7 Tests de Transcription

**Fichier : `observations/tests/test_transcription.py`** (nouveau)

```python
class TestWorkflowTranscription:
    """Tests pour le workflow de transcription"""

    def test_liste_fiches_a_transcrire()
    def test_transcripteur_peut_saisir()
    def test_transcripteur_peut_modifier_non_validee()
    def test_transcripteur_ne_peut_pas_modifier_validee()
    def test_expert_peut_valider()
    def test_expert_peut_refuser()
    def test_validation_notifie_observateur()
    def test_statuts_transcription()
```

**Estimation : 8 tests, 3-4 heures**

**TOTAL PHASE 2 : 46 tests, 15-19 heures**

---

### Phase 3 : FONCTIONNALITÉS MÉTIER (Semaines 5-6)

**Objectif : Couvrir services et tâches asynchrones**

#### 4.8 Tests de Service Email Complets

**Fichier : `accounts/tests/test_email_service_extended.py`** (nouveau)

```python
class TestEmailServiceReinitialisation:
    """Tests pour email réinitialisation (nouveau)"""

    def test_envoyer_email_reinitialisation_mdp_succes()
    def test_email_contient_uid_token()
    def test_url_reset_https_production()
    def test_url_reset_http_developpement()
    def test_template_html_rendu()
    def test_fallback_texte_brut()
    def test_utilisateur_sans_email_retourne_false()
    def test_exception_email_logue_erreur()

class TestEmailServiceConfiguration:
    """Tests pour la configuration email"""

    def test_console_backend_developpement()
    def test_smtp_backend_production()
    def test_admin_email_manquant_logge_warning()
    def test_from_email_correct()
```

**Estimation : 12 tests, 4-5 heures**

#### 4.9 Tests de Recherche et Filtres

**Fichier : `accounts/tests/test_recherche_filtres.py`** (nouveau)

```python
class TestRechercheUtilisateurs:
    """Tests pour la recherche d'utilisateurs"""

    def test_recherche_par_username()
    def test_recherche_par_email()
    def test_recherche_par_nom()
    def test_recherche_par_prenom()
    def test_recherche_insensible_casse()
    def test_recherche_partielle()

class TestFiltresUtilisateurs:
    """Tests pour les filtres liste utilisateurs"""

    def test_filtre_par_role()
    def test_filtre_par_validation()
    def test_filtre_par_statut_actif()
    def test_filtres_combines()
    def test_pagination_20_par_page()
    def test_tri_date_inscription_decroissant()

class TestBadgeNotifications:
    """Tests pour le badge de notifications"""

    def test_compte_demandes_en_attente()
    def test_badge_affiche_nombre_correct()
    def test_badge_visible_admin_seulement()
```

**Estimation : 15 tests, 4-5 heures**

#### 4.10 Tests des Tâches Celery

**Fichier : `observations/tests/test_celery_tasks.py`** (nouveau)

```python
class TestTasksImages:
    """Tests pour les tâches de traitement d'images"""

    def test_verifier_images_manquantes()
    def test_traiter_image_valide()
    def test_traiter_image_invalide_logue_erreur()
    def test_tache_asynchrone_executee()
    def test_retry_en_cas_echec()
```

**Estimation : 5 tests, 3-4 heures**

**TOTAL PHASE 3 : 32 tests, 11-14 heures**

---

### Phase 4 : COMPLÉMENTS (Semaines 7-8)

**Objectif : Atteindre 80%+ de couverture globale**

#### 4.11 Tests des Vues Observations Complexes

**Fichier : `observations/tests/test_saisie_observation.py`** (nouveau)

```python
class TestSaisieObservation:
    """Tests pour la vue principale de saisie"""

    def test_get_affiche_formulaire()
    def test_post_cree_fiche()
    def test_validation_donnees_formulaire()
    def test_gestion_erreurs_formulaire()

class TestExportDonnees:
    """Tests pour l'export de données"""

    def test_export_csv()
    def test_export_json()
    def test_export_filtre_par_observateur()
    def test_export_filtre_par_date()

class TestClonageFiche:
    """Tests pour le clonage de fiches"""

    def test_clonage_copie_donnees()
    def test_clonage_nouveau_num_fiche()
    def test_clonage_preserve_observateur()
```

**Estimation : 11 tests, 5-6 heures**

#### 4.12 Tests de Non-Régression

**Fichier : `tests/test_regressions.py`** (nouveau)

```python
class TestRegressions:
    """Tests pour bugs connus résolus"""

    def test_regression_multiple_emails_filter()  # Bug MultipleObjectsReturned
    def test_regression_email_backend_console()   # Bug email non reçu
    def test_regression_notification_lien_default()  # Migration nullable
```

**Estimation : 3 tests, 1-2 heures**

**TOTAL PHASE 4 : 14 tests, 6-8 heures**

---

## 5. Résumé du Plan

### 5.1 Objectifs Chiffrés

| Phase | Domaine | Tests à ajouter | Heures estimées | Couverture cible |
|-------|---------|-----------------|-----------------|------------------|
| 1 | Sécurité | 57 tests | 13-18h | accounts: 50%+ |
| 2 | Données | 46 tests | 15-19h | observations: 60%+ |
| 3 | Métier | 32 tests | 11-14h | accounts: 70%+, observations: 70%+ |
| 4 | Compléments | 14 tests | 6-8h | Global: 80%+ |
| **TOTAL** | - | **149 tests** | **45-59h** | **80%+** |

**Tests actuels : 25**
**Tests après plan : 174 tests**

### 5.2 Couverture Attendue Après Plan

| Module | Avant | Après | Amélioration |
|--------|-------|-------|--------------|
| accounts | 9% | 75%+ | +66% |
| observations | 28% | 75%+ | +47% |
| geo | 99% | 99% | - |
| **GLOBAL** | **40%** | **80%+** | **+40%** |

---

## 6. Recommandations d'Implémentation

### 6.1 Structure des Tests

**Organisation proposée :**

```
tests/
├── accounts/
│   ├── __init__.py
│   ├── conftest.py                      # Fixtures communes accounts
│   ├── test_models.py                   # Existant (Notification, Utilisateur)
│   ├── test_password_reset.py           # PHASE 1 - Nouveau
│   ├── test_soft_delete.py              # PHASE 1 - Nouveau
│   ├── test_permissions.py              # PHASE 1 - Nouveau
│   ├── test_email_uniqueness.py         # PHASE 1 - Nouveau
│   ├── test_email_service_extended.py   # PHASE 3 - Nouveau
│   └── test_recherche_filtres.py        # PHASE 3 - Nouveau
│
├── observations/
│   ├── __init__.py
│   ├── conftest.py                      # Fixtures communes observations
│   ├── test_models.py                   # Existant
│   ├── test_workflow_fiche.py           # PHASE 2 - Nouveau
│   ├── test_validations.py              # PHASE 2 - Nouveau
│   ├── test_transcription.py            # PHASE 2 - Nouveau
│   ├── test_saisie_observation.py       # PHASE 4 - Nouveau
│   └── test_celery_tasks.py             # PHASE 3 - Nouveau
│
├── geo/
│   └── test_api_communes.py             # Existant - Excellent
│
└── test_regressions.py                  # PHASE 4 - Nouveau
```

### 6.2 Fixtures Réutilisables

**Créer dans `conftest.py` (racine) :**

```python
@pytest.fixture
def user_observateur(db):
    """Utilisateur avec role observateur"""
    return Utilisateur.objects.create_user(
        username='observateur',
        email='obs@test.com',
        password='TestPass123',
        role='observateur',
        est_valide=True,
        is_active=True
    )

@pytest.fixture
def user_admin(db):
    """Utilisateur avec role administrateur"""
    return Utilisateur.objects.create_user(
        username='admin',
        email='admin@test.com',
        password='TestPass123',
        role='administrateur',
        est_valide=True,
        is_active=True
    )

@pytest.fixture
def user_superuser(db):
    """Superuser"""
    return Utilisateur.objects.create_superuser(
        username='superuser',
        email='super@test.com',
        password='TestPass123'
    )

@pytest.fixture
def fiche_complete(db, user_observateur, espece):
    """Fiche avec tous les objets liés"""
    fiche = FicheObservation.objects.create(
        observateur=user_observateur,
        espece=espece,
        annee=2024
    )
    # Objets liés créés automatiquement par save()
    return fiche
```

### 6.3 Configuration de Coverage

**Mettre à jour `pytest.ini` :**

```ini
[pytest]
DJANGO_SETTINGS_MODULE = observations_nids.settings
python_files = tests.py test_*.py *_tests.py
addopts =
    --cov=.
    --cov-report=html
    --cov-report=term-missing
    --cov-fail-under=80
    --no-cov-on-fail
    -v
    --strict-markers

markers =
    security: Tests de sécurité (authentification, permissions)
    integration: Tests d'intégration (workflow complets)
    unit: Tests unitaires (fonctions isolées)
    slow: Tests lents (> 1 seconde)
```

**Exclure de la couverture (`.coveragerc`) :**

```ini
[run]
omit =
    */migrations/*
    */tests/*
    */__pycache__/*
    */venv/*
    manage.py
    */settings*.py
    */conftest.py

[report]
exclude_lines =
    pragma: no cover
    def __repr__
    raise AssertionError
    raise NotImplementedError
    if __name__ == .__main__.:
    if TYPE_CHECKING:
    @abstractmethod
```

### 6.4 Intégration CI/CD

**Ajouter dans `.github/workflows/tests.yml` :**

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.12'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest-cov

      - name: Run tests
        run: pytest --cov=. --cov-fail-under=80

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          file: ./coverage.xml
```

---

## 7. Tests Prioritaires pour Feature Actuelle

### 7.1 Tests à Ajouter IMMÉDIATEMENT (feature/reinitialisation_mdp)

**Avant de merger la branche actuelle**, implémenter au minimum :

#### Tests Critiques (2-3 heures) :

```python
# accounts/tests/test_password_reset_minimal.py

class TestMotDePasseOublieMinimal:
    def test_email_existant_envoie_email()
    def test_email_inexistant_pas_revelation()
    def test_utilisateur_inactif_ignore()

class TestReinitialiserMotDePasseMinimal:
    def test_token_valide_permet_reset()
    def test_token_invalide_refuse()
    def test_mot_de_passe_court_refuse()
    def test_mots_de_passe_differents_refuse()
    def test_reset_reussi_hash_sauvegarde()

class TestEmailReinitialisation:
    def test_email_contient_lien_valide()
    def test_utilisateur_sans_email_gere()
```

**Estimation : 11 tests essentiels, 2-3 heures**

Ces tests garantissent que la fonctionnalité de réinitialisation de mot de passe est sécurisée avant le déploiement.

---

## 8. Outils et Bonnes Pratiques

### 8.1 Outils de Test Recommandés

| Outil | Usage | Installé |
|-------|-------|----------|
| pytest | Framework de test | ✅ Oui |
| pytest-django | Intégration Django | ✅ Oui |
| pytest-cov | Couverture de code | ✅ Oui |
| factory-boy | Création de fixtures | ❌ Recommandé |
| faker | Données de test | ❌ Recommandé |
| freezegun | Mock de datetime | ❌ Utile pour tokens expirés |
| responses | Mock de requêtes HTTP | ❌ Utile pour API externes |

**Installation recommandée :**

```bash
pip install factory-boy faker freezegun responses
pip freeze > requirements-dev.txt
```

### 8.2 Bonnes Pratiques

#### A. Nommage des Tests

✅ **Bon :**
```python
def test_utilisateur_desactive_ne_peut_pas_login()
def test_token_expire_affiche_erreur()
def test_admin_peut_supprimer_utilisateur()
```

❌ **Mauvais :**
```python
def test_1()
def test_user()
def test_password()
```

#### B. Structure des Tests (AAA Pattern)

```python
def test_exemple():
    # ARRANGE - Préparer les données
    user = Utilisateur.objects.create(username='test')

    # ACT - Exécuter l'action
    user.is_active = False
    user.save()

    # ASSERT - Vérifier le résultat
    assert user.is_active is False
```

#### C. Isolation des Tests

✅ **Chaque test doit :**
- Être indépendant des autres tests
- Ne pas dépendre de l'ordre d'exécution
- Nettoyer ses données (ou utiliser `@pytest.mark.django_db(transaction=True)`)

#### D. Mock des Services Externes

```python
from unittest.mock import patch

@patch('accounts.utils.email_service.EmailService.envoyer_email_reinitialisation_mdp')
def test_email_envoye(mock_send):
    mock_send.return_value = True
    # Test ici
    assert mock_send.called
```

---

## 9. Métriques de Suivi

### 9.1 Indicateurs Clés

| Métrique | Valeur Actuelle | Objectif | Critique |
|----------|-----------------|----------|----------|
| Couverture globale | 40% | 80%+ | ⚠️ |
| Tests totaux | 25 | 174+ | ⚠️ |
| Couverture accounts | 9% | 75%+ | 🔴 CRITIQUE |
| Couverture observations | 28% | 75%+ | ⚠️ |
| Couverture geo | 99% | 99% | ✅ |
| Tests sécurité | 10 | 67+ | 🔴 CRITIQUE |
| Tests intégration | 5 | 50+ | ⚠️ |
| Temps exécution tests | ~45s | < 2min | ✅ |

### 9.2 Tableau de Bord de Progression

**À suivre après chaque phase :**

```bash
# Générer rapport de couverture
pytest --cov=. --cov-report=html

# Ouvrir htmlcov/index.html dans navigateur
# Vérifier les fichiers avec < 80% de couverture
```

**Commandes utiles :**

```bash
# Tests par module
pytest accounts/ -v
pytest observations/ -v

# Tests par marqueur
pytest -m security
pytest -m integration

# Tests avec couverture détaillée
pytest --cov=accounts --cov-report=term-missing

# Tests les plus lents
pytest --durations=10
```

---

## 10. Risques et Mitigation

### 10.1 Risques Identifiés

| Risque | Impact | Probabilité | Mitigation |
|--------|--------|-------------|------------|
| **Failles de sécurité non détectées** | 🔴 Critique | Élevée | Phase 1 prioritaire (57 tests sécurité) |
| **Régression sur features existantes** | 🟠 Majeur | Moyenne | Tests de non-régression + CI/CD |
| **Perte de données utilisateurs** | 🔴 Critique | Faible | Tests intégrité (Phase 2) |
| **Emails non envoyés en production** | 🟠 Majeur | Moyenne | Tests service email + monitoring |
| **Permissions bypassées** | 🔴 Critique | Moyenne | Tests permissions exhaustifs |
| **Temps d'exécution tests trop long** | 🟡 Mineur | Faible | Optimisation fixtures + DB transactionnelle |

### 10.2 Plan de Mitigation

**Sécurité :**
- ✅ Implémenter Phase 1 en priorité
- ✅ Revue de code systématique pour toute modification authentification
- ✅ Tests de pénétration manuels après Phase 1

**Performance :**
- ✅ Utiliser `pytest-xdist` pour parallélisation si > 2 minutes
- ✅ DB SQLite en mémoire pour tests (déjà configuré)
- ✅ Fixtures cached avec `scope="session"` pour données statiques

**Maintenabilité :**
- ✅ Documentation inline des tests complexes
- ✅ Refactoring des tests dupliqués avec fixtures
- ✅ Nommage explicite (français, cohérent avec le projet)

---

## 11. Conclusion et Recommandations

### 11.1 Constats Principaux

1. **✅ Points Forts :**
   - Module `geo` excellemment testé (99%)
   - Tests existants bien structurés et maintenables
   - Utilisation correcte de pytest-django
   - Fixtures de base déjà en place

2. **⚠️ Points d'Amélioration :**
   - **Couverture critique insuffisante** sur `accounts` (9%) et `observations` (28%)
   - **Aucun test sur fonctionnalités récemment ajoutées** (réinitialisation mdp, soft delete)
   - **Risques de sécurité élevés** : permissions, authentification, validations
   - **Manque de tests d'intégration** pour workflows complets

3. **🔴 Urgences :**
   - **Tester la réinitialisation de mot de passe AVANT merge** (11 tests minimum)
   - Tester le soft delete et les permissions admin (18 tests)
   - Ajouter tests de contrainte email unique (7 tests)

### 11.2 Recommandations Immédiates

**AVANT de merger `feature/reinitialisation_mdp` :**

1. ✅ **Implémenter les 11 tests critiques de password reset** (2-3h)
2. ✅ **Tester manuellement en production simulée** (SMTP réel, HTTPS)
3. ✅ **Revue de code sécurité** par un pair

**Cette semaine :**

4. ✅ **Compléter Phase 1** (57 tests sécurité, 13-18h)
5. ✅ **Configurer CI/CD** avec seuil 80% de couverture
6. ✅ **Documenter procédure de tests** pour contributeurs

**Ce mois :**

7. ✅ **Implémenter Phases 2 et 3** (78 tests, 26-33h)
8. ✅ **Former l'équipe** aux bonnes pratiques de tests
9. ✅ **Atteindre 80% de couverture globale**

### 11.3 Bénéfices Attendus

Après implémentation complète du plan :

- **Sécurité renforcée** : Détection précoce de failles (authentification, permissions)
- **Confiance accrue** : Déploiements sans régression
- **Maintenance facilitée** : Refactoring sécurisé grâce aux tests
- **Documentation vivante** : Tests comme spécifications exécutables
- **Qualité professionnelle** : 80%+ couverture = standard industriel

**Investissement total : 45-59 heures**
**ROI : Économie de dizaines d'heures de debugging et correction de bugs en production**

---

## 12. Annexes

### 12.1 Commandes Utiles

```bash
# Lancer tous les tests
pytest

# Tests avec couverture
pytest --cov=. --cov-report=html

# Tests d'un module spécifique
pytest accounts/
pytest observations/

# Tests par fichier
pytest accounts/tests/test_password_reset.py

# Tests par classe
pytest accounts/tests.py::TestNotificationModel

# Tests par fonction
pytest accounts/tests.py::TestNotificationModel::test_notification_creation

# Tests avec output détaillé
pytest -vv

# Tests avec print() visible
pytest -s

# Tests les plus lents
pytest --durations=10

# Tests en parallèle (si pytest-xdist installé)
pytest -n auto

# Tests avec marqueur
pytest -m security

# Générer rapport XML pour CI
pytest --cov=. --cov-report=xml

# Vérifier que la couverture est >= 80%
pytest --cov=. --cov-fail-under=80
```

### 12.2 Structure Complète du Projet de Tests

```
observations_nids/
├── accounts/
│   ├── tests/
│   │   ├── __init__.py
│   │   ├── conftest.py
│   │   ├── test_models.py (✅ existant - 20 tests)
│   │   ├── test_password_reset.py (❌ à créer - Phase 1)
│   │   ├── test_soft_delete.py (❌ à créer - Phase 1)
│   │   ├── test_permissions.py (❌ à créer - Phase 1)
│   │   ├── test_email_uniqueness.py (❌ à créer - Phase 1)
│   │   ├── test_email_service_extended.py (❌ à créer - Phase 3)
│   │   └── test_recherche_filtres.py (❌ à créer - Phase 3)
│   └── ...
├── observations/
│   ├── tests/
│   │   ├── __init__.py
│   │   ├── conftest.py
│   │   ├── test_models.py (✅ existant - 9 tests)
│   │   ├── test_workflow_fiche.py (❌ à créer - Phase 2)
│   │   ├── test_validations.py (❌ à créer - Phase 2)
│   │   ├── test_transcription.py (❌ à créer - Phase 2)
│   │   ├── test_saisie_observation.py (❌ à créer - Phase 4)
│   │   └── test_celery_tasks.py (❌ à créer - Phase 3)
│   └── ...
├── geo/
│   └── tests/
│       ├── __init__.py
│       └── test_api_communes.py (✅ existant - 13 tests - 99% couverture)
├── conftest.py (✅ existant - fixtures globales)
├── pytest.ini (✅ existant - configuration)
├── .coveragerc (❌ à créer - configuration couverture)
└── test_regressions.py (❌ à créer - Phase 4)
```

### 12.3 Checklist de Merge de Branche

**Avant de merger toute feature branch :**

- [ ] ✅ Tous les tests passent (`pytest`)
- [ ] ✅ Linting propre (`ruff check`)
- [ ] ✅ Formatage correct (`ruff format`)
- [ ] ✅ Type checking OK (`mypy`)
- [ ] ✅ Couverture >= 80% sur code modifié
- [ ] ✅ Tests ajoutés pour nouvelles fonctionnalités
- [ ] ✅ Tests de régression si bug fix
- [ ] ✅ Documentation mise à jour
- [ ] ✅ Tests manuels en environnement de staging
- [ ] ✅ Revue de code par un pair (si disponible)

### 12.4 Ressources

**Documentation officielle :**
- pytest : https://docs.pytest.org/
- pytest-django : https://pytest-django.readthedocs.io/
- coverage.py : https://coverage.readthedocs.io/

**Bonnes pratiques :**
- Django Testing Best Practices : https://docs.djangoproject.com/en/5.2/topics/testing/
- AAA Pattern : http://wiki.c2.com/?ArrangeActAssert
- Test Pyramid : https://martinfowler.com/articles/practical-test-pyramid.html

---

**Document généré le : 19 octobre 2025**
**Version : 1.0**
**Auteur : Claude Code**
**Statut : FINAL - Prêt pour implémentation**
