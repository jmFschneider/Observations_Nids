# Géocodage automatique des communes françaises

## Contexte et besoin

### Problématique

Les fiches manuscrites d'observation contiennent uniquement le **nom de la commune** (et parfois le département), mais pas de coordonnées GPS précises. 

**Niveau de précision actuel :**
- ✅ Nom de commune (ex: "Chamonix-Mont-Blanc")
- ✅ Département (ex: "Haute-Savoie" ou "74")
- ⚠️ Parfois un lieu-dit (ex: "Les Praz")
- ❌ Pas de coordonnées GPS précises

**Objectif :**
Transformer automatiquement le nom de commune en coordonnées GPS pour :
- Afficher les observations sur une carte
- Permettre des recherches géographiques basiques
- Enrichir les données avec une localisation approximative

**Précision attendue :**
- Point GPS au centre de la commune (~5 km de précision)
- Suffisant pour l'affichage cartographique
- Plus précis que le département, moins précis qu'un GPS de terrain

---

## Solution technique recommandée

### Architecture en deux niveaux

**Niveau 1 : Base de données locale** (prioritaire)
- Cache de toutes les communes françaises (~35 000)
- Recherche instantanée sans appel API
- Gratuit et illimité
- Source : API Géoplateforme (data.gouv.fr)

**Niveau 2 : Géocodage en ligne** (fallback)
- Pour les cas non trouvés (erreurs OCR, anciennes communes, lieux-dits)
- Utilise Geopy + Nominatim (OpenStreetMap)
- Gratuit avec limite de 1 requête/seconde
- Gère les variations de noms de communes

### Technologies utilisées

- **Geopy** : Bibliothèque Python de géocodage
- **Nominatim** : Service de géocodage gratuit (OpenStreetMap)
- **API Géoplateforme** : API officielle française des communes
- **Django models** : Cache en base de données

---

## Implémentation

### 1. Installation des dépendances

```bash
# Ajouter à requirements.txt
geopy==2.4.1
requests==2.31.0

# Installer
pip install geopy requests
```

### 2. Modèle de cache des communes

**Fichier : `geo/models.py`**

Ajouter ce modèle à l'application `geo` :

```python
from django.db import models

class CommuneFrance(models.Model):
    """
    Cache des communes françaises pour géocodage rapide
    Source : API Géoplateforme (data.gouv.fr)
    """
    # Identification
    nom = models.CharField(max_length=200, db_index=True)
    code_insee = models.CharField(max_length=5, unique=True, help_text="Code INSEE de la commune")
    code_postal = models.CharField(max_length=5, db_index=True)
    
    # Localisation administrative
    departement = models.CharField(max_length=100)
    code_departement = models.CharField(max_length=3, db_index=True)
    region = models.CharField(max_length=100, blank=True)
    
    # Coordonnées GPS (centre de la commune)
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    
    # Métadonnées
    population = models.IntegerField(null=True, blank=True)
    superficie = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="Superficie en km²")
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
    
    def __str__(self):
        return f"{self.nom} ({self.code_departement})"
    
    @property
    def coordonnees_gps(self):
        """Retourne les coordonnées au format 'lat,lon'"""
        return f"{self.latitude},{self.longitude}"
```

**Créer et appliquer la migration :**

```bash
python manage.py makemigrations geo
python manage.py migrate geo
```

### 3. Management command pour charger les communes

**Fichier : `geo/management/commands/charger_communes_france.py`**

```python
from django.core.management.base import BaseCommand
import requests
from geo.models import CommuneFrance

class Command(BaseCommand):
    help = 'Charge la base des communes françaises depuis l\'API Géoplateforme'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force le rechargement même si des communes existent déjà',
        )
    
    def handle(self, *args, **options):
        # Vérifier si déjà chargé
        if CommuneFrance.objects.exists() and not options['force']:
            count = CommuneFrance.objects.count()
            self.stdout.write(
                self.style.WARNING(
                    f'⚠️  {count} communes déjà en base. '
                    'Utilisez --force pour recharger.'
                )
            )
            return
        
        # URL de l'API Géoplateforme
        url = "https://geo.api.gouv.fr/communes"
        params = {
            'fields': 'nom,code,codesPostaux,centre,departement,region,population,surface',
            'format': 'json',
            'geometry': 'centre'
        }
        
        self.stdout.write("📥 Téléchargement des communes depuis l'API Géoplateforme...")
        
        try:
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            communes = response.json()
        except requests.RequestException as e:
            self.stdout.write(self.style.ERROR(f'❌ Erreur lors du téléchargement: {e}'))
            return
        
        self.stdout.write(f"📦 {len(communes)} communes récupérées")
        self.stdout.write("💾 Chargement en base de données...")
        
        # Supprimer les anciennes données si --force
        if options['force']:
            deleted_count = CommuneFrance.objects.all().delete()[0]
            self.stdout.write(f"🗑️  {deleted_count} anciennes communes supprimées")
        
        # Charger les nouvelles données
        communes_objects = []
        erreurs = 0
        
        for commune in communes:
            try:
                # Extraire les coordonnées (attention: l'API retourne [lon, lat])
                centre = commune.get('centre', {}).get('coordinates', [None, None])
                longitude = centre[0]
                latitude = centre[1]
                
                if latitude is None or longitude is None:
                    erreurs += 1
                    continue
                
                # Créer l'objet commune
                commune_obj = CommuneFrance(
                    code_insee=commune['code'],
                    nom=commune['nom'],
                    code_postal=commune.get('codesPostaux', [''])[0],
                    departement=commune['departement']['nom'],
                    code_departement=commune['departement']['code'],
                    region=commune.get('region', {}).get('nom', ''),
                    latitude=latitude,
                    longitude=longitude,
                    population=commune.get('population'),
                    superficie=commune.get('surface', 0) / 10000  # m² vers km²
                )
                communes_objects.append(commune_obj)
                
            except (KeyError, IndexError, TypeError) as e:
                erreurs += 1
                self.stdout.write(
                    self.style.WARNING(f"⚠️  Erreur commune {commune.get('nom', '?')}: {e}")
                )
        
        # Insertion en masse
        CommuneFrance.objects.bulk_create(communes_objects, batch_size=1000)
        
        # Rapport final
        self.stdout.write(
            self.style.SUCCESS(
                f"\n✅ Chargement terminé:\n"
                f"   • {len(communes_objects)} communes chargées\n"
                f"   • {erreurs} erreurs"
            )
        )
        
        # Statistiques
        total = CommuneFrance.objects.count()
        depts = CommuneFrance.objects.values('departement').distinct().count()
        self.stdout.write(
            self.style.SUCCESS(
                f"\n📊 Base de données:\n"
                f"   • {total} communes\n"
                f"   • {depts} départements"
            )
        )
```

**Exécuter la commande :**

```bash
# Premier chargement
python manage.py charger_communes_france

# Forcer un rechargement
python manage.py charger_communes_france --force
```

### 4. Utilitaire de géocodage intelligent

**Fichier : `geo/utils/geocoding.py`**

Créer le répertoire et le fichier :

```bash
mkdir -p geo/utils
touch geo/utils/__init__.py
```

```python
"""
Utilitaire de géocodage intelligent pour les communes françaises
Utilise en priorité la base locale, puis Nominatim en fallback
"""

from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError
import time
import logging
from typing import Optional, Dict
from geo.models import CommuneFrance

logger = logging.getLogger(__name__)


class GeocodeurCommunes:
    """
    Géocodeur intelligent pour les communes françaises
    
    Stratégie:
    1. Recherche en base locale (rapide, gratuit)
    2. Fallback sur Nominatim (pour erreurs OCR, anciennes communes)
    """
    
    def __init__(self):
        self.geolocator = Nominatim(
            user_agent="observations_nids/1.0",
            timeout=10
        )
    
    def geocoder_commune(
        self,
        commune: str,
        departement: Optional[str] = None,
        code_postal: Optional[str] = None
    ) -> Optional[Dict]:
        """
        Géocode une commune française
        
        Args:
            commune: Nom de la commune (ex: "Chamonix-Mont-Blanc")
            departement: Nom ou code du département (ex: "Haute-Savoie" ou "74")
            code_postal: Code postal (ex: "74400")
        
        Returns:
            dict: {
                'lat': float,
                'lon': float,
                'coordonnees_gps': str,
                'precision': str,
                'source': str,
                'adresse_complete': str
            } ou None si non trouvé
        """
        # 1. Recherche en base locale
        result = self._recherche_base_locale(commune, departement, code_postal)
        if result:
            return result
        
        # 2. Fallback: Nominatim
        result = self._geocoder_nominatim(commune, departement)
        if result:
            return result
        
        logger.warning(f"Commune non trouvée: {commune}, {departement}")
        return None
    
    def _recherche_base_locale(
        self,
        commune: str,
        departement: Optional[str] = None,
        code_postal: Optional[str] = None
    ) -> Optional[Dict]:
        """Recherche dans la base locale des communes"""
        
        # Nettoyer le nom de commune (majuscules, tirets)
        commune_clean = commune.strip().upper()
        
        # Stratégie 1: Nom exact + département
        if departement:
            # Gérer code ou nom de département
            dept_filter = {}
            if len(str(departement)) <= 3 and departement.isdigit():
                dept_filter['code_departement'] = departement
            else:
                dept_filter['departement__icontains'] = departement
            
            result = CommuneFrance.objects.filter(
                nom__iexact=commune_clean,
                **dept_filter
            ).first()
            
            if result:
                return self._format_resultat_local(result)
        
        # Stratégie 2: Code postal
        if code_postal:
            result = CommuneFrance.objects.filter(
                nom__iexact=commune_clean,
                code_postal=code_postal
            ).first()
            
            if result:
                return self._format_resultat_local(result)
        
        # Stratégie 3: Nom seul (si unique)
        results = CommuneFrance.objects.filter(nom__iexact=commune_clean)
        if results.count() == 1:
            return self._format_resultat_local(results.first())
        
        # Stratégie 4: Recherche floue (contient)
        if departement:
            dept_filter = {}
            if len(str(departement)) <= 3 and departement.isdigit():
                dept_filter['code_departement'] = departement
            else:
                dept_filter['departement__icontains'] = departement
            
            result = CommuneFrance.objects.filter(
                nom__icontains=commune_clean,
                **dept_filter
            ).first()
            
            if result:
                logger.info(f"Correspondance floue: {commune} -> {result.nom}")
                return self._format_resultat_local(result)
        
        return None
    
    def _format_resultat_local(self, commune: CommuneFrance) -> Dict:
        """Formate le résultat depuis la base locale"""
        return {
            'lat': float(commune.latitude),
            'lon': float(commune.longitude),
            'coordonnees_gps': commune.coordonnees_gps,
            'precision': 'commune',
            'precision_metres': 5000,  # ~5km pour le centre d'une commune
            'source': 'base_locale',
            'adresse_complete': f"{commune.nom}, {commune.departement}, France",
            'code_insee': commune.code_insee,
            'code_postal': commune.code_postal,
        }
    
    def _geocoder_nominatim(
        self,
        commune: str,
        departement: Optional[str] = None
    ) -> Optional[Dict]:
        """Géocode via Nominatim (fallback)"""
        try:
            # Construire la requête
            if departement:
                query = f"{commune}, {departement}, France"
            else:
                query = f"{commune}, France"
            
            # Limiter aux résultats de type ville/village
            location = self.geolocator.geocode(
                query,
                country_codes='fr',
                exactly_one=True
            )
            
            if location:
                logger.info(f"Nominatim: {commune} -> {location.address}")
                return {
                    'lat': location.latitude,
                    'lon': location.longitude,
                    'coordonnees_gps': f"{location.latitude},{location.longitude}",
                    'precision': 'commune',
                    'precision_metres': 5000,
                    'source': 'nominatim',
                    'adresse_complete': location.address,
                }
            
        except GeocoderTimedOut:
            logger.warning(f"Timeout Nominatim pour {commune}")
            # Réessayer une fois
            time.sleep(1)
            return self._geocoder_nominatim(commune, departement)
            
        except GeocoderServiceError as e:
            logger.error(f"Erreur Nominatim: {e}")
        
        return None
    
    def geocoder_avec_lieu_dit(
        self,
        commune: str,
        departement: Optional[str] = None,
        lieu_dit: Optional[str] = None
    ) -> Optional[Dict]:
        """
        Géocode avec lieu-dit si disponible (plus précis)
        
        Essaie d'abord le lieu-dit, puis la commune en fallback
        """
        # 1. Essayer avec le lieu-dit
        if lieu_dit:
            try:
                query = f"{lieu_dit}, {commune}"
                if departement:
                    query += f", {departement}"
                query += ", France"
                
                location = self.geolocator.geocode(query, country_codes='fr')
                
                if location:
                    logger.info(f"Lieu-dit trouvé: {lieu_dit} ({commune})")
                    return {
                        'lat': location.latitude,
                        'lon': location.longitude,
                        'coordonnees_gps': f"{location.latitude},{location.longitude}",
                        'precision': 'lieu-dit',
                        'precision_metres': 500,  # Plus précis qu'une commune
                        'source': 'nominatim_lieu_dit',
                        'adresse_complete': location.address,
                    }
            except Exception as e:
                logger.warning(f"Erreur géocodage lieu-dit {lieu_dit}: {e}")
        
        # 2. Fallback: commune seule
        return self.geocoder_commune(commune, departement)
    
    def geocoder_batch(self, communes_list: list, delay: float = 1.0) -> list:
        """
        Géocode une liste de communes en batch
        
        Args:
            communes_list: Liste de dicts {'commune': str, 'departement': str}
            delay: Délai entre requêtes Nominatim (secondes)
        
        Returns:
            Liste de résultats
        """
        results = []
        
        for item in communes_list:
            commune = item.get('commune')
            departement = item.get('departement')
            
            if not commune:
                continue
            
            result = self.geocoder_commune(commune, departement)
            
            if result:
                results.append({
                    'commune': commune,
                    'departement': departement,
                    'resultat': result,
                    'success': True
                })
            else:
                results.append({
                    'commune': commune,
                    'departement': departement,
                    'resultat': None,
                    'success': False
                })
            
            # Respect du rate limit Nominatim (1 req/sec)
            if result and result.get('source') == 'nominatim':
                time.sleep(delay)
        
        return results


# Instance globale réutilisable
_geocodeur_instance = None

def get_geocodeur() -> GeocodeurCommunes:
    """Retourne une instance singleton du géocodeur"""
    global _geocodeur_instance
    if _geocodeur_instance is None:
        _geocodeur_instance = GeocodeurCommunes()
    return _geocodeur_instance
```

### 5. Mise à jour du modèle Localisation

**Fichier : `geo/models.py`**

Ajouter les champs suivants au modèle `Localisation` existant :

```python
class Localisation(models.Model):
    # ... champs existants ...
    
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
        max_length=5,
        blank=True,
        help_text="Code INSEE de la commune"
    )
```

**Créer et appliquer la migration :**

```bash
python manage.py makemigrations geo
python manage.py migrate geo
```

### 6. Intégration dans le workflow de transcription

**Fichier : `observations/tasks.py`**

Modifier la tâche de transcription pour inclure le géocodage automatique :

```python
from celery import shared_task
from geo.utils.geocoding import get_geocodeur
import logging

logger = logging.getLogger(__name__)

@shared_task(bind=True, max_retries=3)
def transcrire_et_geocoder_fiche(self, image_path):
    """
    Transcrit une fiche papier et géocode automatiquement la commune
    """
    try:
        # 1. OCR de l'image (code existant)
        donnees_ocr = extraire_texte_vision_api(image_path)
        
        # 2. Parser les données (code existant)
        commune = donnees_ocr.get('commune', '').strip()
        departement = donnees_ocr.get('departement', '').strip()
        lieu_dit = donnees_ocr.get('lieu_dit', '').strip()
        
        # 3. Créer la fiche (code existant)
        fiche = FicheObservation.objects.create(...)
        
        # 4. Géocodage automatique de la commune
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
            else:
                # Marquer pour révision manuelle
                logger.warning(
                    f"Fiche {fiche.num_fiche}: Impossible de géocoder '{commune}', '{departement}'"
                )
                fiche.localisation.coordonnees_gps = ""
                fiche.localisation.source_coordonnees = "geocodage_auto"
                fiche.localisation.save()
        
        return {
            'success': True,
            'fiche_id': fiche.num_fiche,
            'geocodage': 'success' if commune and coords else 'failed'
        }
        
    except Exception as exc:
        logger.error(f"Erreur transcription: {exc}")
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))
```

### 7. Interface de géocodage manuel

**Fichier : `geo/views.py`**

```python
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from observations.models import FicheObservation
from geo.utils.geocoding import get_geocodeur
import logging

logger = logging.getLogger(__name__)

@login_required
@require_POST
def geocoder_commune_manuelle(request):
    """
    Vue AJAX pour géocoder manuellement une commune
    
    POST params:
        - fiche_id: ID de la fiche
        - commune: Nom de la commune
        - departement: Nom ou code du département (optionnel)
        - lieu_dit: Lieu-dit (optionnel)
    """
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
            
            logger.info(f"Géocodage manuel réussi: {commune} -> {coords['coordonnees_gps']}")
            
            return JsonResponse({
                'success': True,
                'coords': coords,
                'message': f"Commune géocodée avec succès",
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

**Fichier : `geo/urls.py`**

```python
from django.urls import path
from . import views

app_name = 'geo'

urlpatterns = [
    path('geocoder/', views.geocoder_commune_manuelle, name='geocoder_commune'),
]
```

**Inclure dans le routing principal (`observations_nids/urls.py`) :**

```python
urlpatterns = [
    # ... autres urls ...
    path('geo/', include('geo.urls')),
]
```

### 8. Interface JavaScript pour l'interface de saisie

**Fichier : `observations/static/js/geocoding.js`**

```javascript
/**
 * Géocodage manuel depuis l'interface de saisie
 */

function geocoderCommune(ficheId, commune, departement, lieuDit) {
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
    
    // Afficher un loader
    const geocodeBtn = document.getElementById('btn-geocoder');
    const originalText = geocodeBtn.innerHTML;
    geocodeBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Géocodage...';
    geocodeBtn.disabled = true;
    
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
            document.getElementById('id_localisation-coordonnees_gps').value = data.coords.coordonnees_gps;
            
            // Afficher un message de succès
            showNotification('success', `✓ Commune géocodée: ${data.adresse} (${data.source})`);
            
            // Si une carte existe, mettre à jour le marqueur
            if (typeof updateMapMarker === 'function') {
                updateMapMarker(data.coords.lat, data.coords.lon);
            }
        } else {
            showNotification('error', `✗ ${data.message}`);
        }
    })
    .catch(error => {
        showNotification('error', `Erreur: ${error}`);
    })
    .finally(() => {
        geocodeBtn.innerHTML = originalText;
        geocodeBtn.disabled = false;
    });
}

function showNotification(type, message) {
    const alertClass = type === 'success' ? 'alert-success' : 'alert-danger';
    const notification = `
        <div class="alert ${alertClass} alert-dismissible fade show" role="alert">
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
    `;
    
    const container = document.getElementById('notifications-container') || document.querySelector('.container');
    container.insertAdjacentHTML('afterbegin', notification);
    
    // Auto-dismiss après 5 secondes
    setTimeout(() => {
        const alert = container.querySelector('.alert');
        if (alert) alert.remove();
    }, 5000);
}
```

**Ajouter dans le template `saisie_observation_optimise.html` :**

```django
<!-- Dans la section Localisation -->
<div class="card-body">
    <!-- Champs existants -->
    
    <!-- Bouton de géocodage -->
    <div class="row mt-3">
        <div class="col-12">
            <button type="button" id="btn-geocoder" class="btn btn-info"
                    onclick="geocoderCommune(
                        {{ fiche.num_fiche }},
                        document.getElementById('id_localisation-commune').value,
                        document.getElementById('id_localisation-departement').value,
                        document.getElementById('id_localisation-lieu_dit').value
                    )">
                <i class="fas fa-map-marker-alt"></i> Géocoder la commune
            </button>
            <small class="form-text text-muted ms-2">
                Remplissez la commune (et optionnellement le département/lieu-dit) puis cliquez ici
            </small>
        </div>
    </div>
</div>

<!-- Inclure le script -->
<script src="{% static 'js/geocoding.js' %}"></script>