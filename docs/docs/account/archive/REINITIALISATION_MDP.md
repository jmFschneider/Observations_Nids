# Fonctionnalité de réinitialisation de mot de passe

## Vue d'ensemble

Cette fonctionnalité permet aux utilisateurs qui ont oublié leur mot de passe de le réinitialiser de manière sécurisée via email.

## Workflow utilisateur

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

## Composants implémentés

### 1. Formulaires (`accounts/forms.py`)

#### `MotDePasseOublieForm`
- **Champ** : `email` (EmailField)
- **Validation** : Format email valide
- **Usage** : Page de demande de réinitialisation

#### `NouveauMotDePasseForm`
- **Champs** :
  - `password1` : Nouveau mot de passe
  - `password2` : Confirmation du mot de passe
- **Validations** :
  - Minimum 8 caractères
  - Les deux mots de passe doivent correspondre

### 2. Vues (`accounts/views/auth.py`)

#### `mot_de_passe_oublie(request)`
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

#### `reinitialiser_mot_de_passe(request, uidb64, token)`
- **URL** : `/accounts/reinitialiser-mot-de-passe/<uidb64>/<token>/`
- **Méthode** : GET et POST
- **Authentification** : Non requise
- **Fonctionnement** :
  1. Décode l'UID et récupère l'utilisateur
  2. Vérifie la validité du token
  3. Si valide : affiche le formulaire de nouveau mot de passe
  4. Enregistre le nouveau mot de passe avec hachage
  5. Redirige vers la page de login

### 3. Service Email (`accounts/utils/email_service.py`)

#### `EmailService.envoyer_email_reinitialisation_mdp(utilisateur, uid, token)`
- **Template** : `accounts/emails/reinitialisation_mot_de_passe.html`
- **Sujet** : "[Observations Nids] Réinitialisation de votre mot de passe"
- **Contenu** :
  - Bouton avec lien de réinitialisation
  - Lien copié/collable en fallback
  - Avertissement de validité (24h)
  - Instructions de sécurité
- **Protocole** : HTTPS en production, HTTP en développement

### 4. Templates

#### `accounts/templates/accounts/mot_de_passe_oublie.html`
- Formulaire de saisie d'email
- Bouton d'envoi
- Lien de retour vers la page de login

#### `accounts/templates/accounts/reinitialiser_mot_de_passe.html`
- Deux états :
  - **Lien valide** : Formulaire de nouveau mot de passe
  - **Lien invalide/expiré** : Message d'erreur avec option de redemander un lien

#### `accounts/templates/accounts/emails/reinitialisation_mot_de_passe.html`
- Email HTML responsive
- Style inline pour compatibilité email
- Bouton CTA principal
- Lien de fallback
- Section d'avertissements

### 5. URLs (`accounts/urls.py`)

```python
# Demande de réinitialisation
path('mot-de-passe-oublie/', auth.mot_de_passe_oublie, name='mot_de_passe_oublie')

# Réinitialisation avec token
path('reinitialiser-mot-de-passe/<uidb64>/<token>/',
     auth.reinitialiser_mot_de_passe,
     name='reinitialiser_mot_de_passe')
```

### 6. Modification du template de login (`observations/templates/login.html`)

Ajout d'un lien "Mot de passe oublié ?" sous le formulaire de connexion.

## Sécurité

### Mesures implémentées

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

## Configuration requise

### Variables d'environnement

```bash
# .env ou settings_local.py
ADMIN_EMAIL=admin@example.com          # Pour notifications admin
DEFAULT_FROM_EMAIL=noreply@example.com # Email expéditeur
ALLOWED_HOSTS=["localhost", "example.com"]  # Pour construire les URLs
```

### Configuration SMTP

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

## Tests

### Test manuel du workflow

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

### Test des cas limites

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

## Monitoring et logs

### Événements logués

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

## Extensions futures possibles

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

## Dépendances

### Paquets Python
- Django >= 5.0 (inclus dans le projet)
- Pas de dépendances supplémentaires

### Configuration Django requise
- `django.contrib.auth` dans `INSTALLED_APPS`
- `django.contrib.sessions` pour les messages
- `django.contrib.messages` pour les notifications

## Compatibilité

- **Django** : 5.x
- **Python** : 3.10+
- **Navigateurs** : Tous navigateurs modernes
- **Email clients** : HTML responsive compatible

---

**Date de création** : 19 octobre 2025
**Auteur** : JM Schneider avec Claude Code
**Version** : 1.0
**Branche** : `feature/reinitialisation_mdp`
