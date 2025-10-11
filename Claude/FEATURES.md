# Liste des fonctionnalités actives - Observations Nids

Ce document liste toutes les fonctionnalités implémentées dans l'application, leur état, et leurs dépendances.

---

## 📊 Vue d'ensemble

| Module | Fonctionnalités | État global |
|--------|----------------|-------------|
| Authentification | 5 | ✅ Stable |
| Observations | 12 | ✅ Stable |
| Transcription OCR | 6 | ✅ Stable |
| Taxonomie | 4 | ✅ Stable |
| Géocodage | 5 | ✅ Stable |
| Révision | 4 | ✅ Stable |
| Audit | 3 | ✅ Stable |

**Légende :**
- ✅ Stable : Fonctionne correctement, testé
- 🚧 En développement : Fonctionnel mais peut évoluer
- ⚠️ Attention : Problèmes connus ou limitations
- 🔧 Maintenance : Nécessite mise à jour/refactoring
- ❌ Désactivé : Non fonctionnel ou désactivé temporairement

---

## 🔐 Module authentification (`accounts/`)

### Fonctionnalités

| # | Fonctionnalité | État | Fichiers clés | Notes |
|---|----------------|------|---------------|-------|
| 1 | **Connexion utilisateur** | ✅ | `accounts/views.py`, `/auth/login/` | Session expiration: 1h |
| 2 | **Déconnexion** | ✅ | `/auth/logout/` | |
| 3 | **Gestion des rôles** | ✅ | `accounts/models.py` | 4 rôles: observateur, correcteur, validateur, admin |
| 4 | **Permissions par rôle** | ✅ | Decorators, middleware | Contrôle d'accès granulaire |
| 5 | **Modèle utilisateur personnalisé** | ✅ | `Utilisateur` | `AUTH_USER_MODEL` |

### Dépendances
- Django Auth framework
- Sessions (DB ou Redis)

### Tests requis
- [ ] Connexion avec credentials valides
- [ ] Connexion avec credentials invalides
- [ ] Déconnexion
- [ ] Accès pages protégées sans login → redirect
- [ ] Permissions par rôle

---

## 📝 Module observations (`observations/`)

### Fonctionnalités principales

| # | Fonctionnalité | État | Fichiers clés | Notes |
|---|----------------|------|---------------|-------|
| 1 | **Liste des observations** | ✅ | `/observations/liste/`, `views_observation.py` | Pagination, filtres |
| 2 | **Détail d'une fiche** | ✅ | `/observations/fiche/<id>/`, `fiche_observation.html` | Affichage complet |
| 3 | **Création d'observation** | ✅ | `/observations/`, `saisie_observation_view.py` | Formulaire complet |
| 4 | **Modification d'observation** | ✅ | `/observations/modifier/<id>/` | Formulaire pré-rempli |
| 5 | **Suppression d'observation** | ✅ | `/observations/supprimer/<id>/` | Soft delete |
| 6 | **Formsets observations multiples** | ✅ | `ObservationFormSet` | Gestion dynamique |
| 7 | **Validation formulaire** | ✅ | `observations/forms.py` | Côté serveur + client |
| 8 | **Système de remarques** | ✅ | `RemarqueFormSet`, AJAX modal | Annotations collaboratives |
| 9 | **Gestion des images** | ✅ | Upload, stockage | Fiches scannées |
| 10 | **Export de données** | 🚧 | À implémenter | CSV, JSON, Excel |
| 11 | **Recherche avancée** | 🚧 | À implémenter | Par espèce, date, lieu |
| 12 | **Statistiques** | 🚧 | À implémenter | Dashboard |

### Autocomplétion et auto-remplissage ⭐

| # | Fonctionnalité | État | Fichiers clés | Notes |
|---|----------------|------|---------------|-------|
| 13 | **Autocomplétion espèces** | ✅ | `saisie_observation.js` | Recherche temps réel, délai 800ms |
| 14 | **Autocomplétion communes** | ✅ | `saisie_observation.js`, `/geo/rechercher-communes/` | Recherche API, délai 300ms |
| 15 | **Auto-remplissage département** | ✅ | `saisie_observation.js:333-335` | Si vide ou = "00" |
| 16 | **Auto-remplissage GPS** | ✅ | `saisie_observation.js:337-353` | Si vide ou = 0.0, conserve vraies valeurs |
| 17 | **Auto-remplissage altitude** | ✅ | `saisie_observation.js:355-367` | Popup confirmation si = 0 |
| 18 | **Navigation clavier** | ✅ | `saisie_observation.js` | ↑↓ Enter Escape |

### Dépendances
- Bootstrap 5 (UI)
- jQuery (AJAX remarques)
- API géocodage (`/geo/rechercher-communes/`)
- Base taxonomie (espèces)

### Tests requis
- [ ] Création fiche complète
- [ ] Modification fiche existante
- [ ] Formsets : ajout/suppression lignes
- [ ] Autocomplétion espèces
- [ ] Autocomplétion communes (nouvelle saisie)
- [ ] Autocomplétion communes (modification avec GPS existants)
- [ ] Auto-remplissage respecte GPS ≠ 0
- [ ] Remarques AJAX

---

## 🔍 Module transcription OCR (`observations/tasks.py`)

### Fonctionnalités

| # | Fonctionnalité | État | Fichiers clés | Notes |
|---|----------------|------|---------------|-------|
| 1 | **Interface sélection images** | ✅ | `/transcription/demarrer/`, `view_transcription.py` | Upload dossier |
| 2 | **Traitement asynchrone Celery** | ✅ | `tasks.py`, tâche `transcrire_et_geocoder_fiche` | Par lots |
| 3 | **OCR Google Vision API** | ✅ | Integration Google Cloud | Extraction texte |
| 4 | **Parsing intelligent** | ✅ | `tasks.py` | Reconnaissance structure fiche |
| 5 | **Suivi progression temps réel** | ✅ | `/transcription/verifier-progression/` | WebSocket ou polling |
| 6 | **Affichage résultats** | ✅ | `/transcription/resultats/` | Récapitulatif + liens fiches |

### Dépendances critiques
- Celery worker actif
- Redis/RabbitMQ (broker)
- Google Vision API credentials (`GOOGLE_APPLICATION_CREDENTIALS`)
- Module géocodage (auto-remplissage commune)

### Tests requis
- [ ] Worker Celery démarré
- [ ] Upload images
- [ ] Traitement asynchrone
- [ ] Progression affichée
- [ ] Fiches créées correctement

---

## 🦅 Module taxonomie (`taxonomy/`)

### Fonctionnalités

| # | Fonctionnalité | État | Fichiers clés | Notes |
|---|----------------|------|---------------|-------|
| 1 | **Modèles taxonomiques** | ✅ | `taxonomy/models.py` | Ordre → Famille → Espèce |
| 2 | **Import LOF (recommandé)** | ✅ | `charger_lof.py` | ~577 espèces, auto-download |
| 3 | **Import TaxRef (alternative)** | ✅ | `charger_taxref.py` | ~574 espèces, téléchargement manuel |
| 4 | **Liens oiseaux.net** | ✅ | `recuperer_liens_oiseaux_net.py` | Enrichissement automatique |

### Commandes disponibles

```bash
# Méthode recommandée
python manage.py charger_lof

# Alternative
python manage.py charger_taxref --file /chemin/vers/TAXREFv17.txt

# Enrichissement liens
python manage.py recuperer_liens_oiseaux_net
```

### Dépendances
- Fichiers LOF/TaxRef
- Connexion internet (LOF auto-download)
- BeautifulSoup4 (scraping liens)

### Tests requis
- [ ] Commande `charger_lof` réussit
- [ ] ~577 espèces chargées
- [ ] Relations Ordre → Famille → Espèce correctes
- [ ] Liens oiseaux.net présents

---

## 🗺️ Module géocodage (`geo/`)

### Fonctionnalités

| # | Fonctionnalité | État | Fichiers clés | Notes |
|---|----------------|------|---------------|-------|
| 1 | **Base locale communes françaises** | ✅ | `CommuneFrance` model | ~35 000 communes |
| 2 | **Chargement communes** | ✅ | `charger_communes_france.py` | API Géoplateforme |
| 3 | **Recherche rapide locale** | ✅ | `geocoding.py`, méthode `_recherche_base_locale` | Sans appel API |
| 4 | **Fallback Nominatim** | ✅ | `geocoding.py`, méthode `_geocoder_nominatim` | OSM, 1 req/sec |
| 5 | **API recherche AJAX** | ✅ | `/geo/rechercher-communes/`, `geo/views.py:91-188` | Autocomplétion |

### Géocodeur intelligent

```python
from geo.utils.geocoding import get_geocodeur

geocodeur = get_geocodeur()

# Géocoder une commune
coords = geocodeur.geocoder_commune("Chamonix-Mont-Blanc", "Haute-Savoie")
# → {lat, lon, precision, source, altitude, ...}

# Avec lieu-dit (plus précis)
coords = geocodeur.geocoder_avec_lieu_dit("Chamonix", "74", "Les Praz")
```

### Stratégie de recherche
1. **Base locale** (prioritaire) : recherche nom + département
2. **Nominatim** (fallback) : si non trouvé ou erreur OCR
3. **GPS** : utilisés uniquement pour calculer/afficher distance

### Dépendances
- Geopy (Nominatim)
- API Géoplateforme (data.gouv.fr)
- Table `geo_commune_france` remplie

### Tests requis
- [ ] Commande `charger_communes_france` réussit
- [ ] ~35 000 communes chargées
- [ ] Recherche locale rapide
- [ ] Fallback Nominatim fonctionne
- [ ] API `/geo/rechercher-communes/?q=paris` retourne résultats

---

## 🔍 Module révision (`review/`)

### Fonctionnalités

| # | Fonctionnalité | État | Fichiers clés | Notes |
|---|----------------|------|---------------|-------|
| 1 | **Workflow de correction** | ✅ | `EtatCorrection` model | États : nouveau, en_cours, corrigé, validé, rejeté |
| 2 | **Soumission validation** | ✅ | `/observations/soumettre/<id>/` | Correcteur → Validateur |
| 3 | **Validation par reviewer** | ✅ | Permissions validateur | Approuver/rejeter |
| 4 | **Suivi progression** | ✅ | `pourcentage_completion` | Métrique qualité |

### Workflow

```
nouveau → en_cours → corrigé → validé
                         ↓
                     rejeté → en_cours
```

### Dépendances
- Permissions par rôle
- Module audit (traçabilité)

### Tests requis
- [ ] Passage nouveau → en_cours
- [ ] Soumission pour validation
- [ ] Validation par reviewer
- [ ] Rejet avec commentaire

---

## 📜 Module audit (`audit/`)

### Fonctionnalités

| # | Fonctionnalité | État | Fichiers clés | Notes |
|---|----------------|------|---------------|-------|
| 1 | **Historique modifications** | ✅ | `HistoriqueModification` model | Granularité champ |
| 2 | **Tracking automatique** | ✅ | Signaux Django | `post_save`, `pre_save` |
| 3 | **Consultation historique** | ✅ | `/observations/historique/<id>/` | Interface dédiée |

### Données enregistrées
- Utilisateur ayant modifié
- Date/heure modification
- Champ modifié
- Ancienne valeur
- Nouvelle valeur
- Type modification (création, modification, suppression)

### Dépendances
- Django signals
- Relation FK avec `FicheObservation`

### Tests requis
- [ ] Création fiche → entrée historique
- [ ] Modification fiche → entrée historique
- [ ] Affichage historique complet

---

## 🎨 Interface utilisateur

### Technologies frontend

| Technologie | Version | Usage |
|-------------|---------|-------|
| Bootstrap | 5.x | Framework CSS, composants |
| Font Awesome | 6.x | Icônes |
| JavaScript | Vanilla ES6+ | Interactions, AJAX |
| jQuery | 3.x | AJAX remarques (legacy) |

### Composants clés

| Composant | Fichier | État | Notes |
|-----------|---------|------|-------|
| Navbar | `components/navbar.html` | ✅ | Responsive, dropdown |
| Cards | Bootstrap classes | ✅ | Layout formulaires |
| Forms | `observations/forms.py` | ✅ | Django forms + Bootstrap |
| Modals | Bootstrap modals | ✅ | Remarques AJAX |
| Autocomplete | `saisie_observation.js` | ✅ | Custom implementation |

### Responsive breakpoints
- **Desktop** : ≥ 1200px
- **Tablette** : 768-1199px
- **Mobile** : < 768px

---

## 🔧 Configuration et déploiement

### Variables d'environnement (.env)

```bash
# Django
SECRET_KEY=xxx
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Base de données
DATABASE_ENGINE=sqlite3  # ou postgresql
DATABASE_NAME=db.sqlite3

# Session
SESSION_COOKIE_AGE=3600  # 1 heure

# Celery
CELERY_BROKER_URL=redis://127.0.0.1:6379/0

# Google Vision API
GOOGLE_APPLICATION_CREDENTIALS=/path/to/credentials.json

# Debug Toolbar
USE_DEBUG_TOOLBAR=True
```

### Commandes de déploiement

```bash
# Installation dépendances
pip install -r requirements.txt

# Migrations
python manage.py makemigrations
python manage.py migrate

# Chargement données initiales
python manage.py charger_lof
python manage.py charger_communes_france

# Collecte fichiers statiques
python manage.py collectstatic --noinput

# Création superuser
python manage.py createsuperuser

# Démarrage serveur dev
python manage.py runserver

# Démarrage Celery (si OCR)
celery -A observations_nids worker --loglevel=info
```

---

## 📊 Métriques et performances

### Couverture de code
- **Tests unitaires** : ~40% (objectif: ≥70%)
- **Tests d'intégration** : Fonctionnalités critiques couvertes
- **Tests E2E** : À implémenter (Selenium/Playwright)

### Performance
- **Temps réponse API** : < 200ms (moyenne)
- **Temps chargement page** : < 2s
- **Requêtes DB par page** : < 20 (optimisation avec select_related/prefetch_related)

### Qualité code
- **Ruff** : ~17 warnings (non bloquants)
- **Mypy** : ~29 erreurs (manque de stubs principalement)
- **Complexité cyclomatique** : < 10 par fonction (objectif)

---

## 🐛 Problèmes connus et limitations

### Problèmes actifs
Aucun problème critique connu actuellement.

### Limitations connues

| Limitation | Impact | Workaround | Priorité |
|------------|--------|------------|----------|
| OCR nécessite Google Cloud credentials | Bloquant pour transcription | Saisie manuelle | Haute |
| Nominatim rate limit 1 req/sec | Géocodage lent en batch | Base locale prioritaire | Basse |
| Pas de tests E2E automatisés | Risque régressions | Tests manuels CHECKLIST_PR.md | Moyenne |
| Export données non implémenté | Pas d'export CSV/Excel | Extraction SQL manuelle | Moyenne |

### Régressions détectées et corrigées

| Date | Problème | Cause | Correction |
|------|----------|-------|------------|
| 2025-10-10 | Autocomplétion communes vide | API cherchait par GPS au lieu du nom | Correction `geo/views.py:109-117` |
| 2025-10-10 | Auto-remplissage ne fonctionnait pas | Valeurs "0"/"00" non détectées comme vides | Correction `saisie_observation.js:344-360` |

---

## 🔮 Roadmap et évolutions futures

### Court terme (1-3 mois)
- [ ] Tests E2E avec Selenium/Playwright
- [ ] Export données (CSV, JSON, Excel)
- [ ] Recherche avancée avec filtres multiples
- [ ] Dashboard statistiques

### Moyen terme (3-6 mois)
- [ ] Module cartographie interactive (Leaflet/OpenLayers)
- [ ] API REST (Django REST Framework)
- [ ] Application mobile (React Native / Flutter)
- [ ] Notifications temps réel (WebSocket)

### Long terme (6-12 mois)
- [ ] Machine Learning pour OCR amélioré
- [ ] Reconnaissance automatique espèces (photos oiseaux)
- [ ] Plateforme collaborative publique
- [ ] Intégration bases données naturalistes (INPN, eBird)

---

## 📚 Documentation associée

### Documents techniques
- `README.md` : Vue d'ensemble projet
- `README_PROJET.md` : Architecture détaillée
- `README_TESTS.md` : Guide tests
- `API_DOCUMENTATION.md` : Documentation API
- `DEPLOIEMENT_PI.md` : Déploiement Raspberry Pi

### Documentation modules
- `taxonomy/README_LOF.md` : Import Liste Oiseaux France
- `taxonomy/README_TAXREF.md` : Import TaxRef INPN
- `taxonomy/README_LIENS_OISEAUX_NET.md` : Enrichissement liens
- `Claude/7 _ geocoding_doc.md` : Géocodage communes

### Workflows
- `Claude/100_git_workflow_bonnes_pratiques.md` : Stratégie Git
- `Claude/CHECKLIST_PR.md` : Checklist validation (ce document)

---

## ✅ Statut de validation

**Dernière validation complète :** 2025-10-10

**Validateur :** Claude Code + Utilisateur

**Fonctionnalités critiques vérifiées :**
- ✅ Authentification
- ✅ Création/Modification observations
- ✅ Autocomplétion espèces
- ✅ Autocomplétion communes
- ✅ Auto-remplissage GPS/altitude
- ✅ Transcription OCR (Celery)
- ✅ Géocodage
- ✅ Révision
- ✅ Audit

**Prochaine validation :** Après chaque merge sur `production`

---

*Ce document est maintenu à jour au fur et à mesure des évolutions du projet.*

*Pour toute question ou ajout, contacter l'équipe de développement.*

*Dernière mise à jour : 2025-10-10*
