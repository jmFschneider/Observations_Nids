# Accounts - Pièges et points d'attention

Ce fichier documente les erreurs récurrentes et pièges rencontrés dans l'application accounts.

---

## 🔥 Problème : Conflit d'email unique

### Contexte
Le champ `Utilisateur.email` a une contrainte **UNIQUE** (override de `AbstractUser`).

### Symptôme
```
IntegrityError: UNIQUE constraint failed: accounts_utilisateur.email
```

### Cause
Tentative de créer deux utilisateurs avec le même email.

### Solution

**Toujours vérifier l'existence avant création** :

```python
# ✅ CORRECT : Vérifier avant création
email = "jean.dupont@example.com"

if Utilisateur.objects.filter(email=email).exists():
    raise ValueError(f"Un utilisateur avec l'email {email} existe déjà")

utilisateur = Utilisateur.objects.create(
    username="jean.dupont",
    email=email,
    first_name="Jean",
    last_name="Dupont"
)
```

**❌ INCORRECT** : Créer sans vérifier

```python
# ❌ Erreur si email existe déjà
utilisateur = Utilisateur.objects.create(
    username="jean.dupont2",
    email="jean.dupont@example.com"  # Peut déjà exister !
)
```

### Gestion lors de l'import

**Fichier** : `accounts/management/commands/import_users.py`

```python
# Option 1 : Utiliser get_or_create avec email
utilisateur, created = Utilisateur.objects.get_or_create(
    email=email,
    defaults={
        'username': username,
        'first_name': first_name,
        'last_name': last_name
    }
)

if not created:
    # Utilisateur existe déjà, mettre à jour si nécessaire
    utilisateur.username = username
    utilisateur.save()

# Option 2 : Générer un email unique temporaire
if Utilisateur.objects.filter(email=email).exists():
    email_temporaire = f"{username}_{int(time.time())}@temp.local"
    utilisateur = Utilisateur.objects.create(
        username=username,
        email=email_temporaire  # Email temporaire unique
    )
    # Avertir l'admin de corriger manuellement
```

### Prévention
- Toujours valider l'unicité de l'email avant création
- Utiliser `get_or_create()` lors d'imports
- Documenter la stratégie de gestion des conflits d'email

### Fichiers concernés
- `accounts/models.py:15-21` (contrainte UNIQUE)
- `accounts/management/commands/import_users.py` (gestion conflits)

**Voir aussi** : [docs/developpeurs/guides/INTEGRATION_UTILISATEURS.md](../../guides/INTEGRATION_UTILISATEURS.md)

---

## ⚠️ Problème : Confusion entre états de validation

### Contexte
Trois champs booléens contrôlent l'état du compte : `est_valide`, `is_active`, `est_refuse`.

### Symptôme
- Utilisateur validé mais ne peut pas se connecter
- Utilisateur refusé mais apparaît dans la liste des comptes actifs
- Incohérence entre `est_valide` et `is_active`

### Cause
Modification incohérente des drapeaux ou oubli d'un champ.

### Solution

**Toujours utiliser les workflows complets** :

```python
# ✅ CORRECT : Validation complète
def valider_compte(utilisateur):
    utilisateur.est_valide = True
    utilisateur.is_active = True
    utilisateur.est_refuse = False  # Réinitialiser si précédemment refusé
    utilisateur.save()

# ✅ CORRECT : Refus complet
def refuser_compte(utilisateur):
    utilisateur.est_valide = False
    utilisateur.is_active = False
    utilisateur.est_refuse = True
    utilisateur.save()

# ✅ CORRECT : Soft delete (désactivation)
def desactiver_compte(utilisateur):
    # Conserver est_valide=True pour historique
    utilisateur.is_active = False
    utilisateur.save()
```

**❌ INCORRECT** : Modifier un seul champ

```python
# ❌ Utilisateur validé mais ne peut pas se connecter
utilisateur.est_valide = True
utilisateur.save()  # Oubli de is_active=True !

# ❌ Utilisateur refusé mais toujours actif
utilisateur.est_refuse = True
utilisateur.save()  # Oubli de is_active=False !
```

### États valides

| est_valide | is_active | est_refuse | État correct |
|------------|-----------|------------|--------------|
| False | False | False | **En attente** (nouveau compte) |
| True | True | False | **Actif** (compte validé et actif) |
| False | False | True | **Refusé** (demande rejetée) |
| True | False | False | **Désactivé** (soft delete) |

**⚠️ États invalides** :
- `est_valide=True` + `is_active=False` + `est_refuse=True` → Incohérent !
- `est_valide=False` + `is_active=True` → Utilisateur peut se connecter mais n'est pas validé !

### Prévention
- Toujours utiliser les fonctions de workflow complètes
- Vérifier les trois champs après modification
- Ajouter une méthode `clean()` au modèle pour valider la cohérence

### Fichiers concernés
- `accounts/models.py:10-12` (champs booléens)
- `accounts/views/auth.py:345-386` (validation)
- `accounts/views/auth.py:389-435` (refus)

---

## ⚠️ Problème : Suppression d'utilisateur (CASCADE)

### Contexte
Les relations vers `Utilisateur` varient : certaines CASCADE, d'autres SET_NULL.

### Symptôme
Suppression d'un utilisateur → suppression en cascade de données importantes.

### Cause
Comportement CASCADE sur certaines relations (notifications, etc.).

### Solution

**Toujours utiliser soft delete (désactivation)** :

```python
# ✅ CORRECT : Soft delete
utilisateur.is_active = False
utilisateur.save()
# ✅ Utilisateur ne peut plus se connecter
# ✅ Toutes ses données sont conservées (fiches, validations, etc.)
```

**❌ INCORRECT** : Hard delete

```python
# ❌ DANGER : Suppression physique
utilisateur.delete()
# ❌ Supprime toutes les notifications en CASCADE
# ❌ Perte de traçabilité (observateur, reviewer)
```

**Avant de supprimer physiquement** (si vraiment nécessaire) :

```python
# Vérifier l'impact
from observations.models import FicheObservation
from review.models import Validation

nb_fiches = FicheObservation.objects.filter(observateur=utilisateur).count()
nb_validations = Validation.objects.filter(reviewer=utilisateur).count()
nb_notifications = utilisateur.notifications.count()

print(f"ATTENTION : Suppression va affecter :")
print(f"  - {nb_fiches} fiches (observateur → NULL)")
print(f"  - {nb_validations} validations (reviewer → CASCADE !)")
print(f"  - {nb_notifications} notifications (CASCADE)")
```

### Cascade behaviors par application

| Relation | on_delete | Impact suppression |
|----------|-----------|---------------------|
| `Notification.destinataire` → `Utilisateur` | **CASCADE** | Notifications supprimées |
| `Notification.utilisateur_concerne` → `Utilisateur` | **CASCADE** | Notifications supprimées |
| `FicheObservation.observateur` → `Utilisateur` | **SET_NULL** | Observateur → NULL (conservé) |
| `Validation.reviewer` → `Utilisateur` | **CASCADE** | Validations supprimées ⚠️ |
| `EtatCorrection.validee_par` → `Utilisateur` | **SET_NULL** | Valideur → NULL (conservé) |

### Prévention
- **Toujours** utiliser soft delete (is_active=False)
- Ne jamais supprimer physiquement un utilisateur en production
- Archiver les comptes au lieu de les supprimer

### Fichiers concernés
- `accounts/views/auth.py:201-217` (soft delete)
- `review/models.py:16-18` (CASCADE sur reviewer)

---

## ⚠️ Problème : Superuser vs Administrateur

### Contexte
Deux niveaux de droits : `is_superuser` (Django natif) et `role='administrateur'` (custom).

### Symptôme
- Administrateur ne peut pas promouvoir d'autres administrateurs
- Superuser ne peut pas accéder aux fonctions admin du projet

### Cause
Confusion entre `is_superuser` et `role='administrateur'`.

### Solution

**Hiérarchie des droits** :

```python
# Superuser (is_superuser=True)
# ✅ Accès admin Django (/admin/)
# ✅ Peut promouvoir des administrateurs
# ✅ Bypass toutes les permissions

# Administrateur (role='administrateur')
# ✅ Peut valider/refuser comptes
# ✅ Peut gérer utilisateurs
# ❌ Ne peut PAS promouvoir des administrateurs
# ❌ N'a PAS accès admin Django (sauf si is_staff=True)
```

**Vérification des permissions** :

```python
# ✅ CORRECT : Vérifier le bon niveau
from accounts.views.auth import est_admin, est_superuser

# Pour gestion utilisateurs
@user_passes_test(est_admin)
def gerer_utilisateurs(request):
    pass  # Accessible aux administrateurs

# Pour promotion admin
@user_passes_test(est_superuser)
def promouvoir_admin(request):
    pass  # Accessible uniquement aux superusers
```

**Créer un superuser** :

```bash
# Via management command Django
python manage.py createsuperuser
# → is_superuser=True, is_staff=True automatiquement
```

### Prévention
- Documenter clairement la différence
- Utiliser les bonnes fonctions de test (`est_admin` vs `est_superuser`)
- Limiter le nombre de superusers (1-2 max)

### Fichiers concernés
- `accounts/views/auth.py:29-36` (fonctions de test)
- `accounts/views/auth.py:315-333` (promotion admin)

---

## ⚠️ Problème : Token de réinitialisation expiré

### Contexte
Django génère des tokens pour la réinitialisation de mot de passe (durée limitée).

### Symptôme
- Utilisateur clique sur le lien de réinitialisation
- Message "Lien invalide ou expiré"

### Cause
- Token expiré (timeout Django par défaut)
- Utilisateur a changé son mot de passe après génération du token
- Token utilisé plusieurs fois

### Solution

**Le système actuel gère déjà l'expiration** :

```python
# accounts/views/auth.py:480-521
if utilisateur is not None and default_token_generator.check_token(utilisateur, token):
    # Token valide
    pass
else:
    # Token invalide ou expiré
    logger.warning("Tentative de réinitialisation avec lien invalide ou expiré")
    return render(request, 'accounts/reinitialiser_mot_de_passe.html', {'validlink': False})
```

**Si besoin d'étendre la durée** :

```python
# settings.py
PASSWORD_RESET_TIMEOUT = 86400  # 24 heures (en secondes)
# Par défaut : 259200 (3 jours)
```

### Prévention
- Informer l'utilisateur de la durée de validité du lien
- Permettre de redemander un lien si expiré
- Logger les tokens expirés pour détecter les problèmes

### Fichiers concernés
- `accounts/views/auth.py:438-477` (génération token)
- `accounts/views/auth.py:480-521` (validation token)

---

## ⚠️ Problème : Anti-spam notification bypass

### Contexte
Limite de 1 renvoi de notification admin toutes les 24 heures (stocké en session).

### Symptôme
- Utilisateur peut contourner en nettoyant les cookies
- Session expirée → anti-spam resetté

### Cause
Stockage en session (côté client, peut être effacé).

### Solution

**Solution actuelle (suffisante pour la plupart des cas)** :

```python
# accounts/views/auth.py:562-569
last_sent_time_str = request.session.get(f'last_resend_{user_id}')
if last_sent_time_str:
    last_sent_time = datetime.fromisoformat(last_sent_time_str)
    if datetime.now() - last_sent_time < timedelta(hours=24):
        messages.warning(request, "Une notification a déjà été renvoyée il y a moins de 24 heures.")
        return redirect('accounts:compte_en_attente', user_id=user_id)
```

**Solution robuste (si problème de spam)** :

```python
# Option 1 : Ajouter un champ au modèle Utilisateur
class Utilisateur(AbstractUser):
    # ...
    derniere_relance_notification = models.DateTimeField(null=True, blank=True)

# Vérifier en base au lieu de session
if utilisateur.derniere_relance_notification:
    if timezone.now() - utilisateur.derniere_relance_notification < timedelta(hours=24):
        messages.warning(request, "Une notification a déjà été renvoyée.")
        return redirect('accounts:compte_en_attente', user_id=user_id)

utilisateur.derniere_relance_notification = timezone.now()
utilisateur.save()
```

**Option 2 : Créer un modèle RelanceNotification**

```python
class RelanceNotification(models.Model):
    utilisateur = models.ForeignKey(Utilisateur, on_delete=models.CASCADE)
    date_relance = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date_relance']

# Vérifier les relances récentes
relances_recentes = RelanceNotification.objects.filter(
    utilisateur=utilisateur,
    date_relance__gte=timezone.now() - timedelta(hours=24)
)

if relances_recentes.exists():
    messages.warning(request, "Une notification a déjà été renvoyée.")
    return redirect('accounts:compte_en_attente', user_id=user_id)

RelanceNotification.objects.create(utilisateur=utilisateur)
```

### Prévention
- Monitorer les relances de notifications dans les logs
- Implémenter la solution robuste si abus détectés

### Fichiers concernés
- `accounts/views/auth.py:547-590` (anti-spam session)

---

## ⚠️ Problème : Échec d'envoi d'email silencieux

### Contexte
`EmailService` envoie des emails critiques (validation, refus, mot de passe).

### Symptôme
- Email non reçu par l'utilisateur
- Aucun message d'erreur visible dans l'interface
- Utilisateur attend la validation sans savoir

### Cause
- Erreur SMTP silencieuse (credentials invalides, quota dépassé)
- Email dans les spams
- Email invalide

### Solution

**Toujours logger les emails envoyés** :

```python
# ✅ CORRECT : Logger les succès et échecs
try:
    succes = EmailService.envoyer_email_compte_valide(utilisateur)
    if succes:
        logger.info(f"Email validation envoyé à {utilisateur.email}")
    else:
        logger.error(f"Échec envoi email à {utilisateur.email}")
        messages.warning(request, f"Erreur lors de l'envoi de l'email à {utilisateur.email}")
except Exception as e:
    logger.exception(f"Exception lors envoi email : {e}")
    messages.error(request, "Erreur lors de l'envoi de l'email")
```

**Vérifier la configuration email** :

```python
# settings.py
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'  # Production
# EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'  # Dev (logs console)
# EMAIL_BACKEND = 'django.core.mail.backends.filebased.EmailBackend'  # Dev (sauvegarde fichiers)

EMAIL_HOST = 'smtp.example.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'noreply@example.com'
EMAIL_HOST_PASSWORD = 'password'  # ⚠️ Utiliser variables d'environnement !
```

**Tester l'envoi d'email** :

```python
from django.core.mail import send_mail

send_mail(
    subject='Test email',
    message='Ceci est un test',
    from_email='noreply@example.com',
    recipient_list=['admin@example.com'],
    fail_silently=False  # ⚠️ Raise exception si erreur
)
```

### Prévention
- Logger tous les envois d'email (succès et échecs)
- Monitorer les logs régulièrement
- Tester les emails en dev avec `console` backend
- Afficher un message à l'utilisateur si email critique échoue

### Fichiers concernés
- `accounts/utils/email_service.py` (envoi emails)
- `settings.py` (configuration SMTP)

---

## 🔥 Problème : Modification de AUTH_USER_MODEL

### Contexte
`AUTH_USER_MODEL = 'accounts.Utilisateur'` est défini au niveau projet.

### Symptôme
Changement du modèle utilisateur après création de la base de données → erreurs de migration complexes.

### Cause
Django ne supporte **pas** le changement de `AUTH_USER_MODEL` après les migrations initiales.

### Solution

**⚠️ NE JAMAIS CHANGER AUTH_USER_MODEL** après création de la base.

**Si vraiment nécessaire** (extrêmement rare) :

```bash
# 1. Exporter toutes les données
python manage.py dumpdata > backup.json

# 2. Supprimer la base de données
rm db.sqlite3  # ou DROP DATABASE sur PostgreSQL

# 3. Supprimer toutes les migrations
find . -path "*/migrations/*.py" -not -name "__init__.py" -delete

# 4. Modifier AUTH_USER_MODEL dans settings.py

# 5. Créer nouvelles migrations
python manage.py makemigrations
python manage.py migrate

# 6. Réimporter les données (avec adaptations)
python manage.py loaddata backup.json
```

**⚠️ ATTENTION** : Cette opération est **très risquée** et peut entraîner une **perte de données**.

### Prévention
- Définir AUTH_USER_MODEL dès le début du projet (avant première migration)
- **NE JAMAIS** le modifier ensuite
- Étendre le modèle Utilisateur via relation OneToOne (Profil) si besoin de champs supplémentaires

### Fichiers concernés
- `settings.py` (AUTH_USER_MODEL)
- Toutes les migrations du projet

---

## ⚠️ Problème : Notifications non filtrées (spam)

### Contexte
Les notifications peuvent rapidement s'accumuler pour les administrateurs.

### Symptôme
- Centaines de notifications non lues
- Interface surchargée
- Notifications importantes noyées dans le bruit

### Cause
- Création de notifications en doublon
- Pas de nettoyage des anciennes notifications
- Notifications créées pour chaque relance

### Solution

**Éviter les doublons** :

```python
# ✅ CORRECT : Vérifier l'existence avant création
existing_notif = Notification.objects.filter(
    destinataire=admin,
    type_notification='demande_compte',
    utilisateur_concerne=utilisateur,
    est_lue=False
).first()

if not existing_notif:
    Notification.objects.create(
        destinataire=admin,
        type_notification='demande_compte',
        titre=f"Nouvelle demande de compte : {utilisateur.username}",
        message=f"{utilisateur.first_name} {utilisateur.last_name} a demandé un compte.",
        lien=f"/accounts/utilisateurs/{utilisateur.id}/detail/",
        utilisateur_concerne=utilisateur
    )
```

**Nettoyer les anciennes notifications** :

```python
from django.utils import timezone
from datetime import timedelta

# Supprimer les notifications lues de plus de 30 jours
Notification.objects.filter(
    est_lue=True,
    date_lecture__lt=timezone.now() - timedelta(days=30)
).delete()
```

**Créer une commande management pour nettoyage** :

```bash
python manage.py nettoyer_notifications
```

### Prévention
- Vérifier l'existence avant créer notification
- Marquer comme lues automatiquement après action (validation, refus)
- Nettoyer régulièrement les anciennes notifications

### Fichiers concernés
- `accounts/views/auth.py:289-300` (création notifications)
- `accounts/views/auth.py:376-378` (marquage comme lue)

---

## ✅ Bonnes pratiques

### 1. Toujours utiliser soft delete

```python
# ✅ Désactiver au lieu de supprimer
utilisateur.is_active = False
utilisateur.save()
```

### 2. Vérifier l'unicité de l'email

```python
# ✅ get_or_create pour éviter doublons
utilisateur, created = Utilisateur.objects.get_or_create(
    email=email,
    defaults={'username': username, ...}
)
```

### 3. Workflows complets de validation/refus

```python
# ✅ Modifier tous les champs nécessaires
utilisateur.est_valide = True
utilisateur.is_active = True
utilisateur.est_refuse = False
utilisateur.save()
```

### 4. Logger les opérations critiques

```python
import logging
logger = logging.getLogger(__name__)

logger.info(f"Compte validé pour {utilisateur.username} par {request.user.username}")
logger.warning(f"Échec envoi email à {utilisateur.email}")
logger.error(f"Erreur inattendue : {e}", exc_info=True)
```

### 5. Requêtes optimisées

```python
# ✅ select_related pour ForeignKey
utilisateurs = Utilisateur.objects.select_related('profile').all()

# ✅ prefetch_related pour reverse relations
utilisateurs = Utilisateur.objects.prefetch_related('notifications').all()
```

---

## 🔥 Checklist avant modification d'accounts

- [ ] Lire ce fichier gotchas.md
- [ ] **NE JAMAIS** modifier AUTH_USER_MODEL après migrations initiales
- [ ] Toujours utiliser soft delete (is_active=False)
- [ ] Vérifier unicité email avant création
- [ ] Utiliser workflows complets (valider/refuser avec tous les champs)
- [ ] Logger les opérations critiques (email, validation, refus)
- [ ] Tester l'envoi d'emails en dev
- [ ] Distinguer superuser et administrateur

---

*Dernière mise à jour : 2025-12-27*
