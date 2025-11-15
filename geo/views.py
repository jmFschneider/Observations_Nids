import logging
from math import atan2, cos, radians, sin, sqrt

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_GET, require_POST

from geo.models import AncienneCommune, CommuneFrance
from geo.services.geocodeur import geocoder_commune_unifiee
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
            # Vérifier si c'est une ancienne commune
            resultat_geocodage = geocoder_commune_unifiee(commune)

            # Mise à jour de la localisation
            fiche.localisation.coordonnees = coords['coordonnees_gps']
            fiche.localisation.latitude = str(coords['lat'])
            fiche.localisation.longitude = str(coords['lon'])

            # Enregistrer le nom saisi ET le nom normalisé
            fiche.localisation.commune_saisie = commune  # Ce que l'utilisateur a saisi
            if resultat_geocodage and resultat_geocodage['est_fusionnee']:
                # Si c'est une ancienne commune, enregistrer la commune actuelle
                fiche.localisation.commune = resultat_geocodage['commune_actuelle']
            else:
                # Sinon, enregistrer tel quel
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

            return JsonResponse(
                {
                    'success': True,
                    'coords': coords,
                    'message': "Commune géocodée avec succès",
                    'adresse': coords.get('adresse_complete', ''),
                    'source': coords.get('source', ''),
                    'precision': coords.get('precision', ''),
                }
            )
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
        JSON: Liste des communes correspondantes, filtrées par rayon de 10km si GPS fourni
    """
    query = request.GET.get('q', '').strip()
    lat = request.GET.get('lat', '').strip()
    lon = request.GET.get('lon', '').strip()
    limit = int(request.GET.get('limit', 10))

    # Recherche par nom de commune
    if query and len(query) >= 2:
        # 1. Rechercher dans les communes actuelles
        communes_queryset = CommuneFrance.objects.filter(nom__icontains=query)

        # Si coordonnées GPS fournies ET valides (pas 0,0), filtrer par bounding box (~10 km)
        if lat and lon:
            try:
                lat_float = float(lat)
                lon_float = float(lon)

                # Ignorer les coordonnées par défaut (0,0 = non renseigné)
                if lat_float != 0.0 and lon_float != 0.0:
                    # Rayon approximatif : 0.1° ≈ 11 km
                    # Filtrage rapide par bounding box avant calcul exact
                    delta = 0.1

                    communes_queryset = communes_queryset.filter(
                        latitude__gte=lat_float - delta,
                        latitude__lte=lat_float + delta,
                        longitude__gte=lon_float - delta,
                        longitude__lte=lon_float + delta,
                    )
            except ValueError:
                logger.warning(f"Coordonnées GPS invalides: lat={lat}, lon={lon}")

        communes = list(
            communes_queryset.values(
                'id',  # Ajout de l'ID pour l'autocomplétion
                'nom',
                'departement',
                'code_departement',
                'code_postal',
                'code_insee',
                'latitude',
                'longitude',
                'altitude',
            )[:50]
        )  # Récupérer 50 communes actuelles

        # 2. Rechercher dans les anciennes communes
        anciennes_queryset = AncienneCommune.objects.filter(nom__icontains=query).select_related(
            'commune_actuelle'
        )

        # Appliquer le même filtrage GPS si nécessaire
        if lat and lon:
            try:
                lat_float = float(lat)
                lon_float = float(lon)
                if lat_float != 0.0 and lon_float != 0.0:
                    delta = 0.1
                    anciennes_queryset = anciennes_queryset.filter(
                        commune_actuelle__latitude__gte=lat_float - delta,
                        commune_actuelle__latitude__lte=lat_float + delta,
                        commune_actuelle__longitude__gte=lon_float - delta,
                        commune_actuelle__longitude__lte=lon_float + delta,
                    )
            except ValueError:
                pass

        # Ajouter les anciennes communes au résultat
        for ancienne in anciennes_queryset[:50]:
            # Utiliser les coordonnées de l'ancienne commune si disponibles, sinon celles de la commune actuelle
            lat_ancienne = (
                ancienne.latitude if ancienne.latitude else ancienne.commune_actuelle.latitude
            )
            lon_ancienne = (
                ancienne.longitude if ancienne.longitude else ancienne.commune_actuelle.longitude
            )
            alt_ancienne = (
                ancienne.altitude if ancienne.altitude else ancienne.commune_actuelle.altitude
            )

            communes.append(
                {
                    'id': f"ancienne_{ancienne.id}",  # Préfixe pour différencier
                    'nom': ancienne.nom,
                    'nom_actuel': ancienne.commune_actuelle.nom,  # Nom de la commune actuelle
                    'departement': ancienne.departement or ancienne.commune_actuelle.departement,
                    'code_departement': ancienne.code_departement,
                    'code_postal': ancienne.code_postal or ancienne.commune_actuelle.code_postal,
                    'code_insee': ancienne.commune_actuelle.code_insee,  # Code INSEE actif
                    'latitude': lat_ancienne,
                    'longitude': lon_ancienne,
                    'altitude': alt_ancienne,
                    'est_fusionnee': True,  # Marqueur pour affichage différent
                }
            )

    else:
        return JsonResponse({'communes': []})

    # Formater les résultats et calculer les distances
    results = []

    # Précalculer les conversions si on a des coordonnées GPS valides (pas 0,0)
    if lat and lon:
        try:
            lat_float = float(lat)
            lon_float = float(lon)
            # Vérifier que ce ne sont pas les coordonnées par défaut (0,0 = non renseigné)
            if lat_float != 0.0 and lon_float != 0.0:
                lat_rad = radians(lat_float)
                lon_rad = radians(lon_float)
                has_gps = True
            else:
                has_gps = False
        except ValueError:
            has_gps = False
    else:
        has_gps = False

    for commune in communes:
        distance_km = None
        distance_info = ''

        # Calculer la distance exacte si on a des coordonnées GPS
        if has_gps:
            try:
                # Formule de Haversine complète
                lat2_rad = radians(float(commune['latitude']))
                lon2_rad = radians(float(commune['longitude']))

                dlat = lat2_rad - lat_rad
                dlon = lon2_rad - lon_rad

                # Haversine
                a = sin(dlat / 2) ** 2 + cos(lat_rad) * cos(lat2_rad) * sin(dlon / 2) ** 2
                c = 2 * atan2(sqrt(a), sqrt(1 - a))
                distance_km = 6371 * c  # Rayon de la Terre en km

                # Filtrer : ne garder que les communes à moins de 10 km
                if distance_km > 10:
                    continue

                if distance_km < 1:
                    distance_info = f" - {int(distance_km * 1000)}m"
                else:
                    distance_info = f" - {distance_km:.1f}km"
            except Exception as e:
                logger.debug(f"Erreur calcul distance: {e}")
                distance_km = None

        # Construire le label selon que c'est une ancienne commune ou non
        if commune.get('est_fusionnee'):
            label = f"{commune['nom']} → {commune['nom_actuel']} ({commune['code_departement']}) - {commune['departement']}{distance_info}"
        else:
            label = f"{commune['nom']} ({commune['code_departement']}) - {commune['departement']}{distance_info}"

        results.append(
            {
                'id': commune['id'],  # ID pour l'autocomplétion
                'nom': commune['nom'],
                'nom_actuel': commune.get('nom_actuel'),  # Seulement pour les anciennes communes
                'departement': commune['departement'],
                'code_departement': commune['code_departement'],
                'code_postal': commune['code_postal'],
                'code_insee': commune['code_insee'],
                'label': label,
                'latitude': str(commune['latitude']),
                'longitude': str(commune['longitude']),
                'altitude': commune['altitude'] if commune.get('altitude') is not None else None,
                'est_fusionnee': commune.get('est_fusionnee', False),
                'distance_km': distance_km,  # Pour le tri
            }
        )

    # Trier par distance si GPS fourni, sinon par ordre alphabétique
    if has_gps:
        results.sort(key=lambda x: x['distance_km'] if x['distance_km'] is not None else 999)
    else:
        results.sort(key=lambda x: x['nom'])

    # Limiter le nombre de résultats
    results = results[:limit]

    # Retirer distance_km de la réponse (utilisé uniquement pour le tri)
    for result in results:
        result.pop('distance_km', None)

    return JsonResponse({'communes': results})
