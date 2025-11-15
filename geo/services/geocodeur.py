"""
Service de géocodage unifié pour les communes françaises.
Cherche automatiquement dans les communes actuelles ET les anciennes communes fusionnées.
"""

from geo.models import CommuneFrance, AncienneCommune


def geocoder_commune_unifiee(nom_commune, code_departement=None):
    """
    Cherche une commune dans la base actuelle + anciennes communes.
    Retourne toujours les données normalisées vers la commune actuelle.

    Args:
        nom_commune: Nom de la commune à rechercher (peut être actuelle ou ancienne)
        code_departement: Code département optionnel pour affiner la recherche

    Returns:
        dict avec les clés suivantes, ou None si non trouvée:
        {
            'commune_saisie': str,      # Nom exact saisi (ex: "Les Praz")
            'commune_actuelle': str,    # Nom normalisé (ex: "Chamonix-Mont-Blanc")
            'code_insee': str,          # Code INSEE actif (ex: "74056")
            'latitude': float,          # Coordonnées GPS (anciennes si dispo, sinon actuelles)
            'longitude': float,
            'altitude': int,            # Peut être None
            'type': str,                # 'actuelle' ou 'fusionnee'
            'est_fusionnee': bool,      # True si ancienne commune
            'date_fusion': date or None # Date de fusion si applicable
        }
    """
    if not nom_commune or not nom_commune.strip():
        return None

    nom_commune = nom_commune.strip()

    # Construire les filtres de recherche
    filters = {'nom__iexact': nom_commune}
    if code_departement:
        filters['code_departement'] = code_departement

    # 1. Chercher dans les communes actuelles
    commune = CommuneFrance.objects.filter(**filters).first()
    if commune:
        return {
            'commune_saisie': nom_commune,
            'commune_actuelle': commune.nom,
            'code_insee': commune.code_insee,
            'latitude': float(commune.latitude),
            'longitude': float(commune.longitude),
            'altitude': commune.altitude,
            'type': 'actuelle',
            'est_fusionnee': False,
            'date_fusion': None,
        }

    # 2. Chercher dans les anciennes communes
    ancienne = AncienneCommune.objects.filter(**filters).first()
    if ancienne:
        # Utiliser les coordonnées historiques si disponibles, sinon celles de la commune actuelle
        lat = ancienne.latitude if ancienne.latitude else ancienne.commune_actuelle.latitude
        lon = ancienne.longitude if ancienne.longitude else ancienne.commune_actuelle.longitude
        alt = ancienne.altitude if ancienne.altitude else ancienne.commune_actuelle.altitude

        return {
            'commune_saisie': nom_commune,
            'commune_actuelle': ancienne.commune_actuelle.nom,
            'code_insee': ancienne.commune_actuelle.code_insee,
            'latitude': float(lat),
            'longitude': float(lon),
            'altitude': alt,
            'type': 'fusionnee',
            'est_fusionnee': True,
            'date_fusion': ancienne.date_fusion,
        }

    # 3. Non trouvée
    return None


def rechercher_communes_autocomplete(terme_recherche, code_departement=None, limit=20):
    """
    Recherche pour l'autocomplete : communes actuelles + anciennes communes.

    Args:
        terme_recherche: Début du nom de commune (ex: "Cham", "Les P")
        code_departement: Code département optionnel
        limit: Nombre max de résultats

    Returns:
        Liste de dicts avec les infos pour l'autocomplete:
        [
            {
                'nom_affiche': str,     # Ex: "Les Praz → Chamonix-Mont-Blanc" ou "Chamonix-Mont-Blanc"
                'nom_saisie': str,      # Le nom à utiliser pour le géocodage
                'code_insee': str,
                'code_departement': str,
                'est_fusionnee': bool
            },
            ...
        ]
    """
    if not terme_recherche or len(terme_recherche) < 2:
        return []

    resultats = []

    # Filtres communs
    filters = {'nom__istartswith': terme_recherche}
    if code_departement:
        filters['code_departement'] = code_departement

    # 1. Communes actuelles
    communes_actuelles = CommuneFrance.objects.filter(**filters).order_by('nom')[:limit]
    for commune in communes_actuelles:
        resultats.append({
            'nom_affiche': f"{commune.nom} ({commune.code_departement})",
            'nom_saisie': commune.nom,
            'code_insee': commune.code_insee,
            'code_departement': commune.code_departement,
            'est_fusionnee': False,
        })

    # 2. Anciennes communes (seulement si on n'a pas atteint la limite)
    if len(resultats) < limit:
        anciennes_communes = AncienneCommune.objects.filter(**filters).select_related('commune_actuelle').order_by('nom')[:(limit - len(resultats))]
        for ancienne in anciennes_communes:
            resultats.append({
                'nom_affiche': f"{ancienne.nom} → {ancienne.commune_actuelle.nom} ({ancienne.code_departement})",
                'nom_saisie': ancienne.nom,
                'code_insee': ancienne.commune_actuelle.code_insee,
                'code_departement': ancienne.code_departement,
                'est_fusionnee': True,
            })

    return resultats
