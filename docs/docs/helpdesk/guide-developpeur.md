# Guide développeur : Django-Helpdesk

## 🎯 Vue d'ensemble

Ce document détaille l'intégration et la personnalisation de **Django-Helpdesk** dans le projet Observations Nids.

**Package utilisé** : `django-helpdesk` v2.0.2

---

## 📦 Installation et configuration

### Dépendances

Django-Helpdesk a été ajouté dans `requirements-base.in` :

```ini
django-helpdesk
```

**Dépendances transitives installées :**
- `django-bootstrap4-form` (rendu des formulaires)
- `django-cleanup` (nettoyage automatique des fichiers)
- `django-model-utils` (utilitaires pour modèles)
- `djangorestframework` (API REST)
- `akismet` (anti-spam)
- `email-reply-parser` (parsing des réponses email)
- `lxml`, `markdown`, `oauthlib`, `requests-oauthlib`

### Configuration Django

**Fichier : `observations_nids/settings.py`**

```python
INSTALLED_APPS = [
    # ...
    'django.contrib.sites',         # Requis pour django-helpdesk
    'django.contrib.humanize',      # Formatage des dates/nombres
    'bootstrap4form',               # Rendu des formulaires
    'rest_framework',               # API REST
    'helpdesk',                     # Django-Helpdesk
    'helpdesk_custom.apps.HelpdeskCustomConfig',  # Personnalisations
]

# Configuration Django Sites
SITE_ID = 1

# Désactiver l'accès public (authentification obligatoire)
HELPDESK_SUBMIT_A_TICKET_PUBLIC = False
HELPDESK_VIEW_A_TICKET_PUBLIC = False

# Désactiver le mode équipes
HELPDESK_TEAMS_MODE_ENABLED = False

# Formulaires personnalisés
HELPDESK_PUBLIC_TICKET_FORM_CLASS = 'helpdesk_custom.forms.CustomPublicTicketForm'
HELPDESK_TICKET_FORM_CLASS = 'helpdesk_custom.forms.CustomTicketForm'
```

### URLs

**Fichier : `observations_nids/urls.py`**

```python
urlpatterns = [
    # ...
    path('helpdesk/', include('helpdesk.urls')),
]
```

**URLs disponibles :**
- `/helpdesk/` : Tableau de bord
- `/helpdesk/tickets/submit/` : Créer un ticket
- `/helpdesk/tickets/<slug>/` : Voir un ticket
- `/helpdesk/api/` : API REST (si activée)

---

## 🎨 Personnalisations

### Module helpdesk_custom

Un module Django dédié a été créé pour les personnalisations sans modifier le code de `django-helpdesk`.

**Structure :**
```
helpdesk_custom/
├── __init__.py
├── apps.py          # Configuration avec hook ready()
└── forms.py         # Formulaires personnalisés
```

### 1. Formulaires personnalisés

**Fichier : `helpdesk_custom/forms.py`**

```python
from django.utils.translation import gettext_lazy as _
from helpdesk.forms import PublicTicketForm, TicketForm


class CustomPublicTicketForm(PublicTicketForm):
    """Formulaire pour création de tickets (utilisateurs non authentifiés)"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Changer "Queue" en "Catégorie" (traduction française)
        if 'queue' in self.fields:
            self.fields['queue'].label = _('Catégorie')


class CustomTicketForm(TicketForm):
    """Formulaire pour création de tickets (utilisateurs authentifiés)"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'queue' in self.fields:
            self.fields['queue'].label = _('Catégorie')
```

**Pourquoi cette approche ?**
- Modification du label sans toucher aux traductions globales
- Héritage propre des formulaires Django-Helpdesk
- Facilité de maintenance lors des mises à jour du package

### 2. Monkey-patching de la vue staff

**Problème** : Le formulaire `TicketForm` est hard-codé dans `CreateTicketView` :

```python
# Dans helpdesk/views/staff.py (code original)
class CreateTicketView(TemplateView):
    form_class = TicketForm  # Hard-codé !
```

**Solution** : Utiliser un hook `ready()` dans `AppConfig` :

**Fichier : `helpdesk_custom/apps.py`**

```python
from django.apps import AppConfig


class HelpdeskCustomConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'helpdesk_custom'
    verbose_name = 'Helpdesk Personnalisé'

    def ready(self):
        """
        Hook appelé au démarrage de Django.
        Remplace la form_class de CreateTicketView.
        """
        # Import local pour éviter les imports circulaires
        from helpdesk.views import staff  # noqa: PLC0415
        from .forms import CustomTicketForm  # noqa: PLC0415

        # Monkey-patch : remplacer la classe de formulaire
        staff.CreateTicketView.form_class = CustomTicketForm
```

**Avantages :**
- Pas besoin de forker `django-helpdesk`
- Modification appliquée automatiquement au démarrage
- Code de personnalisation isolé et maintenable

**Inconvénients :**
- Technique "hacky" qui peut casser lors d'une mise à jour majeure
- Non documenté dans Django-Helpdesk (solution trouvée par analyse du code)

---

## 🎭 Personnalisation des templates

### Structure des templates

```
templates/
└── helpdesk/
    ├── base.html                    # Template de base (surcharge)
    ├── create_ticket.html           # Formulaire (authentifié)
    └── public_create_ticket.html    # Formulaire (public)
```

### Template de base personnalisé

**Fichier : `templates/helpdesk/base.html`**

**Principales modifications :**

1. **Intégration de la navbar du site**
```django
{% include "components/navbar.html" %}
```

2. **Conservation du menu latéral Helpdesk**
```django
<div class="sidebar">
    <!-- Menu Helpdesk original -->
    <ul class="sidebar-nav">
        <li><a href="{% url 'helpdesk:dashboard' %}">Tableau de bord</a></li>
        <li><a href="{% url 'helpdesk:submit' %}">Créer un ticket</a></li>
        <!-- ... -->
    </ul>
</div>
```

3. **Layout flexbox pour sidebar + content**
```css
#wrapper {
    display: flex !important;
    min-height: calc(100vh - 200px);
}

.sidebar {
    width: 250px !important;
    background-color: #343a40;
    flex-shrink: 0;
}

#page-content-wrapper {
    flex: 1;
    padding: 1cm 1cm 1cm 1.5cm;  /* Espacement content-sidebar */
}
```

4. **Personnalisation des couleurs**
```css
.sidebar {
    background-color: #343a40;  /* Gris foncé */
}

.sidebar a:hover {
    background-color: #198754;  /* Vert du site */
}
```

### Templates de formulaires

**Fichiers : `templates/helpdesk/create_ticket.html` et `public_create_ticket.html`**

**Modifications :**
- Utilisation de `bootstrap4form` pour rendu cohérent
- Espacement entre champs (marges CSS)
- Conservation du style du site

```django
<div class="form-group" style="margin-bottom: 60px; padding: 20px 0;">
    {{ form.field_name|bootstrap4form }}
</div>
```

---

## 📊 Modèle de données

### Principales tables (gérées par Django-Helpdesk)

| Table | Description |
|-------|-------------|
| `helpdesk_queue` | Catégories de tickets (Bug, Feature, Support, Doc) |
| `helpdesk_ticket` | Tickets créés par les utilisateurs |
| `helpdesk_followup` | Réponses et suivis sur les tickets |
| `helpdesk_attachment` | Fichiers joints aux tickets |
| `helpdesk_ticketchange` | Historique des modifications |
| `helpdesk_customfield` | Champs personnalisés (optionnel) |

### Modèle Utilisateur

Django-Helpdesk utilise le modèle d'utilisateur Django par défaut (`AUTH_USER_MODEL`).

Dans notre cas : `accounts.Utilisateur`

**Champs utilisés :**
- `username` : Identification
- `email` : Notifications
- `first_name` + `last_name` : Affichage
- `is_staff` : Accès à l'interface staff

---

## 🔧 Création des catégories (Queues)

### Via le shell Django

```python
python manage.py shell

from helpdesk.models import Queue

Queue.objects.create(
    title="Bug",
    slug="bug",
    email_address="observationnids+bug@gmail.com",
    allow_public_submission=False
)

Queue.objects.create(
    title="Nouvelle fonctionnalité",
    slug="nouvelle-fonctionnalite",
    email_address="observationnids+feature@gmail.com",
    allow_public_submission=False
)

Queue.objects.create(
    title="Support/Question",
    slug="support-question",
    email_address="observationnids+support@gmail.com",
    allow_public_submission=False
)

Queue.objects.create(
    title="Documentation",
    slug="documentation",
    email_address="observationnids+doc@gmail.com",
    allow_public_submission=False
)
```

### Via l'admin Django

1. Aller sur `/admin/`
2. **Helpdesk → Files** (ou Queues en anglais)
3. Cliquer sur **"Ajouter"**
4. Remplir les champs :
   - **Titre** : Nom de la catégorie
   - **Slug** : Identifiant URL
   - **Adresse e-mail** : Email pour cette file

---

## 📧 Configuration email

### Variables d'environnement

**Fichier : `.env`**

```bash
# Backend email (console pour dev, smtp pour prod)
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend

# Serveur SMTP
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True

# Authentification
EMAIL_HOST_USER=observationnids@gmail.com
EMAIL_HOST_PASSWORD=votre_mot_de_passe_application

# Expéditeur par défaut
DEFAULT_FROM_EMAIL=observationnids@gmail.com

# Email admin (pour notifications critiques)
ADMIN_EMAIL=admin@observations-nids.fr
```

### Astuce Gmail : Sous-adresses

Gmail ignore le `+` dans les adresses, ce qui permet de router tous les tickets vers une seule boîte :

```
observationnids+bug@gmail.com       → observationnids@gmail.com
observationnids+feature@gmail.com   → observationnids@gmail.com
observationnids+support@gmail.com   → observationnids@gmail.com
```

**Avantages :**
- Une seule boîte email à gérer
- Filtrage automatique par catégorie
- Aucune config Gmail supplémentaire

---

## 🔐 Sécurité

### Désactivation de l'accès public

```python
HELPDESK_SUBMIT_A_TICKET_PUBLIC = False
HELPDESK_VIEW_A_TICKET_PUBLIC = False
```

**Conséquences :**
- Seuls les utilisateurs authentifiés peuvent créer/voir des tickets
- Pas de risque de spam
- Meilleur contrôle des demandes

### Permissions

Django-Helpdesk utilise les permissions Django standard :

| Permission | Description |
|------------|-------------|
| `helpdesk.add_ticket` | Créer des tickets |
| `helpdesk.change_ticket` | Modifier des tickets |
| `helpdesk.view_ticket` | Voir les tickets |
| `helpdesk.delete_ticket` | Supprimer des tickets |

**Configuration dans notre projet :**
- **Utilisateurs authentifiés** : Peuvent créer et voir leurs propres tickets
- **Staff** (`is_staff=True`) : Accès complet à l'interface d'administration
- **Administrateurs** (`role='administrateur'`) : Toutes les permissions

---

## 🔍 API REST (optionnel)

Django-Helpdesk inclut une API REST via Django REST Framework.

### Activer l'API

Dans `settings.py` :

```python
REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.TokenAuthentication',
    ],
}
```

### Endpoints disponibles

```
GET    /helpdesk/api/tickets/           # Liste des tickets
POST   /helpdesk/api/tickets/           # Créer un ticket
GET    /helpdesk/api/tickets/<id>/      # Détail d'un ticket
PATCH  /helpdesk/api/tickets/<id>/      # Modifier un ticket
DELETE /helpdesk/api/tickets/<id>/      # Supprimer un ticket

GET    /helpdesk/api/queues/            # Liste des queues
GET    /helpdesk/api/followups/         # Liste des followups
```

### Exemple d'utilisation

```python
import requests

# Authentification
session = requests.Session()
session.auth = ('username', 'password')

# Créer un ticket via API
response = session.post('https://site.fr/helpdesk/api/tickets/', json={
    'queue': 1,  # ID de la queue
    'title': 'Bug dans la saisie',
    'description': 'Description détaillée...',
    'priority': 3,
})

ticket = response.json()
print(f"Ticket créé : #{ticket['id']}")
```

---

## 🧪 Tests

### Tests d'intégration recommandés

**Fichier : `helpdesk_custom/tests/test_integration.py`**

```python
import pytest
from django.urls import reverse
from helpdesk.models import Queue, Ticket


@pytest.mark.django_db
def test_create_ticket_authenticated(client, user):
    """Test de création d'un ticket par un utilisateur authentifié"""
    client.force_login(user)

    queue = Queue.objects.create(title="Bug", slug="bug")

    response = client.post(reverse('helpdesk:submit'), {
        'queue': queue.id,
        'title': 'Test ticket',
        'description': 'Description de test',
        'priority': 3,
    })

    assert response.status_code == 302  # Redirection
    assert Ticket.objects.count() == 1
    ticket = Ticket.objects.first()
    assert ticket.title == 'Test ticket'


@pytest.mark.django_db
def test_create_ticket_unauthenticated(client):
    """Test de refus d'accès pour utilisateur non authentifié"""
    response = client.get(reverse('helpdesk:submit'))
    assert response.status_code == 302  # Redirection vers login
```

---

## 📝 Migrations

Lors de l'installation de Django-Helpdesk :

```bash
python manage.py migrate helpdesk
```

**Tables créées :**
- `helpdesk_queue`
- `helpdesk_ticket`
- `helpdesk_followup`
- `helpdesk_attachment`
- `helpdesk_ticketchange`
- `helpdesk_customfield`
- `helpdesk_customfieldvalue`
- Etc.

**Site Django** :
```bash
python manage.py migrate sites
```

Puis mettre à jour le site :

```python
from django.contrib.sites.models import Site
site = Site.objects.get(id=1)
site.domain = 'observations-nids.fr'
site.name = 'Observations Nids'
site.save()
```

---

## 🚀 Déploiement en production

### Checklist

- [ ] Exécuter les migrations : `python manage.py migrate`
- [ ] Collecter les statiques : `python manage.py collectstatic`
- [ ] Créer les Queues (catégories)
- [ ] Configurer l'email SMTP
- [ ] Mettre à jour le Site Django
- [ ] Vérifier `HELPDESK_SUBMIT_A_TICKET_PUBLIC = False`
- [ ] Créer un utilisateur staff pour le support
- [ ] Tester la création d'un ticket
- [ ] Vérifier les emails de notification

### Variables d'environnement production

```bash
# Email
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=observationnids@gmail.com
EMAIL_HOST_PASSWORD=***

# Site
SITE_DOMAIN=observations-nids.fr
```

---

## 🔧 Maintenance

### Mise à jour de Django-Helpdesk

```bash
# Dans requirements-base.in
django-helpdesk==2.1.0  # Nouvelle version

pip-compile requirements-base.in
pip install -r requirements-base.txt
python manage.py migrate
python manage.py collectstatic
```

**Attention :** Vérifier les breaking changes dans le CHANGELOG avant de mettre à jour.

### Nettoyage des anciens tickets

Django-Helpdesk ne nettoie pas automatiquement les vieux tickets fermés.

**Script de nettoyage (optionnel) :**

```python
from datetime import timedelta
from django.utils import timezone
from helpdesk.models import Ticket

# Supprimer les tickets fermés depuis plus de 2 ans
cutoff_date = timezone.now() - timedelta(days=730)
old_tickets = Ticket.objects.filter(
    status=Ticket.CLOSED_STATUS,
    modified__lt=cutoff_date
)

print(f"Suppression de {old_tickets.count()} anciens tickets...")
old_tickets.delete()
```

---

## 📚 Ressources

### Documentation officielle

- [Django-Helpdesk Documentation](https://django-helpdesk.readthedocs.io/)
- [GitHub Repository](https://github.com/django-helpdesk/django-helpdesk)
- [PyPI Package](https://pypi.org/project/django-helpdesk/)

### Documentation du projet

- [Guide utilisateur Helpdesk](guide-utilisateur.md)
- [Configuration Django-Helpdesk (détaillée)](../guides/fonctionnalites/django-helpdesk.md)

### Issues connues

- **Traduction française partielle** : Certains termes ne sont pas traduits (ex: "Queue" → "File")
  - **Solution** : Formulaires personnalisés pour changer les labels

- **Form hard-codée dans CreateTicketView** : Impossible de surcharger via settings
  - **Solution** : Monkey-patching dans `apps.py`

---

## 🤝 Contribution

Pour contribuer aux personnalisations de Helpdesk :

1. Modifier `helpdesk_custom/forms.py` ou `helpdesk_custom/apps.py`
2. Tester localement
3. Exécuter `pytest` pour vérifier la non-régression
4. Créer une PR avec description des changements

**Ne jamais modifier directement le code de `django-helpdesk` dans `.venv/` !**
