# Documentation - Gestion des utilisateurs

## Vue d'ensemble

Ce document décrit toutes les fonctionnalités de gestion des utilisateurs dans l'application Observations Nids, incluant la création, modification, validation, réinitialisation de mot de passe et suppression (soft delete).

---

## Table des matières

1. [Workflow d'inscription](#workflow-dinscription)
2. [Rôles et permissions](#rôles-et-permissions)
3. [Gestion des comptes (administrateurs)](#gestion-des-comptes-administrateurs)
4. [Réinitialisation de mot de passe](#réinitialisation-de-mot-de-passe)
5. [Suppression d'utilisateurs (Soft Delete)](#suppression-dutilisateurs-soft-delete)
6. [Contraintes et validations](#contraintes-et-validations)
7. [Notifications et emails](#notifications-et-emails)
8. [Sécurité](#sécurité)

---

## Workflow d'inscription

### Inscription publique

Les nouveaux utilisateurs peuvent demander un compte via la page d'inscription publique.

**URL** : `/accounts/inscription-publique/`

**Processus** :

```
1. L'utilisateur remplit le formulaire d'inscription
   ├─ Nom d'utilisateur (unique)
   ├─ Email (unique)
   ├─ Prénom
   ├─ Nom
   ├─ Mot de passe (min 8 caractères)
   └─ Confirmation du mot de passe

2. Soumission du formulaire
   └─> Compte créé avec :
       ├─ est_valide = False
       ├─ is_active = False
       └─ role = 'observateur'

3. Notifications envoyées
   ├─ Notification in-app pour tous les administrateurs
   └─ Email à l'administrateur principal (ADMIN_EMAIL)

4. Redirection vers la page de login
   └─> Message : "Votre demande d'inscription a été enregistrée..."
```

**Fichiers impliqués** :
- Vue : `accounts/views/auth.py::inscription_publique()`
- Template : `accounts/templates/accounts/inscription_publique.html`
- Formulaire : `accounts/forms.py::UtilisateurCreationForm`

---

## Rôles et permissions

### Types de rôles

Le système utilise 3 rôles définis dans `core/constants.py::ROLE_CHOICES` :

| Rôle | Valeur DB | Permissions |
|------|-----------|-------------|
| **Observateur** | `observateur` | Créer et modifier ses propres observations |
| **Correcteur** | `correcteur` | Corriger les observations des autres utilisateurs |
| **Administrateur** | `administrateur` | Accès complet à toutes les fonctionnalités |

### Permissions détaillées

#### Observateur (rôle par défaut)
- ✅ Créer de nouvelles fiches d'observation
- ✅ Modifier ses propres fiches (statut NOUVEAU ou EN_EDITION)
- ✅ Consulter toutes les observations
- ✅ Soumettre ses fiches pour correction
- ✅ Voir son profil
- ❌ Modifier les fiches d'autres utilisateurs
- ❌ Accéder à l'interface d'administration

#### Correcteur
Toutes les permissions de l'observateur, plus :
- ✅ Corriger les fiches en statut EN_COURS
- ✅ Modifier les fiches de tous les utilisateurs
- ✅ Accéder à l'outil de transcription

#### Administrateur
Toutes les permissions, plus :
- ✅ Gérer les utilisateurs (créer, modifier, valider, supprimer)
- ✅ Voir la liste de tous les utilisateurs
- ✅ Promouvoir des utilisateurs
- ✅ Accéder aux statistiques avancées

---

## Gestion des comptes (administrateurs)

### Liste des utilisateurs

**URL** : `/accounts/utilisateurs/`
**Permission requise** : Administrateur

**Fonctionnalités** :

#### Filtres disponibles

1. **Recherche textuelle**
   - Recherche dans : username, first_name, last_name, email
   - Insensible à la casse

2. **Filtre par rôle**
   - Tous les rôles
   - Observateurs
   - Administrateurs

3. **Filtre par validation**
   - Tous
   - Validés
   - En attente (nouveaux comptes)

4. **Filtre par statut** ⭐ NOUVEAU
   - Tous les statuts
   - Actifs uniquement
   - Inactifs uniquement (utilisateurs supprimés)

#### Affichage des utilisateurs

**Colonnes affichées** :
- Nom d'utilisateur (avec badge "Nouveau" si non validé)
- Nom
- Prénom
- Email
- Rôle
- Validation (Validé / En attente)
- Statut (Actif / Inactif)
- Actions

**Indicateurs visuels** :
- 🟡 Fond jaune : Compte en attente de validation
- 🔘 Grisé + barré : Compte inactif (supprimé)
- Badge compteur : Nombre de demandes en attente

#### Actions disponibles

Pour chaque utilisateur :

1. **Valider** (si non validé)
   - Active le compte (is_active = True)
   - Marque comme validé (est_valide = True)
   - Envoie un email de confirmation à l'utilisateur
   - Crée une notification pour l'utilisateur
   - Marque les notifications admin comme lues

2. **Modifier**
   - Formulaire d'édition des informations
   - Changement de rôle possible
   - Modification email, nom, prénom

3. **Supprimer** (si actif) ⭐ SOFT DELETE
   - Désactive le compte (is_active = False)
   - Conserve toutes les données
   - Affichage en grisé dans la liste
   - Action réversible
   - Voir section [Suppression d'utilisateurs](#suppression-dutilisateurs-soft-delete)

4. **Réactiver** (si inactif)
   - Réactive le compte (is_active = True)
   - L'utilisateur peut à nouveau se connecter
   - Retour à l'affichage normal

### Création manuelle d'utilisateurs

**URL** : `/accounts/utilisateurs/creer/`
**Permission requise** : Administrateur

Les administrateurs peuvent créer directement des comptes validés :
- Compte créé avec est_valide = True
- Compte actif immédiatement (is_active = True)
- Rôle choisi par l'administrateur

### Modification d'utilisateurs

**URL** : `/accounts/utilisateurs/<user_id>/modifier/`
**Permission requise** : Administrateur

**Champs modifiables** :
- Nom d'utilisateur
- Email
- Prénom
- Nom
- Rôle
- Statut de validation
- Statut actif/inactif

### Détails d'un utilisateur

**URL** : `/accounts/utilisateurs/<user_id>/detail/`
**Permission requise** : Administrateur

**Informations affichées** :
- Informations personnelles
- Nombre d'observations créées
- Liste des fiches d'observation
- Historique des actions

**Chargement AJAX** :
- Les détails se chargent sans rechargement de page
- Clic sur une ligne de la liste des utilisateurs

---

## Fonctionnalité de réinitialisation de mot de passe

### Vue d'ensemble

Cette fonctionnalité permet aux utilisateurs qui ont oublié leur mot de passe de le réinitialiser de manière sécurisée via email.

### Workflow utilisateur

```
1. Page de login
   └─> Clic sur "Mot de passe oublié ?"
       └─> 2. Formulaire de demande de réinitialisation
           ├─> Saisie de l'email
           └─> Envoi du formulaire
               └─> 3. Email de réinitialisation envoyé
                   ├─> Lien avec token (valide 24h)
                   └─> Clic sur le lien
                       └─> 4. Formulaire nouveau mot de passe
                           ├─> Saisie du nouveau mot de passe
                           ├─> Confirmation du mot de passe
                           └─> Enregistrement
                               └─> 5. Redirection vers login
```

### Composants implémentés

#### 1. Formulaires (`accounts/forms.py`)

##### `MotDePasseOublieForm`
- **Champ** : `email` (EmailField)
- **Validation** : Format email valide
- **Usage** : Page de demande de réinitialisation

##### `NouveauMotDePasseForm`
- **Champs** :
  - `password1` : Nouveau mot de passe
  - `password2` : Confirmation du mot de passe
- **Validations** :
  - Minimum 8 caractères
  - Les deux mots de passe doivent correspondre

#### 2. Vues (`accounts/views/auth.py`)

##### `mot_de_passe_oublie(request)`
- **URL** : `/accounts/mot-de-passe-oublie/`
- **Méthode** : GET et POST
- **Authentification** : Non requise
- **Fonctionnement** :
  1. Affiche le formulaire de saisie d'email
  2. Vérifie si l'email existe dans la base de données
  3. Génère un token sécurisé (Django `default_token_generator`)
  4. Encode l'ID utilisateur (base64)
  5. Envoie l'email avec le lien de réinitialisation
  6. **Sécurité** : Message identique que l'email existe ou non (évite l'énumération d'emails)

##### `reinitialiser_mot_de_passe(request, uidb64, token)`
- **URL** : `/accounts/reinitialiser-mot-de-passe/<uidb64>/<token>/`
- **Méthode** : GET et POST
- **Authentification** : Non requise
- **Fonctionnement** :
  1. Décode l'UID et récupère l'utilisateur
  2. Vérifie la validité du token
  3. Si valide : affiche le formulaire de nouveau mot de passe
  4. Enregistre le nouveau mot de passe avec hachage
  5. Redirige vers la page de login

#### 3. Service Email (`accounts/utils/email_service.py`)

##### `EmailService.envoyer_email_reinitialisation_mdp(utilisateur, uid, token)`
- **Template** : `accounts/emails/reinitialisation_mot_de_passe.html`
- **Sujet** : "[Observations Nids] Réinitialisation de votre mot de passe"
- **Contenu** :
  - Bouton avec lien de réinitialisation
  - Lien copié/collable en fallback
  - Avertissement de validité (24h)
  - Instructions de sécurité
- **Protocole** : HTTPS en production, HTTP en développement

#### 4. Templates

##### `accounts/templates/accounts/mot_de_passe_oublie.html`
- Formulaire de saisie d'email
- Bouton d'envoi
- Lien de retour vers la page de login

##### `accounts/templates/accounts/reinitialiser_mot_de_passe.html`
- Deux états :
  - **Lien valide** : Formulaire de nouveau mot de passe
  - **Lien invalide/expiré** : Message d'erreur avec option de redemander un lien

##### `accounts/templates/accounts/emails/reinitialisation_mot_de_passe.html`
- Email HTML responsive
- Style inline pour compatibilité email
- Bouton CTA principal
- Lien de fallback
- Section d'avertissements

#### 5. URLs (`accounts/urls.py`)

```python
# Demande de réinitialisation
path('mot-de-passe-oublie/', auth.mot_de_passe_oublie, name='mot_de_passe_oublie')

# Réinitialisation avec token
path('reinitialiser-mot-de-passe/<uidb64>/<token>/',
     auth.reinitialiser_mot_de_passe,
     name='reinitialiser_mot_de_passe')
```

#### 6. Modification du template de login (`observations/templates/login.html`)

Ajout d'un lien "Mot de passe oublié ?" sous le formulaire de connexion.

### Sécurité

#### Mesures implémentées

1. **Token sécurisé**
   - Utilise `django.contrib.auth.tokens.default_token_generator`
   - Token unique basé sur le timestamp et le hash du mot de passe
   - Invalide automatiquement après changement de mot de passe

2. **Durée de validité**
   - Les tokens expirent après 24 heures
   - Configurable via `PASSWORD_RESET_TIMEOUT` dans settings

3. **Encodage sécurisé**
   - UID utilisateur encodé en base64 URL-safe
   - Empêche la manipulation directe des IDs

4. **Protection contre l'énumération**
   - Message identique que l'email existe ou non
   - Logs séparés pour le monitoring (email inexistant)

5. **Validation du mot de passe**
   - Minimum 8 caractères
   - Vérification de correspondance password1/password2
   - Hachage Django (`make_password`)

6. **Compte actif uniquement**
   - La réinitialisation ne fonctionne que pour les comptes `is_active=True`

### Configuration requise

#### Variables d'environnement

```bash
# .env ou settings_local.py
ADMIN_EMAIL=admin@example.com          # Pour notifications admin
DEFAULT_FROM_EMAIL=noreply@example.com # Email expéditeur
ALLOWED_HOSTS=["localhost", "example.com"]  # Pour construire les URLs
```

#### Configuration SMTP

L'envoi d'emails nécessite une configuration SMTP dans Django :

```python
# settings.py
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.example.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'your-email@example.com'
EMAIL_HOST_PASSWORD = 'your-password'
```

**En développement**, utilisez le backend console :
```python
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
```

### Tests

#### Test manuel du workflow

1. **Demande de réinitialisation**
   ```
   1. Aller sur http://localhost:8000/auth/login/
   2. Cliquer sur "Mot de passe oublié ?"
   3. Saisir un email existant
   4. Vérifier le message de confirmation
   ```

2. **Réception de l'email**
   ```
   En mode console (développement) :
   - Vérifier la console Django pour l'email
   - Copier le lien de réinitialisation

   En production :
   - Vérifier la boîte email
   ```

3. **Réinitialisation**
   ```
   1. Cliquer sur le lien (ou le copier dans le navigateur)
   2. Saisir un nouveau mot de passe (min 8 caractères)
   3. Confirmer le mot de passe
   4. Valider le formulaire
   5. Vérifier la redirection vers login
   ```

4. **Connexion**
   ```
   1. Se connecter avec le nouveau mot de passe
   2. Vérifier l'accès au compte
   ```

#### Test des cas limites

1. **Email inexistant**
   - Saisir un email qui n'existe pas
   - Vérifier que le message reste identique (sécurité)

2. **Lien expiré**
   - Utiliser un lien de plus de 24h
   - Vérifier le message d'erreur approprié

3. **Token invalide**
   - Modifier manuellement le token dans l'URL
   - Vérifier le message d'erreur

4. **Mot de passe trop court**
   - Saisir moins de 8 caractères
   - Vérifier le message de validation

5. **Mots de passe non correspondants**
   - Saisir deux mots de passe différents
   - Vérifier le message d'erreur

### Monitoring et logs

#### Événements logués

```python
# Email de réinitialisation envoyé
logger.info(f"Email de réinitialisation envoyé à {email}")

# Tentative pour email inexistant
logger.warning(f"Tentative de réinitialisation pour email inexistant : {email}")

# Réinitialisation réussie
logger.info(f"Mot de passe réinitialisé pour {utilisateur.username}")

# Lien invalide ou expiré
logger.warning(f"Tentative de réinitialisation avec lien invalide ou expiré")
```

### Surveillance recommandée

- **Taux de réinitialisation** : Nombre de demandes par jour
- **Taux d'échec** : Liens invalides/expirés
- **Tentatives suspectes** : Multiples tentatives pour le même email

### Extensions futures possibles

1. **Limitation de taux (Rate limiting)**
   - Limiter les demandes à X par email par heure
   - Prévenir les abus

2. **Authentification à deux facteurs (2FA)**
   - Code par email ou SMS
   - Couche de sécurité supplémentaire

3. **Historique des changements**
   - Tracer les changements de mot de passe
   - Notifications lors des changements

4. **Expiration personnalisée**
   - Durée de validité configurable
   - Différente selon le rôle utilisateur

5. **Questions de sécurité**
   - Questions secrètes en complément
   - Alternative en cas d'email inaccessible

### Dépendances

#### Paquets Python
- Django >= 5.0 (inclus dans le projet)
- Pas de dépendances supplémentaires

#### Configuration Django requise
- `django.contrib.auth` dans `INSTALLED_APPS`
- `django.contrib.sessions` pour les messages
- `django.contrib.messages` pour les notifications

### Compatibilité

- **Django** : 5.x
- **Python** : 3.10+
- **Navigateurs** : Tous navigateurs modernes
- **Email clients** : HTML responsive compatible

---

**Date de création** : 19 octobre 2025
**Auteur** : JM Schneider avec Claude Code
**Version** : 1.0
**Branche** : `feature/reinitialisation_mdp`

---

## Suppression d'utilisateurs (Soft Delete)

### Concept

**Soft Delete** = Suppression "douce" sans perte de données

- L'utilisateur est **désactivé** (is_active = False)
- Toutes ses données **restent dans le système**
- Ses observations **restent accessibles**
- Action **100% réversible**
- Aucune suppression définitive depuis l'interface web

### Interface utilisateur

#### Bouton "Supprimer"

**Apparence** :
- Icône : `trash-alt` (poubelle)
- Couleur : Rouge (`btn-danger`)
- Visible uniquement pour les utilisateurs actifs

**Message de confirmation** :
```
⚠️ ATTENTION

Voulez-vous vraiment supprimer cet utilisateur ?

L'utilisateur [username] ne pourra plus se connecter.
Ses observations resteront dans le système.

Cette action est réversible via le bouton 'Réactiver'.
```

#### Affichage des utilisateurs supprimés

**Style CSS** :
```css
.user-inactive {
    opacity: 0.5;                    /* Semi-transparent */
    background-color: #f8f9fa;       /* Fond gris clair */
}

.user-inactive td {
    color: #6c757d;                  /* Texte gris */
    text-decoration: line-through;   /* Texte barré */
}
```

**Comportement** :
- Ligne complète en grisé
- Texte barré
- Badge "Inactif" en rouge
- Survol possible (opacity: 0.7)
- Boutons et badges restent visibles (opacity: 1)

#### Bouton "Réactiver"

**Apparence** :
- Icône : `user-check`
- Couleur : Vert (`btn-success`)
- Visible uniquement pour les utilisateurs inactifs

**Message de confirmation** :
```
Voulez-vous réactiver l'utilisateur [username] ?

Il pourra à nouveau se connecter à l'application.
```

### Workflow technique

**Suppression** :
```python
@login_required
@user_passes_test(est_admin)
def desactiver_utilisateur(request, user_id):
    utilisateur = get_object_or_404(Utilisateur, id=user_id)
    utilisateur.is_active = False
    utilisateur.save()

    # Log de l'action
    logger.info(f"Utilisateur {utilisateur.username} supprimé (soft delete) par {request.user.username}")

    # Message de succès explicite
    messages.success(request,
        f"L'utilisateur {utilisateur.username} a été supprimé. "
        f"Il ne peut plus se connecter mais ses données sont conservées. "
        f"Vous pouvez le réactiver à tout moment."
    )
```

**Réactivation** :
```python
@login_required
@user_passes_test(est_admin)
def activer_utilisateur(request, user_id):
    utilisateur = get_object_or_404(Utilisateur, id=user_id)
    utilisateur.is_active = True
    utilisateur.save()

    # Log de l'action
    logger.info(f"Utilisateur {utilisateur.username} réactivé par {request.user.username}")

    messages.success(request,
        f"L'utilisateur {utilisateur.username} a été réactivé. "
        f"Il peut à nouveau se connecter à l'application."
    )
```

### Impact sur les données

**Ce qui est conservé** :
- ✅ Informations utilisateur (username, email, nom, prénom)
- ✅ Toutes les observations créées
- ✅ Historique des modifications
- ✅ Notifications
- ✅ Relations ForeignKey

**Ce qui est affecté** :
- ❌ Connexion impossible (is_active = False)
- ❌ Apparaît comme "Inactif" dans les listes
- ℹ️ Les observations restent attribuées à cet utilisateur

### Suppression définitive (admin Django)

**Interface admin Django** : `/admin/accounts/utilisateur/`

**Cas d'usage** :
- Nettoyage de comptes de test
- Suppression suite à demande RGPD
- Cas exceptionnels uniquement

**Conséquences** :
- ⚠️ Suppression définitive de toutes les données
- ⚠️ CASCADE ou PROTECT selon les ForeignKey
- ⚠️ Peut échouer si des données liées existent

**Recommandation** : Utiliser uniquement en dernier recours. Préférer le soft delete.

---

## Contraintes et validations

### Email unique

**Contrainte DB** : `unique=True` sur le champ email

**Implémentation** :
```python
# accounts/models.py
class Utilisateur(AbstractUser):
    email = models.EmailField(
        "adresse email",
        unique=True,
        error_messages={
            'unique': "Un utilisateur avec cette adresse email existe déjà.",
        },
    )
```

**Migration** : `accounts/migrations/0003_email_unique_et_lien_default.py`

**Bénéfices** :
- Empêche les doublons accidentels
- Simplifie la réinitialisation de mot de passe
- Intégrité des données garantie au niveau DB
- Message d'erreur clair en français

### Validation du mot de passe

**Règles Django par défaut** (configurables dans `settings.py`) :

1. **UserAttributeSimilarityValidator**
   - Le mot de passe ne doit pas ressembler aux attributs de l'utilisateur

2. **MinimumLengthValidator**
   - Minimum 8 caractères (par défaut)

3. **CommonPasswordValidator**
   - Rejet des mots de passe trop courants

4. **NumericPasswordValidator**
   - Le mot de passe ne peut pas être entièrement numérique

**Validation supplémentaire dans les formulaires** :
```python
# accounts/forms.py
class NouveauMotDePasseForm(forms.Form):
    def clean_password1(self):
        password = self.cleaned_data.get('password1')
        if password and len(password) < 8:
            raise forms.ValidationError("Le mot de passe doit contenir au moins 8 caractères.")
        return password

    def clean_password2(self):
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Les deux mots de passe ne correspondent pas.")
        return password2
```

### Validation de l'email

**Format** : Validation automatique Django (EmailField)
- Format email valide requis
- Longueur max : 254 caractères (norme RFC)

**Unicité** : Vérifiée au niveau DB et au niveau formulaire

---

## Notifications et emails

### Système de notifications in-app

**Modèle** : `accounts.models.Notification`

**Types de notifications** :
- `demande_compte` : Nouvelle demande d'inscription
- `compte_valide` : Compte validé par un admin
- `compte_refuse` : Compte refusé
- `info` : Information générale
- `warning` : Avertissement

**Workflow des notifications** :

```
Demande d'inscription
  └─> Notification créée pour tous les administrateurs actifs
      ├─ Type : demande_compte
      ├─ Titre : "Nouvelle demande de compte : [username]"
      ├─ Message : "[Prénom] [Nom] ([email]) a demandé un compte."
      ├─ Lien : /accounts/utilisateurs/[id]/detail/
      └─ utilisateur_concerne : référence vers l'utilisateur

Validation du compte
  └─> Notification créée pour l'utilisateur
      ├─ Type : compte_valide
      ├─ Titre : "Votre compte a été validé"
      ├─ Message : "Votre demande de compte a été approuvée..."
      └─ Lien : /login/
  └─> Notifications admin marquées comme lues
```

### Emails

**Service centralisé** : `accounts/utils/email_service.py::EmailService`

#### Email 1 : Nouvelle demande de compte (à l'admin)

**Destinataire** : `ADMIN_EMAIL` (configuré dans .env)
**Sujet** : `[Observations Nids] Nouvelle demande de compte - [username]`
**Template** : `accounts/templates/accounts/emails/nouvelle_demande_admin.html`

**Contenu** :
- Informations sur le demandeur
- Lien direct vers le profil utilisateur
- Actions suggérées (valider/refuser)

#### Email 2 : Compte validé (à l'utilisateur)

**Destinataire** : Email de l'utilisateur
**Sujet** : `[Observations Nids] Votre compte a été validé`
**Template** : `accounts/templates/accounts/emails/compte_valide_utilisateur.html`

**Contenu** :
- Confirmation de validation
- Lien vers la page de connexion
- Instructions de première connexion

#### Email 3 : Réinitialisation de mot de passe

**Destinataire** : Email de l'utilisateur
**Sujet** : `[Observations Nids] Réinitialisation de votre mot de passe`
**Template** : `accounts/templates/accounts/emails/reinitialisation_mot_de_passe.html`

**Contenu** :
- Bouton CTA avec lien de réinitialisation
- Lien copié/collable en fallback
- Avertissement de validité (24h)
- Instructions de sécurité

### Configuration email

**Développement** (console backend) :
```bash
# .env
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
```
Les emails s'affichent dans la console du serveur Django.

**Production** (SMTP Gmail) :
```bash
# .env
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=observationnids@gmail.com
EMAIL_HOST_PASSWORD=[mot de passe d'application]
DEFAULT_FROM_EMAIL=Observations Nids <observationnids@gmail.com>
ADMIN_EMAIL=schneider.jm@free.fr
```

**Basculer entre les modes** : Commenter/décommenter la ligne EMAIL_BACKEND dans `.env`

---

## Sécurité

### Authentification

**Backend** : Django `AuthenticationBackend` par défaut
- Hachage sécurisé des mots de passe (PBKDF2 par défaut)
- Protection CSRF sur tous les formulaires
- Sessions sécurisées

### Autorisation

**Décorateurs utilisés** :
```python
@login_required                    # Authentification requise
@user_passes_test(est_admin)       # Administrateur requis
@user_passes_test(est_superuser)   # Superuser requis (Django)
```

**Mixins pour les vues class-based** :
```python
LoginRequiredMixin      # Authentification requise
UserPassesTestMixin     # Test personnalisé (est_admin)
```

### Protection contre les attaques

**1. Énumération d'utilisateurs**
- Messages identiques que l'email existe ou non (réinitialisation mdp)
- Pas de différenciation dans les erreurs de login

**2. Brute force**
- Pas de limitation de taux implémentée (à considérer)
- Recommandation : Ajouter django-ratelimit pour production

**3. CSRF (Cross-Site Request Forgery)**
- Token CSRF sur tous les formulaires POST
- Middleware CSRF actif

**4. XSS (Cross-Site Scripting)**
- Templates Django avec échappement automatique
- Validation des inputs utilisateur

**5. SQL Injection**
- ORM Django (requêtes paramétrées)
- Pas de requêtes SQL brutes

### Logs et traçabilité

**Actions loguées** :
```python
# Inscription
logger.info(f"Nouvelle demande d'inscription reçue : {username} ({email})")

# Validation
logger.info(f"Compte validé pour {username} par {admin.username}")

# Réinitialisation mdp
logger.info(f"Email de réinitialisation envoyé à {email}")
logger.warning(f"Tentative de réinitialisation pour email inexistant : {email}")
logger.info(f"Mot de passe réinitialisé pour {username}")

# Suppression/Réactivation
logger.info(f"Utilisateur {username} supprimé (soft delete) par {admin.username}")
logger.info(f"Utilisateur {username} réactivé par {admin.username}")
```

**Fichiers de logs** : Configurés dans `settings.py::LOGGING`
- `django_debug.log` : Logs généraux
- Rotation automatique (5 fichiers × 5 MB)

### Bonnes pratiques implémentées

✅ **Principe du moindre privilège**
- Rôles bien définis (observateur < correcteur < administrateur)
- Permissions granulaires

✅ **Défense en profondeur**
- Validation au niveau formulaire
- Contraintes au niveau DB
- Vérifications dans les vues

✅ **Soft delete par défaut**
- Aucune suppression définitive depuis l'interface web
- Toutes les données préservées
- Traçabilité complète

✅ **Audibilité**
- Logs détaillés de toutes les actions sensibles
- Traçabilité des modifications utilisateurs

---

## Fichiers et composants

### Structure des fichiers

```
accounts/
├── models.py                    # Modèle Utilisateur + Notification
├── forms.py                     # Formulaires (création, modification, mdp)
├── urls.py                      # Configuration des URLs
├── views/
│   ├── auth.py                  # Vues d'authentification et gestion utilisateurs
│   └── admin_views.py           # Vues administration (si séparées)
├── utils/
│   └── email_service.py         # Service centralisé d'envoi d'emails
├── templates/accounts/
│   ├── liste_utilisateurs.html  # Liste des utilisateurs (admin)
│   ├── creer_utilisateur.html   # Formulaire création
│   ├── modifier_utilisateur.html # Formulaire modification
│   ├── inscription_publique.html # Inscription publique
│   ├── mon_profil.html          # Profil utilisateur connecté
│   ├── user_detail.html         # Détails utilisateur (admin)
│   ├── mot_de_passe_oublie.html # Demande réinitialisation
│   ├── reinitialiser_mot_de_passe.html # Nouveau mot de passe
│   └── emails/
│       ├── nouvelle_demande_admin.html
│       ├── compte_valide_utilisateur.html
│       └── reinitialisation_mot_de_passe.html
└── migrations/
    ├── 0001_initial.py
    ├── 0002_notification.py
    └── 0003_email_unique_et_lien_default.py

observations/templates/
└── login.html                   # Page de connexion (avec lien mdp oublié)
```

### URLs configurées

```python
# accounts/urls.py
urlpatterns = [
    # Gestion des utilisateurs (admin)
    path('utilisateurs/', ListeUtilisateursView.as_view(), name='liste_utilisateurs'),
    path('utilisateurs/creer/', creer_utilisateur, name='creer_utilisateur'),
    path('utilisateurs/<int:user_id>/modifier/', modifier_utilisateur, name='modifier_utilisateur'),
    path('utilisateurs/<int:user_id>/desactiver/', desactiver_utilisateur, name='desactiver_utilisateur'),
    path('utilisateurs/<int:user_id>/activer/', activer_utilisateur, name='activer_utilisateur'),
    path('utilisateurs/<int:user_id>/detail/', detail_utilisateur, name='detail_utilisateur'),
    path('utilisateurs/<int:user_id>/valider/', valider_utilisateur, name='valider_utilisateur'),

    # Profil
    path('mon-profil/', mon_profil, name='mon_profil'),

    # Inscription publique
    path('inscription-publique/', inscription_publique, name='inscription_publique'),

    # Réinitialisation mot de passe
    path('mot-de-passe-oublie/', mot_de_passe_oublie, name='mot_de_passe_oublie'),
    path('reinitialiser-mot-de-passe/<uidb64>/<token>/', reinitialiser_mot_de_passe, name='reinitialiser_mot_de_passe'),

    # Fonctionnalités d'urgence
    path('urgence/promouvoir-administrateur/', promouvoir_administrateur, name='promouvoir_administrateur'),
]
```

---

## Évolutions futures possibles

### Court terme

1. **Rate limiting**
   - Limiter les tentatives de connexion
   - Limiter les demandes de réinitialisation de mot de passe
   - Package recommandé : `django-ratelimit`

2. **Amélioration des notifications**
   - Badge de compteur dans la navbar
   - Notifications temps réel (websockets)
   - Historique des notifications

3. **Export des utilisateurs**
   - Export CSV/Excel de la liste
   - Filtres avancés

### Moyen terme

4. **Authentification à deux facteurs (2FA)**
   - Code par email ou SMS
   - TOTP (Google Authenticator)
   - Package recommandé : `django-otp`

5. **Sessions avancées**
   - Gestion des sessions actives
   - Déconnexion à distance
   - Historique des connexions

6. **Anonymisation RGPD**
   - Fonction d'anonymisation des données
   - Export des données utilisateur
   - Suppression conforme RGPD

### Long terme

7. **OAuth / SSO**
   - Connexion via Google, GitHub, etc.
   - Package recommandé : `django-allauth`

8. **Audit complet**
   - Historique détaillé de toutes les modifications
   - Timeline des actions utilisateur
   - Package recommandé : `django-auditlog`

9. **Permissions granulaires**
   - Permissions au niveau des objets
   - Groupes d'utilisateurs
   - Package recommandé : `django-guardian`

---

## Troubleshooting

### Problèmes courants

#### "Un utilisateur avec cette adresse email existe déjà"

**Cause** : Contrainte d'unicité sur le champ email

**Solutions** :
1. Utiliser un autre email
2. Si c'est votre email, utiliser "Mot de passe oublié"
3. Contacter un administrateur pour vérifier les doublons

**Script de diagnostic** : `check_duplicate_emails.py` (racine du projet)

#### "DisallowedHost" en production

**Cause** : L'IP/domaine n'est pas dans ALLOWED_HOSTS

**Solution** : Ajouter dans `.env`
```bash
ALLOWED_HOSTS=["localhost","127.0.0.1","votre-domaine.com","votre-ip"]
```

#### Email non reçu

**Causes possibles** :
1. EMAIL_BACKEND en mode console (développement)
2. Mauvaise configuration SMTP
3. Email dans les spams

**Diagnostic** :
```bash
# Vérifier le backend
python -c "from django.conf import settings; print(settings.EMAIL_BACKEND)"

# Tester l'envoi d'email
python manage.py shell
>>> from django.core.mail import send_mail
>>> send_mail('Test', 'Message test', 'from@example.com', ['to@example.com'])
```

#### Utilisateur ne peut pas se connecter après validation

**Vérifications** :
1. `is_active = True` ?
2. `est_valide = True` ?
3. Mot de passe correct ?
4. Compte non supprimé (soft delete) ?

**Script de vérification** :
```python
python manage.py shell
>>> from accounts.models import Utilisateur
>>> u = Utilisateur.objects.get(username='nom_utilisateur')
>>> print(f"is_active: {u.is_active}, est_valide: {u.est_valide}")
```

---

## Références

### Documentation Django
- [Authentification](https://docs.djangoproject.com/en/5.1/topics/auth/)
- [Password management](https://docs.djangoproject.com/en/5.1/topics/auth/passwords/)
- [Sending email](https://docs.djangoproject.com/en/5.1/topics/email/)

### Documentation du projet
- [README principal](../README.md)
- [Réinitialisation de mot de passe](#réinitialisation-de-mot-de-passe)
- [Déploiement Production](../deployment/production.md)

### Code source
- Modèles : `accounts/models.py`
- Vues : `accounts/views/auth.py`
- Formulaires : `accounts/forms.py`
- Service email : `accounts/utils/email_service.py`

---

**Date de création** : 19 octobre 2025
**Dernière mise à jour** : 19 octobre 2025
**Auteur** : JM Schneider avec Claude Code
**Version** : 1.0
**Branche** : `feature/reinitialisation_mdp`
