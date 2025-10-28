# Django-Helpdesk : Système de Support et Tickets

## Vue d'ensemble

Django-Helpdesk est un système de gestion de tickets de support intégré au projet Observations Nids. Il permet aux utilisateurs de signaler des bugs, demander de nouvelles fonctionnalités, poser des questions et obtenir de l'aide.

**Version installée** : django-helpdesk (installée via pip)

**URL d'accès** : `/helpdesk/`

---

## Fonctionnalités principales

### 1. Création de tickets

Les utilisateurs (connectés ou non) peuvent créer des tickets en choisissant parmi plusieurs catégories :

- 🐛 **Bug** : Signaler un problème ou dysfonctionnement
- ✨ **Nouvelle fonctionnalité** : Demander une amélioration ou nouvelle fonction
- 💬 **Support / Question** : Poser une question d'aide
- 📝 **Documentation** : Signaler un problème de documentation

### 2. Gestion des tickets (Staff)

Les membres du staff peuvent :
- Consulter tous les tickets via le **Dashboard**
- Filtrer et rechercher les tickets
- Assigner des tickets à des utilisateurs
- Définir des priorités (basse, normale, haute, critique, urgente)
- Ajouter des commentaires et suivis
- Résoudre et fermer les tickets
- Générer des rapports statistiques

### 3. Suivi des tickets (Utilisateurs)

Les utilisateurs connectés peuvent :
- Voir leurs propres tickets via "My Tickets"
- Suivre l'état de leurs demandes (Ouvert, En cours, Résolu, Fermé)
- Ajouter des commentaires supplémentaires
- Recevoir des notifications

---

## Installation et Configuration

### 1. Dépendances installées

Les packages suivants ont été ajoutés au projet :

```python
# requirements-base.in
django-helpdesk
```

**Dépendances automatiques** :
- `django-bootstrap4form` : Pour le formatage des formulaires
- `djangorestframework` : Pour l'API REST de Helpdesk

### 2. Configuration dans `settings.py`

```python
INSTALLED_APPS = [
    # ...
    'django.contrib.humanize',  # Requis pour les dates humanisées
    'bootstrap4form',           # Formatage des formulaires
    'rest_framework',          # API REST
    'helpdesk',                # Application principale
]

# Configuration Django-Helpdesk
HELPDESK_TEAMS_MODE_ENABLED = False
SITE_ID = 1

# 🔒 Sécurité : Désactiver l'accès public
# Seuls les utilisateurs connectés peuvent accéder à Helpdesk
HELPDESK_SUBMIT_A_TICKET_PUBLIC = False
HELPDESK_VIEW_A_TICKET_PUBLIC = False

# Formulaires personnalisés
HELPDESK_PUBLIC_TICKET_FORM_CLASS = 'helpdesk_custom.forms.CustomPublicTicketForm'
HELPDESK_TICKET_FORM_CLASS = 'helpdesk_custom.forms.CustomTicketForm'
```

### 3. Configuration des URLs

```python
# observations_nids/urls.py
urlpatterns = [
    # ...
    path('helpdesk/', include('helpdesk.urls')),
]
```

### 4. Création du dossier média

Le système de pièces jointes nécessite un dossier spécifique :

```
media/
  └── helpdesk/
      └── attachments/  # Dossier pour les fichiers joints aux tickets
```

---

## Personnalisation

### 1. Templates personnalisés

Les templates suivants ont été créés dans `templates/helpdesk/` :

#### `base.html`
Template de base qui intègre :
- La navbar du site (Accueil, Admin, Support)
- Le menu latéral (sidebar) de Helpdesk
- Structure en deux colonnes (sidebar + contenu)
- CSS et JS originaux de Helpdesk
- Harmonisation avec la charte graphique du site

**Caractéristiques** :
- Sidebar : fond sombre (#343a40) avec survol vert (#4CAF50)
- Espacement de 1cm entre sidebar et contenu
- Boutons verts harmonisés avec le site

#### `create_ticket.html`
Formulaire de création de tickets pour utilisateurs connectés :
- Utilise `bootstrap4form` pour un rendu automatique
- CSS personnalisé pour espacements
- Carte centrée avec belle mise en page

#### `public_create_ticket.html`
Formulaire de création de tickets pour utilisateurs non connectés :
- Même structure que `create_ticket.html`
- Formulaire simplifié (moins de champs)

### 2. Formulaires personnalisés

Module créé : `helpdesk_custom/forms.py`

```python
from helpdesk.forms import PublicTicketForm, TicketForm
from django.utils.translation import gettext_lazy as _

class CustomPublicTicketForm(PublicTicketForm):
    """Formulaire personnalisé pour les tickets publics"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Changer "File" en "Catégorie"
        if 'queue' in self.fields:
            self.fields['queue'].label = _('Catégorie')

class CustomTicketForm(TicketForm):
    """Formulaire personnalisé pour les tickets (utilisateurs connectés)"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'queue' in self.fields:
            self.fields['queue'].label = _('Catégorie')
```

### 3. Queues (Catégories) créées

Quatre queues ont été configurées en base de données :

| Queue | Slug | Description | Public |
|-------|------|-------------|--------|
| Bug | `bug` | Signaler des bugs | ✅ |
| Nouvelle fonctionnalité | `feature` | Demander des améliorations | ✅ |
| Support / Question | `support` | Poser des questions | ✅ |
| Documentation | `documentation` | Problèmes de docs | ✅ |

**Création via Django shell** :
```python
from helpdesk.models import Queue

Queue.objects.create(
    title='Bug',
    slug='bug',
    email_address='bug@support.local',
    allow_public_submission=True
)
# ... (répéter pour les autres queues)
```

---

## Structure de navigation

### Menu latéral (Sidebar)

Pour les **utilisateurs non connectés** :
- Homepage
- New Ticket
- My Tickets (si connecté)
- Knowledgebase (si activée)

Pour le **staff/administrateurs** :
- Dashboard
- All Tickets
- Saved Queries
- Manage Saved Queries
- New Ticket
- My Tickets
- Reports
- Knowledgebase

### Menu principal du site

Le lien "**Support**" a été ajouté à la navbar principale dans :
- `observations/templates/includes/header.html`
- `observations/templates/components/navbar.html`

```html
<a href="{% url 'helpdesk:home' %}">Support</a>
```

---

## Utilisation

### Créer un ticket (Utilisateur)

1. Cliquer sur "Support" dans le menu principal
2. Ou aller directement sur `/helpdesk/tickets/submit/`
3. Remplir le formulaire :
   - **Catégorie** : Choisir Bug, Fonctionnalité, Support ou Documentation
   - **Titre** : Résumé court du problème
   - **Description** : Description détaillée
   - **Priorité** : Basse, Normale, Haute, Critique, Urgente
   - **Date de résolution souhaitée** (optionnel)
   - **Pièce jointe** (optionnel)
   - **Email** (si non connecté)
4. Cliquer sur "Submit Ticket"

### Gérer les tickets (Administrateur)

1. Se connecter en tant que staff
2. Aller sur `/helpdesk/`
3. Utiliser le **Dashboard** pour voir les statistiques
4. **All Tickets** pour voir la liste complète
5. Cliquer sur un ticket pour :
   - Voir les détails
   - Ajouter un commentaire
   - Changer le statut (Ouvert → En cours → Résolu → Fermé)
   - Assigner à un utilisateur
   - Modifier la priorité

### Rechercher et filtrer

1. Utiliser les filtres dans "All Tickets"
2. Créer des **Saved Queries** pour les recherches fréquentes
3. Utiliser la recherche globale

---

## Modèle de données

### Principaux modèles

#### `Queue` (File/Catégorie)
- `title` : Nom affiché
- `slug` : Identifiant unique
- `email_address` : Email de la queue
- `allow_public_submission` : Autoriser soumissions publiques
- `default_owner` : Propriétaire par défaut

#### `Ticket`
- `title` : Titre du ticket
- `queue` : Catégorie (FK vers Queue)
- `created` : Date de création
- `modified` : Dernière modification
- `submitter_email` : Email du créateur
- `assigned_to` : Assigné à (FK vers User)
- `status` : Statut (Ouvert, En cours, Résolu, Fermé, En attente)
- `description` : Description complète
- `priority` : 1-5 (Basse à Urgente)
- `due_date` : Date d'échéance
- `resolution` : Résolution du ticket

#### `FollowUp`
- `ticket` : Ticket associé (FK)
- `date` : Date du suivi
- `comment` : Commentaire
- `user` : Utilisateur (FK)
- `new_status` : Nouveau statut

---

## API REST

Django-Helpdesk expose une API REST pour l'intégration externe.

### Endpoints disponibles

```
GET  /helpdesk/api/tickets/          # Liste des tickets
GET  /helpdesk/api/tickets/{id}/     # Détails d'un ticket
POST /helpdesk/api/tickets/          # Créer un ticket
PUT  /helpdesk/api/tickets/{id}/     # Modifier un ticket
```

**Authentification** : Token ou session Django

---

## Permissions

### Permissions Django

- `helpdesk.view_ticket` : Voir les tickets
- `helpdesk.add_ticket` : Créer des tickets
- `helpdesk.change_ticket` : Modifier des tickets
- `helpdesk.delete_ticket` : Supprimer des tickets

### Accès public

⚠️ **Configuration actuelle** : L'accès public est **DÉSACTIVÉ** pour des raisons de sécurité.

Les paramètres suivants sont configurés :
- `HELPDESK_SUBMIT_A_TICKET_PUBLIC = False` → Les utilisateurs doivent être connectés pour créer des tickets
- `HELPDESK_VIEW_A_TICKET_PUBLIC = False` → Les utilisateurs doivent être connectés pour voir leurs tickets

**Raisons de cette configuration** :
- ✅ Traçabilité : Tous les tickets sont liés à des comptes utilisateurs
- ✅ Sécurité : Pas de spam ou de création anonyme de tickets
- ✅ Cohérence : L'application nécessite déjà une authentification pour les autres fonctionnalités

**Pour activer l'accès public** (non recommandé) :
```python
# settings.py
HELPDESK_SUBMIT_A_TICKET_PUBLIC = True
HELPDESK_VIEW_A_TICKET_PUBLIC = True
```

---

## Maintenance

### Commandes de gestion

```bash
# Créer une queue
python manage.py shell
>>> from helpdesk.models import Queue
>>> Queue.objects.create(title='Test', slug='test', ...)

# Voir les queues
>>> Queue.objects.all()

# Voir les tickets
>>> from helpdesk.models import Ticket
>>> Ticket.objects.all()
```

### Nettoyage

```bash
# Supprimer les tickets fermés de plus de X jours
# (à configurer dans les settings de Helpdesk)
python manage.py helpdesk_cleanup
```

---

## Personnalisations futures possibles

### 1. Email automatique

Configurer l'envoi d'emails automatiques :
```python
# settings.py
HELPDESK_EMAIL_SUBJECT_TEMPLATE = "Ticket #{ticket_id}: {ticket_title}"
HELPDESK_EMAIL_FALLBACK_LOCALE = 'fr'
```

### 2. Notifications

Activer les notifications pour :
- Nouveau ticket créé
- Ticket assigné
- Commentaire ajouté
- Statut modifié

### 3. Knowledgebase

Activer la base de connaissances :
```python
HELPDESK_KB_ENABLED = True
```

### 4. Intégration externe

Connecter Helpdesk à :
- Slack/Discord (notifications)
- Email (création de tickets par email)
- GitHub Issues (synchronisation)

---

## Dépannage

### Problème : "No public queues defined"

**Solution** : Créer au moins une queue avec `allow_public_submission=True`

### Problème : Formulaire non stylisé

**Solution** : Vérifier que `bootstrap4form` est installé et dans `INSTALLED_APPS`

### Problème : Pièces jointes ne fonctionnent pas

**Solution** : Vérifier que le dossier `media/helpdesk/attachments/` existe et est accessible en écriture

### Problème : Menu latéral caché

**Solution** : Forcer le rechargement (Ctrl+F5) pour recharger le CSS personnalisé

---

## Ressources

- **Documentation officielle** : [django-helpdesk.readthedocs.io](https://django-helpdesk.readthedocs.io/)
- **GitHub** : [github.com/django-helpdesk/django-helpdesk](https://github.com/django-helpdesk/django-helpdesk)
- **Templates personnalisés** : `templates/helpdesk/`
- **Formulaires personnalisés** : `helpdesk_custom/forms.py`

---

## Changelog

### Version initiale (28 octobre 2024)

✅ **Installation et configuration**
- Installation de django-helpdesk et dépendances
- Configuration dans settings.py et urls.py
- Création du dossier media/helpdesk/attachments/

✅ **Personnalisation visuelle**
- Template base.html avec navbar et sidebar
- Intégration de la charte graphique du site
- Templates personnalisés pour formulaires

✅ **Queues (Catégories)**
- Création de 4 queues : Bug, Fonctionnalité, Support, Documentation
- Label "File" renommé en "Catégorie"

✅ **Formulaires personnalisés**
- CustomPublicTicketForm et CustomTicketForm
- Harmonisation des mises en page

✅ **Navigation**
- Ajout du lien "Support" dans la navbar principale
- Menu latéral fonctionnel avec toutes les sections

✅ **Sécurité**
- Désactivation de l'accès public (HELPDESK_SUBMIT_A_TICKET_PUBLIC = False)
- Authentification obligatoire pour créer et voir les tickets
- Protection contre le spam et création anonyme

---

## Auteur

Documentation rédigée suite à l'intégration de Django-Helpdesk dans le projet Observations Nids.

🤖 Généré avec Claude Code
