# Guide de Géolocalisation

Ce guide complet décrit le système de géolocalisation et de géocodage automatique des observations dans le projet "Observations Nids".

---

## 📋 Table des matières

1. [Vue d'ensemble](#1-vue-densemble)
2. [Base de données des communes françaises](#2-base-de-donnees-des-communes-francaises)
3. [Stratégie de géocodage](#3-strategie-de-geocodage)
4. [Installation et configuration](#4-installation-et-configuration)
5. [Utilisation](#5-utilisation)
6. [APIs et intégration](#6-apis-et-integration)
7. [Optimisations et performances](#7-optimisations-et-performances)
8. [Dépannage et maintenance](#8-depannage-et-maintenance)
9. [Référence technique](#9-reference-technique)

---

## 1. Vue d'ensemble

### Contexte et problématique

Les fiches manuscrites d'observation contiennent uniquement le **nom de la commune** (et parfois le département), mais pas de coordonnées GPS précises.

**Niveau de précision actuel :**
- ✅ Nom de commune (ex: "Chamonix-Mont-Blanc")
- ✅ Département (ex: "Haute-Savoie" ou "74")
- ⚠️ Parfois un lieu-dit (ex: "Les Praz")
- ❌ Pas de coordonnées GPS précises

**Objectif :**
Transformer automatiquement le nom de commune en coordonnées GPS pour :
- Afficher les observations sur une carte
- Permettre des recherches géographiques
- Enrichir les données avec une localisation approximative

**Précision attendue :**
- Point GPS au centre de la commune (~5 km de précision)
- Suffisant pour l'affichage cartographique
- Plus précis que le département, moins précis qu'un GPS de terrain

### Architecture du système

Le système de géolocalisation fonctionne en deux niveaux :

**Niveau 1 : Base de données locale** (prioritaire)
- Cache de toutes les communes françaises (~35 000)
- Recherche quasi-instantanée sans appel API
- Gratuit et illimité
- Source : API Géoplateforme ([geo.api.gouv.fr](https://geo.api.gouv.fr))

**Niveau 2 : Géocodage en ligne** (fallback)
- Pour les cas non trouvés (erreurs OCR, anciennes communes, lieux-dits)
- Utilise Geopy + Nominatim (OpenStreetMap)
- Gratuit avec limite de 1 requête/seconde
- Gère les variations de noms de communes

### Fonctionnalités principales

✅ **Géocodage automatique** lors de la transcription OCR
✅ **Géocodage manuel** depuis l'interface de saisie
✅ **Autocomplétion** des communes avec distance GPS
✅ **Gestion intelligente de l'altitude** avec confirmation
✅ **Recherche géographique** par proximité
✅ **Pattern singleton** pour optimiser les ressources

---

## 2. Base de données des communes françaises

### Modèle de données `CommuneFrance`

Le modèle (`geo/models.py`) stocke pour chaque commune :

```python
class CommuneFrance(models.Model):
    """
    Cache des communes françaises pour géocodage rapide
    Source : API Géoplateforme (data.gouv.fr)
    """
    # Identification
    nom = models.CharField(max_length=200, db_index=True)
    code_insee = models.CharField(max_length=5, unique=True)
    code_postal = models.CharField(max_length=5, db_index=True)

    # Localisation administrative
    departement = models.CharField(max_length=100)
    code_departement = models.CharField(max_length=3, db_index=True)
    region = models.CharField(max_length=100, blank=True)

    # Coordonnées GPS (centre de la commune)
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)

    # Altitude moyenne de la commune
    altitude = models.IntegerField(null=True, blank=True)

    # Métadonnées
    population = models.IntegerField(null=True, blank=True)
    superficie = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True,
        help_text="Superficie en km²"
    )
    date_maj = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'geo_commune_france'
        verbose_name = 'Commune française'
        verbose_name_plural = 'Communes françaises'
        ordering = ['nom']
        indexes = [
            models.Index(fields=['nom', 'code_departement']),
            models.Index(fields=['code_postal']),
        ]
```

### Avantages de la base locale

- **Performance** : La recherche d'une commune est quasi-instantanée (~120ms)
- **Fiabilité** : Aucune dépendance à une API externe qui pourrait être lente ou indisponible
- **Gratuité** : Pas de limite de requêtes
- **Données officielles** : Source gouvernementale à jour

### Chargement de la base de données

Pour peupler cette base de données, une commande de gestion est fournie :

```bash
# À exécuter une seule fois lors de l'installation initiale
python manage.py charger_communes_france
```

Cette commande télécharge les données depuis l'API officielle [geo.api.gouv.fr](https://geo.api.gouv.fr/decoupage-administratif) et les charge dans la table `geo_commune_france`.

**Sortie attendue :**
```
📥 Téléchargement des communes depuis l'API Géoplateforme...
📦 35482 communes récupérées
💾 Chargement en base de données...

✅ Chargement terminé:
   • 35482 communes chargées
   • 0 erreurs

📊 Base de données:
   • 35482 communes
   • 101 départements
```

**Options de la commande :**

```bash
# Forcer le rechargement complet (mise à jour annuelle)
python manage.py charger_communes_france --force
```

**Temps d'exécution :** ~30 secondes pour charger toutes les communes.

---

## 3. Stratégie de géocodage

### Architecture du géocodeur

Le système utilise un utilitaire intelligent (`geo.utils.geocoding.GeocodeurCommunes`) qui opère en plusieurs niveaux pour trouver les coordonnées d'une commune.

```
┌─────────────────────────────────────┐
│ 1. Recherche en base locale         │
│    (Priorité 1 - Rapide)            │
├─────────────────────────────────────┤
│ ├─ Nom exact + département          │
│ ├─ Nom exact + code postal          │
│ ├─ Nom seul (si unique)             │
│ └─ Recherche floue (contient)       │
└─────────────────────────────────────┘
                 ↓ Si non trouvé
┌─────────────────────────────────────┐
│ 2. Fallback sur API externe         │
│    (Priorité 2 - Nominatim/OSM)     │
├─────────────────────────────────────┤
│ ├─ Commune + département            │
│ ├─ Lieu-dit (si disponible)         │
│ └─ Retry avec délai si timeout      │
└─────────────────────────────────────┘
```

### Pattern Singleton

Pour optimiser les ressources, le géocodeur est implémenté comme un **singleton**. Une seule instance est créée et réutilisée pour toutes les opérations de géocodage, évitant ainsi de multiples initialisations et connexions réseau.

```python
from geo.utils.geocoding import get_geocodeur

# Obtenir l'instance singleton
geocodeur = get_geocodeur()

# Géocoder une commune
coords = geocodeur.geocoder_commune("Chamonix-Mont-Blanc", "Haute-Savoie")
```

**Avantages :**
- ✅ Une seule instance réutilisée (économie de ressources)
- ✅ Réutilisation des connexions réseau Nominatim
- ✅ Performance améliorée de ~25%
- ✅ Pattern standard et reconnu

### Stratégies de recherche

Le géocodeur utilise **4 stratégies successives** pour trouver une commune dans la base locale :

**Stratégie 1 : Nom exact + département**
```python
# Exemple : "Chamonix-Mont-Blanc" + "Haute-Savoie"
result = CommuneFrance.objects.filter(
    nom__iexact="CHAMONIX-MONT-BLANC",
    departement__icontains="Haute-Savoie"
).first()
```

**Stratégie 2 : Nom exact + code postal**
```python
# Exemple : "Chamonix-Mont-Blanc" + "74400"
result = CommuneFrance.objects.filter(
    nom__iexact="CHAMONIX-MONT-BLANC",
    code_postal="74400"
).first()
```

**Stratégie 3 : Nom seul (si unique)**
```python
# Exemple : "Chamonix-Mont-Blanc" (unique en France)
results = CommuneFrance.objects.filter(nom__iexact="CHAMONIX-MONT-BLANC")
if results.count() == 1:
    return results.first()
```

**Stratégie 4 : Recherche floue (contient)**
```python
# Exemple : "Chamonix" trouve "Chamonix-Mont-Blanc"
result = CommuneFrance.objects.filter(
    nom__icontains="CHAMONIX",
    departement__icontains="Haute-Savoie"
).first()
```

### Gestion de l'altitude

Lors du géocodage, le système gère intelligemment le champ **altitude** :

#### Matrice de décision

| Valeur actuelle | Action | Confirmation |
|----------------|--------|--------------|
| Vide / `""` | ✅ Remplace automatiquement | Non |
| `"0"` | ✅ Remplace automatiquement | Non |
| `"0.0"` ou `"0.0m"` | ✅ Remplace automatiquement | Non |
| Valeur réelle (ex: `"1900"`) | ⚠️ Demande confirmation | **Oui** |

#### Exemple de confirmation

Lorsqu'une valeur réelle existe, l'utilisateur voit :

```
L'altitude actuelle est 1900m.
Voulez-vous la remplacer par 84m (altitude de Saint-James) ?

[OK] [Annuler]
```

**Choix :**
- **OK** → L'altitude devient `84` (altitude de la commune)
- **Annuler** → L'altitude reste `1900`, la commune change quand même

**Code de détection des valeurs nulles :**

```javascript
// Détecte toutes les variations de zéro
const shouldUpdate = !currentValue ||
                    currentValue === '' ||
                    currentValue === '0' ||
                    currentValue === '0.0' ||
                    currentValue.match(/^0(\.0+)?m?$/i) ||
                    (currentNumeric === 0 || isNaN(currentNumeric));
```

Cette regex matche :
- `"0"`, `"0.0"`, `"0.00"`, `"0.000"`
- `"0m"`, `"0.0m"`, `"0.00m"`
- `"0M"` (insensible à la casse)

### Géocodage avec lieu-dit

Le géocodeur peut tenter une recherche plus précise si un **lieu-dit** est disponible :

```python
coords = geocodeur.geocoder_avec_lieu_dit(
    commune="Chamonix-Mont-Blanc",
    departement="Haute-Savoie",
    lieu_dit="Les Praz"
)
```

**Stratégie :**
1. Essaie d'abord le lieu-dit via Nominatim (précision ~500m)
2. Si échec, fallback sur la commune seule (précision ~5000m)

---

## 4. Installation et configuration

### Dépendances requises

Ajouter à `requirements.txt` :

```txt
geopy==2.4.1
requests==2.31.0
```

Installer les dépendances :

```bash
pip install geopy requests
```

### Créer les migrations

Après avoir défini le modèle `CommuneFrance`, créer et appliquer les migrations :

```bash
python manage.py makemigrations geo
python manage.py migrate geo
```

### Charger les données initiales

```bash
# Premier chargement
python manage.py charger_communes_france

# Mise à jour annuelle (force le rechargement)
python manage.py charger_communes_france --force
```

### Configuration des fichiers statiques

**Fichier :** `observations_nids/settings.py`

```python
# Dossiers sources (développement)
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, "static"),  # ← Pour static/ racine
    os.path.join(BASE_DIR, "observations", "static"),
    os.path.join(BASE_DIR, "ingest", "static"),
]

# Dossier de collecte (production)
STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")  # ← Dossier séparé
```

**⚠️ Important :** `STATIC_ROOT` doit être **différent** de `STATICFILES_DIRS` pour éviter les conflits.

### Fichiers JavaScript

Le JavaScript de géocodage est externalisé pour meilleure maintenabilité :

**Fichier :** `static/Observations/js/saisie_observation.js`

Chargé dans le template avec cache busting :

```django
{% block extra_js %}
<script src="{% static 'Observations/js/saisie_observation.js' %}?v=3.3"></script>
{% endblock %}
```

Le `?v=3.3` force le navigateur à recharger le fichier lors de changements.

---

## 5. Utilisation

### Géocodage automatique (lors de la transcription)

Le géocodage est **automatiquement déclenché** lors de la transcription OCR des fiches manuscrites.

**Workflow :**

1. **OCR de l'image** → Extraction du texte (commune, département, lieu-dit)
2. **Création de la fiche** → Enregistrement en base de données
3. **Géocodage automatique** → Recherche des coordonnées GPS
4. **Mise à jour de la localisation** → Enregistrement des résultats

**Code d'intégration :**

```python
from geo.utils.geocoding import get_geocodeur

@shared_task(bind=True, max_retries=3)
def transcrire_et_geocoder_fiche(self, image_path):
    """Transcrit une fiche papier et géocode automatiquement la commune"""

    # 1. OCR de l'image
    donnees_ocr = extraire_texte_vision_api(image_path)

    # 2. Parser les données
    commune = donnees_ocr.get('commune', '').strip()
    departement = donnees_ocr.get('departement', '').strip()
    lieu_dit = donnees_ocr.get('lieu_dit', '').strip()

    # 3. Créer la fiche
    fiche = FicheObservation.objects.create(...)

    # 4. Géocodage automatique
    if commune:
        geocodeur = get_geocodeur()

        # Essayer avec lieu-dit si disponible
        if lieu_dit:
            coords = geocodeur.geocoder_avec_lieu_dit(commune, departement, lieu_dit)
        else:
            coords = geocodeur.geocoder_commune(commune, departement)

        if coords:
            # Mise à jour de la localisation
            fiche.localisation.coordonnees_gps = coords['coordonnees_gps']
            fiche.localisation.precision_gps = coords.get('precision_metres', 5000)
            fiche.localisation.source_coordonnees = coords['source']
            if 'code_insee' in coords:
                fiche.localisation.code_insee = coords['code_insee']
            fiche.localisation.save()

            logger.info(
                f"Fiche {fiche.num_fiche}: Commune géocodée "
                f"({commune} -> {coords['coordonnees_gps']}, source: {coords['source']})"
            )
```

### Géocodage manuel (depuis l'interface)

L'interface de saisie propose un **bouton de géocodage manuel** pour corriger ou compléter les coordonnées.

**Template :** `saisie_observation_optimise.html`

```django
<!-- Bouton de géocodage -->
<button type="button" id="btn-geocoder" class="btn btn-info"
        onclick="geocoderCommune(
            {{ fiche.num_fiche }},
            document.getElementById('id_localisation-commune').value,
            document.getElementById('id_localisation-departement').value,
            document.getElementById('id_localisation-lieu_dit').value
        )">
    <i class="fas fa-map-marker-alt"></i> Géocoder la commune
</button>
```

**JavaScript :**

```javascript
function geocoderCommune(ficheId, commune, departement, lieuDit) {
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;

    fetch('/geo/geocoder/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
            'X-CSRFToken': csrfToken
        },
        body: new URLSearchParams({
            'fiche_id': ficheId,
            'commune': commune,
            'departement': departement,
            'lieu_dit': lieuDit || ''
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Mettre à jour les champs GPS
            document.getElementById('id_localisation-coordonnees_gps').value =
                data.coords.coordonnees_gps;

            // Afficher un message de succès
            showNotification('success',
                `✓ Commune géocodée: ${data.adresse} (${data.source})`);

            // Si une carte existe, mettre à jour le marqueur
            if (typeof updateMapMarker === 'function') {
                updateMapMarker(data.coords.lat, data.coords.lon);
            }
        } else {
            showNotification('error', `✗ ${data.message}`);
        }
    });
}
```

### Autocomplétion des communes

Le système propose une **autocomplétion intelligente** avec calcul de distance GPS en temps réel.

**Fonctionnement :**

1. L'utilisateur tape les premières lettres (ex: "Blonv")
2. Le système interroge l'API `/geo/rechercher-communes/`
3. Les résultats sont triés par distance GPS (si position disponible)
4. Affichage avec nom, département, et distance

**Exemple d'affichage :**

```
Blonville-sur-Mer (14) - Calvados - 150m
Benerville-sur-Mer (14) - Calvados - 1.2km
Deauville (14) - Calvados - 2.5km
```

**Paramètres de l'API :**

```
GET /geo/rechercher-communes/?q=Blonv&lat=49.32&lon=0.03&limit=10
```

---

## 6. APIs et intégration

### API 1 : Géocodage manuel

**Endpoint :** `POST /geo/geocoder/`

**Rôle :** Géocode manuellement une commune pour une fiche d'observation donnée et met à jour ses coordonnées en base.

**Paramètres :**

| Paramètre | Type | Obligatoire | Description |
|-----------|------|-------------|-------------|
| `fiche_id` | integer | Oui | ID de la fiche à géocoder |
| `commune` | string | Oui | Nom de la commune |
| `departement` | string | Non | Nom ou code du département |
| `lieu_dit` | string | Non | Lieu-dit (pour précision accrue) |

**Réponse en cas de succès :**

```json
{
    "success": true,
    "coords": {
        "lat": 45.9237,
        "lon": 6.8694,
        "coordonnees_gps": "45.9237,6.8694",
        "precision": "commune",
        "precision_metres": 5000,
        "source": "base_locale",
        "adresse_complete": "Chamonix-Mont-Blanc, Haute-Savoie, France",
        "code_insee": "74056",
        "code_postal": "74400"
    },
    "message": "Commune géocodée avec succès",
    "adresse": "Chamonix-Mont-Blanc, Haute-Savoie, France",
    "source": "base_locale",
    "precision": "commune"
}
```

**Réponse en cas d'erreur :**

```json
{
    "success": false,
    "message": "Impossible de trouver la commune 'Chamonixx'"
}
```

**Code de la vue :**

```python
@login_required
@require_POST
def geocoder_commune_manuelle(request):
    """Vue AJAX pour géocoder manuellement une commune"""
    try:
        fiche_id = request.POST.get('fiche_id')
        commune = request.POST.get('commune', '').strip()
        departement = request.POST.get('departement', '').strip()
        lieu_dit = request.POST.get('lieu_dit', '').strip()

        if not fiche_id or not commune:
            return JsonResponse({
                'success': False,
                'message': 'Paramètres manquants (fiche_id, commune)'
            }, status=400)

        # Récupérer la fiche
        fiche = FicheObservation.objects.get(pk=fiche_id)

        # Géocoder
        geocodeur = get_geocodeur()

        if lieu_dit:
            coords = geocodeur.geocoder_avec_lieu_dit(commune, departement, lieu_dit)
        else:
            coords = geocodeur.geocoder_commune(commune, departement)

        if coords:
            # Mise à jour de la localisation
            fiche.localisation.coordonnees_gps = coords['coordonnees_gps']
            fiche.localisation.commune = commune
            if departement:
                fiche.localisation.departement = departement
            fiche.localisation.precision_gps = coords.get('precision_metres', 5000)
            fiche.localisation.source_coordonnees = 'geocodage_manuel'
            if 'code_insee' in coords:
                fiche.localisation.code_insee = coords['code_insee']
            fiche.localisation.save()

            return JsonResponse({
                'success': True,
                'coords': coords,
                'message': 'Commune géocodée avec succès',
                'adresse': coords.get('adresse_complete', ''),
                'source': coords.get('source', ''),
                'precision': coords.get('precision', '')
            })
        else:
            return JsonResponse({
                'success': False,
                'message': f"Impossible de trouver la commune '{commune}'"
            })

    except FicheObservation.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Fiche non trouvée'
        }, status=404)

    except Exception as e:
        logger.error(f"Erreur géocodage manuel: {e}")
        return JsonResponse({
            'success': False,
            'message': f"Erreur: {str(e)}"
        }, status=500)
```

### API 2 : Recherche de communes (autocomplétion)

**Endpoint :** `GET /geo/rechercher-communes/`

**Rôle :** API de recherche pour l'auto-complétion du champ "Commune" dans les formulaires. Retourne une liste de communes correspondant à la recherche de l'utilisateur, triées par distance GPS si des coordonnées sont fournies.

**Paramètres :**

| Paramètre | Type | Obligatoire | Description |
|-----------|------|-------------|-------------|
| `q` | string | Oui | Texte de recherche (min. 2 caractères) |
| `lat` | float | Non | Latitude pour tri par distance |
| `lon` | float | Non | Longitude pour tri par distance |
| `limit` | integer | Non | Nombre max de résultats (défaut: 10) |

**Réponse :**

```json
{
    "communes": [
        {
            "nom": "Chamonix-Mont-Blanc",
            "departement": "Haute-Savoie",
            "code_departement": "74",
            "code_postal": "74400",
            "code_insee": "74056",
            "latitude": 45.9237,
            "longitude": 6.8694,
            "altitude": 1035,
            "distance_km": 0.15
        },
        {
            "nom": "Les Houches",
            "departement": "Haute-Savoie",
            "code_departement": "74",
            "code_postal": "74310",
            "code_insee": "74143",
            "latitude": 45.8933,
            "longitude": 6.8019,
            "altitude": 1004,
            "distance_km": 4.2
        }
    ]
}
```

**Code de la vue avec calcul de distance optimisé :**

```python
@login_required
def rechercher_communes(request):
    """API de recherche de communes avec tri par distance GPS"""
    query = request.GET.get('q', '').strip()
    lat = request.GET.get('lat')
    lon = request.GET.get('lon')
    limit = int(request.GET.get('limit', 10))

    if len(query) < 2:
        return JsonResponse({'communes': []})

    # Recherche en base
    communes = CommuneFrance.objects.filter(
        nom__icontains=query
    ).values(
        'nom', 'departement', 'code_departement', 'code_postal',
        'code_insee', 'latitude', 'longitude', 'altitude'
    )[:limit]

    # Calcul de distance si coordonnées fournies
    if lat and lon:
        from math import atan2, cos, radians, sin, sqrt

        # Précalcul des conversions (optimisation)
        lat_rad = radians(float(lat))
        lon_rad = radians(float(lon))

        for commune in communes:
            lat2_rad = radians(float(commune['latitude']))
            lon2_rad = radians(float(commune['longitude']))

            dlat = lat2_rad - lat_rad
            dlon = lon2_rad - lon_rad

            # Formule de Haversine complète (précision à quelques mètres)
            a = sin(dlat/2)**2 + cos(lat_rad) * cos(lat2_rad) * sin(dlon/2)**2
            c = 2 * atan2(sqrt(a), sqrt(1-a))
            distance_km = 6371 * c  # Rayon de la Terre en km

            commune['distance_km'] = round(distance_km, 2)

        # Trier par distance
        communes = sorted(communes, key=lambda x: x['distance_km'])

    return JsonResponse({'communes': list(communes)})
```

**Formule de Haversine :**

Cette formule calcule la distance entre deux points sur une sphère (la Terre) en tenant compte de la courbure terrestre. Elle est précise à quelques mètres près et est la norme dans le domaine de la géolocalisation.

---

## 7. Optimisations et performances

### Singleton Pattern

**Avant :**
```python
# Nouvelle instance à chaque appel
geocodeur = GeocodeurCommunes()
```

**Après :**
```python
# Instance unique réutilisée
from geo.utils.geocoding import get_geocodeur
geocodeur = get_geocodeur()
```

**Avantages :**
- ✅ Économie de ressources (1 instance au lieu de N)
- ✅ Réutilisation des connexions réseau Nominatim
- ✅ Amélioration de performance de ~25%

### Requêtes de base de données optimisées

**Avant :**
```python
communes = CommuneFrance.objects.filter(
    nom__icontains=query
).only(
    'nom', 'departement', ...
).values(
    'nom', 'departement', ...
)[:limit]
```

**Après :**
```python
communes = CommuneFrance.objects.filter(
    nom__icontains=query
).values(
    'nom', 'departement', ...
)[:limit]
```

**Explication :** `.only()` avant `.values()` est redondant car `.values()` ne récupère que les champs spécifiés.

### JavaScript externalisé

**Avant :**
- 675 lignes de JavaScript inline dans le template
- Code dupliqué entre templates
- Difficile à maintenir et déboguer

**Après :**
- Fichier externe `saisie_observation.js` (28 Ko)
- Template réduit à une simple balise `<script>`
- Code réutilisable et maintenable
- Cache navigateur exploité

**Template :**
```django
{% block extra_js %}
<script src="{% static 'Observations/js/saisie_observation.js' %}?v=3.3"></script>
{% endblock %}
```

### Métriques de performance

| Opération | Avant | Après | Gain |
|-----------|-------|-------|------|
| Recherche commune | 150ms | 120ms | -20% |
| Calcul distance | 5ms | 3ms | -40% |
| Création ImportationService | 50ms | 10ms | -80% |
| **Import 100 fiches** | **~8s** | **~6s** | **-25%** |

---

## 8. Dépannage et maintenance

### Problèmes courants

#### Erreur 404 sur le fichier JavaScript

**Symptôme :** Console du navigateur affiche `404 Not Found` pour `saisie_observation.js`

**Cause :** Configuration `STATICFILES_DIRS` incomplète ou `STATIC_ROOT` en conflit

**Solution :**

1. **Vérifier la configuration** (`settings.py`) :
   ```python
   STATICFILES_DIRS = [
       os.path.join(BASE_DIR, "static"),  # ← Doit être présent
       os.path.join(BASE_DIR, "observations", "static"),
       os.path.join(BASE_DIR, "ingest", "static"),
   ]

   STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")  # ← Dossier séparé
   ```

2. **Vérifier la structure des fichiers :**
   ```
   projet/
   ├── static/
   │   └── Observations/
   │       └── js/
   │           └── saisie_observation.js
   ```

3. **Vider le cache du navigateur :**
   - Chrome : `Ctrl + Shift + Suppr` → Images et fichiers
   - Ou : Clic droit sur Actualiser → "Vider le cache et actualiser"

#### Altitude non mise à jour

**Symptôme :** L'altitude reste à `0.0m` même après changement de commune

**Cause :** Valeur `"0.0m"` non détectée comme nulle par JavaScript

**Solution :** Mise à jour du code JavaScript pour détecter toutes les variations de zéro :

```javascript
const shouldUpdate = !currentValue ||
                    currentValue === '' ||
                    currentValue === '0' ||
                    currentValue === '0.0' ||
                    currentValue.match(/^0(\.0+)?m?$/i) ||
                    (currentNumeric === 0 || isNaN(currentNumeric));
```

#### Cache navigateur agressif

**Symptôme :** Modifications du JavaScript non prises en compte

**Solutions :**

1. **Cache busting** (recommandé) :
   ```django
   <script src="{% static 'file.js' %}?v=3.4"></script>
   ```

2. **Mode navigation privée** (pour tester) :
   - Chrome : `Ctrl + Shift + N`
   - Firefox : `Ctrl + Shift + P`

3. **DevTools avec cache désactivé** :
   - F12 → Network → Cocher "Disable cache"
   - Garder DevTools ouvert

#### Commune non trouvée

**Symptôme :** Géocodage échoue même pour une commune valide

**Diagnostic :**

1. **Vérifier la base de données :**
   ```python
   python manage.py shell
   >>> from geo.models import CommuneFrance
   >>> CommuneFrance.objects.filter(nom__icontains="Chamonix").count()
   ```

2. **Vérifier les logs :**
   ```bash
   # Activer le logging dans settings.py
   LOGGING = {
       'loggers': {
           'geo': {
               'level': 'DEBUG',
           }
       }
   }
   ```

3. **Tester manuellement :**
   ```python
   from geo.utils.geocoding import get_geocodeur
   geocodeur = get_geocodeur()
   coords = geocodeur.geocoder_commune("Chamonix-Mont-Blanc", "Haute-Savoie")
   print(coords)
   ```

**Solutions :**

- Vérifier l'orthographe de la commune
- Essayer avec un département ou code postal
- Forcer le rechargement de la base : `python manage.py charger_communes_france --force`

### Commandes de maintenance

#### Mettre à jour la base des communes

```bash
# Mise à jour annuelle (force le rechargement)
python manage.py charger_communes_france --force
```

**Quand l'exécuter :**
- Une fois par an pour avoir les communes à jour
- Après une fusion de communes
- En cas de données corrompues

#### Réinitialiser les importations

Pour les environnements de développement, des commandes de réinitialisation sont disponibles :

```bash
# Réinitialisation complète (ATTENTION: perte de données)
python manage.py reset_importations

# Réinitialisation partielle (garder les fiches)
python manage.py reset_transcriptions
```

⚠️ **Ne JAMAIS exécuter en production !**

### Bonnes pratiques

✅ **Séparation des responsabilités**
- HTML dans templates
- CSS dans fichiers `.css`
- JavaScript dans fichiers `.js`
- Logique métier en Python

✅ **Pattern Singleton**
- Une seule instance du géocodeur
- Économie de ressources
- Réutilisation des connexions

✅ **Configuration Django**
- Variables d'environnement (`.env`)
- Settings validés
- Séparation dev/prod (`DEBUG`)

✅ **Gestion des fichiers statiques**
- `STATICFILES_DIRS` pour sources
- `STATIC_ROOT` pour collecte
- Cache busting pour versions

✅ **Expérience utilisateur**
- Autocomplétion intelligente
- Confirmation avant écrasement
- Messages clairs et contextuels
- Pas d'interruption du workflow

✅ **Performance**
- Requêtes DB optimisées
- Calculs précalculés (Haversine)
- Singleton pour ressources
- Cache navigateur exploité

---

## 9. Référence technique

### Modèle de données `Localisation`

**Fichier :** `geo/models.py`

```python
class Localisation(models.Model):
    # Champs de base
    commune = models.CharField(max_length=100)
    departement = models.CharField(max_length=100, blank=True)
    lieu_dit = models.CharField(max_length=200, blank=True)

    # Coordonnées GPS
    coordonnees_gps = models.CharField(
        max_length=50, blank=True,
        help_text="Format: latitude,longitude"
    )

    # Altitude
    altitude = models.IntegerField(null=True, blank=True)

    # Nouveaux champs pour le géocodage
    precision_gps = models.IntegerField(
        default=5000,
        help_text="Précision estimée en mètres (ex: 10m pour GPS terrain, 5000m pour commune)"
    )
    source_coordonnees = models.CharField(
        max_length=50,
        choices=[
            ('gps_terrain', 'GPS de terrain'),
            ('geocodage_auto', 'Géocodage automatique'),
            ('geocodage_manuel', 'Géocodage manuel'),
            ('carte', 'Pointé sur carte'),
            ('base_locale', 'Base locale des communes'),
            ('nominatim', 'Nominatim (OSM)'),
        ],
        default='geocodage_auto'
    )
    code_insee = models.CharField(
        max_length=5, blank=True,
        help_text="Code INSEE de la commune"
    )
```

### Sources de coordonnées

| Source | Précision | Origine | Usage |
|--------|-----------|---------|-------|
| `gps_terrain` | 5-20m | GPS physique (smartphone, appareil dédié) | Observations terrain |
| `base_locale` | 5000m | Base de données `geo_commune_france` | Géocodage prioritaire |
| `nominatim` | 5000m | API Nominatim (OpenStreetMap) | Géocodage fallback |
| `geocodage_auto` | 5000m | Géocodage lors transcription OCR | Automatique |
| `geocodage_manuel` | 5000m | Bouton "Géocoder la commune" | Utilisateur |
| `carte` | Variable | Sélection manuelle sur carte interactive | Interface future |

### Technologies utilisées

- **Django 5.1** - Framework web Python
- **Geopy 2.4.1** - Bibliothèque de géocodage
- **Nominatim** - Service de géocodage gratuit (OpenStreetMap)
- **API Géoplateforme** - API officielle française des communes
- **Bootstrap 5** - Framework CSS
- **Font Awesome 6** - Icônes

### Prochaines améliorations possibles

**Court terme :**
- [ ] Bouton "Forcer altitude de la commune" pour éviter la popup
- [ ] Indicateur visuel quand l'altitude provient de la commune vs saisie manuelle
- [ ] Tooltip sur le champ altitude montrant la source (commune/GPS/manuel)

**Moyen terme :**
- [ ] Cache Redis pour les résultats de géocodage
- [ ] API de géocodage en arrière-plan (Celery) pour gros imports
- [ ] Validation des coordonnées GPS (cohérence avec commune)
- [ ] Historique des modifications d'altitude

**Long terme :**
- [ ] Migration vers PostgreSQL avec index spatiaux (PostGIS)
- [ ] Recherche géographique avancée (rayon personnalisable)
- [ ] Export des données géographiques (KML, GeoJSON)
- [ ] Carte interactive pour sélection de commune

### Ressources et documentation

**Documentation officielle :**
- [Django Static Files](https://docs.djangoproject.com/en/5.1/howto/static-files/)
- [Haversine Formula](https://en.wikipedia.org/wiki/Haversine_formula)
- [Nominatim API](https://nominatim.org/release-docs/develop/api/Search/)
- [API Géoplateforme](https://geo.api.gouv.fr/decoupage-administratif)
- [Geopy Documentation](https://geopy.readthedocs.io/)

**Fichiers du projet :**
- `geo/models.py` - Modèles de données
- `geo/views.py` - APIs de géocodage
- `geo/utils/geocoding.py` - Utilitaire de géocodage
- `geo/management/commands/charger_communes_france.py` - Commande de chargement
- `static/Observations/js/saisie_observation.js` - JavaScript d'autocomplétion

---

**Document créé le** : 24/10/2025
**Version** : 1.0 (consolidé de 3 fichiers sources)
**Sources** :
- `features/geo/README.md` (69 lignes)
- `features/geo/archive/geocoding.md` (874 lignes)
- `features/geo/archive/optimisations_geocodage_altitude.md` (767 lignes)
