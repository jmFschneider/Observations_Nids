import logging
from math import atan2, cos, radians, sin, sqrt

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_GET, require_POST

from geo.models import CommuneFrance
from geo.utils.geocoding import get_geocodeur
from observations.models import FicheObservation

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
            return JsonResponse(
                {'success': False, 'message': 'Paramètres manquants (fiche_id, commune)'},
                status=400,
            )

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
            fiche.localisation.coordonnees = coords['coordonnees_gps']
            fiche.localisation.latitude = str(coords['lat'])
            fiche.localisation.longitude = str(coords['lon'])
            fiche.localisation.commune = commune
            if departement:
                fiche.localisation.departement = departement
            if lieu_dit:
                fiche.localisation.lieu_dit = lieu_dit
            fiche.localisation.precision_gps = coords.get('precision_metres', 5000)
            fiche.localisation.source_coordonnees = 'geocodage_manuel'
            if 'code_insee' in coords:
                fiche.localisation.code_insee = coords['code_insee']
            fiche.localisation.save()

            logger.info(f"Géocodage manuel réussi: {commune} -> {coords['coordonnees_gps']}")

            return JsonResponse({
                'success': True,
                'coords': coords,
                'message': "Commune géocodée avec succès",
                'adresse': coords.get('adresse_complete', ''),
                'source': coords.get('source', ''),
                'precision': coords.get('precision', ''),
            })
        else:
            return JsonResponse(
                {'success': False, 'message': f"Impossible de trouver la commune '{commune}'"}
            )

    except FicheObservation.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Fiche non trouvée'}, status=404)

    except Exception as e:
        logger.error(f"Erreur géocodage manuel: {e}")
        return JsonResponse({'success': False, 'message': f"Erreur: {str(e)}"}, status=500)


@login_required
@require_GET
def rechercher_communes(request):
    """
    API AJAX pour rechercher des communes dans la base CommuneFrance

    GET params:
        - q: Terme de recherche (nom de commune)
        - lat: Latitude GPS (optionnel, pour recherche géographique)
        - lon: Longitude GPS (optionnel, pour recherche géographique)
        - limit: Nombre maximum de résultats (défaut: 10)

    Returns:
        JSON: Liste des communes correspondantes
    """
    query = request.GET.get('q', '').strip()
    lat = request.GET.get('lat', '').strip()
    lon = request.GET.get('lon', '').strip()
    limit = int(request.GET.get('limit', 10))

    # Recherche par coordonnées GPS (bounding box)
    if lat and lon:
        try:
            lat_float = float(lat)
            lon_float = float(lon)

            # Rayon approximatif : 0.1° ≈ 11 km
            # Pour un rayon de ~10km autour de la position
            delta = 0.1

            communes = CommuneFrance.objects.filter(
                latitude__gte=lat_float - delta,
                latitude__lte=lat_float + delta,
                longitude__gte=lon_float - delta,
                longitude__lte=lon_float + delta,
            ).values(
                'nom', 'departement', 'code_departement', 'code_postal',
                'code_insee', 'latitude', 'longitude', 'altitude'
            )[:limit]

        except ValueError:
            return JsonResponse({'communes': [], 'error': 'Coordonnées GPS invalides'})

    # Recherche par nom de commune
    elif query and len(query) >= 2:
        communes = CommuneFrance.objects.filter(
            nom__icontains=query
        ).values(
            'nom', 'departement', 'code_departement', 'code_postal',
            'code_insee', 'latitude', 'longitude', 'altitude'
        )[:limit]

    else:
        return JsonResponse({'communes': []})

    # Formater les résultats
    results = []

    # Précalculer les conversions si on a des coordonnées GPS
    if lat and lon:
        lat_rad = radians(float(lat))
        lon_rad = radians(float(lon))

    for commune in communes:
        # Calculer la distance si on a des coordonnées GPS
        distance_info = ''
        if lat and lon:
            try:
                # Formule de Haversine complète
                lat2_rad = radians(float(commune['latitude']))
                lon2_rad = radians(float(commune['longitude']))

                dlat = lat2_rad - lat_rad
                dlon = lon2_rad - lon_rad

                # Haversine
                a = sin(dlat/2)**2 + cos(lat_rad) * cos(lat2_rad) * sin(dlon/2)**2
                c = 2 * atan2(sqrt(a), sqrt(1-a))
                distance_km = 6371 * c  # Rayon de la Terre en km

                if distance_km < 1:
                    distance_info = f" - {int(distance_km * 1000)}m"
                else:
                    distance_info = f" - {distance_km:.1f}km"
            except Exception as e:
                logger.debug(f"Erreur calcul distance: {e}")

        results.append({
            'nom': commune['nom'],
            'departement': commune['departement'],
            'code_departement': commune['code_departement'],
            'code_postal': commune['code_postal'],
            'code_insee': commune['code_insee'],
            'label': f"{commune['nom']} ({commune['code_departement']}) - {commune['departement']}{distance_info}",
            'latitude': str(commune['latitude']),
            'longitude': str(commune['longitude']),
            'altitude': commune['altitude'] if commune.get('altitude') is not None else None,
        })

    return JsonResponse({'communes': results})
