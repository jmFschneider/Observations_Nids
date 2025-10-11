"""
Utilitaire de géocodage intelligent pour les communes françaises
Utilise en priorité la base locale, puis Nominatim en fallback
"""

import logging
import time

from geopy.exc import GeocoderServiceError, GeocoderTimedOut
from geopy.geocoders import Nominatim

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
        self.geolocator = Nominatim(user_agent="observations_nids/1.0", timeout=10)

    def geocoder_commune(
        self, commune: str, departement: str | None = None, code_postal: str | None = None
    ) -> dict | None:
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

    def _normaliser_nom_commune(self, nom: str) -> str:
        """Normalise le nom d'une commune pour améliorer la correspondance"""
        # Mettre en majuscules
        nom_norm = nom.strip().upper()

        # Remplacer les abréviations courantes
        remplacements = {
            ' S/': '-SUR-',
            ' S ': '-SUR-',
            ' ST ': '-SAINT-',
            ' ST-': '-SAINT-',
            ' STE ': '-SAINTE-',
            ' STE-': '-SAINTE-',
            '-S-': '-SUR-',
            '-S/': '-SUR-',
        }

        for abr, complet in remplacements.items():
            nom_norm = nom_norm.replace(abr, complet)

        return nom_norm

    def _recherche_base_locale(
        self, commune: str, departement: str | None = None, code_postal: str | None = None
    ) -> dict | None:
        """Recherche dans la base locale des communes"""

        # Nettoyer et normaliser le nom de commune
        commune_clean = self._normaliser_nom_commune(commune)

        # Stratégie 1: Nom exact + département
        if departement:
            # Gérer code ou nom de département
            dept_filter = {}
            if len(str(departement)) <= 3 and str(departement).isdigit():
                dept_filter['code_departement'] = departement
            else:
                dept_filter['departement__icontains'] = departement

            result = CommuneFrance.objects.filter(
                nom__iexact=commune_clean, **dept_filter
            ).first()

            if result:
                return self._format_resultat_local(result)

        # Stratégie 2: Code postal
        if code_postal:
            result = CommuneFrance.objects.filter(
                nom__iexact=commune_clean, code_postal=code_postal
            ).first()

            if result:
                return self._format_resultat_local(result)

        # Stratégie 3: Nom seul (si unique)
        results = CommuneFrance.objects.filter(nom__iexact=commune_clean)
        if results.count() == 1:
            first_result = results.first()
            if first_result:
                return self._format_resultat_local(first_result)

        # Stratégie 4: Recherche floue (contient)
        if departement:
            dept_filter = {}
            if len(str(departement)) <= 3 and str(departement).isdigit():
                dept_filter['code_departement'] = departement
            else:
                dept_filter['departement__icontains'] = departement

            result = CommuneFrance.objects.filter(
                nom__icontains=commune_clean, **dept_filter
            ).first()

            if result:
                logger.info(f"Correspondance floue: {commune} -> {result.nom}")
                return self._format_resultat_local(result)

        return None

    def _format_resultat_local(self, commune: CommuneFrance) -> dict:
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
            'altitude': commune.altitude,
        }

    def _geocoder_nominatim(
        self, commune: str, departement: str | None = None
    ) -> dict | None:
        """Géocode via Nominatim (fallback)"""
        try:
            # Construire la requête
            query = f"{commune}, {departement}, France" if departement else f"{commune}, France"

            # Limiter aux résultats de type ville/village
            location = self.geolocator.geocode(query, country_codes='fr', exactly_one=True)

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
        self, commune: str, departement: str | None = None, lieu_dit: str | None = None
    ) -> dict | None:
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
                    'success': True,
                })
            else:
                results.append({
                    'commune': commune,
                    'departement': departement,
                    'resultat': None,
                    'success': False,
                })

            # Respect du rate limit Nominatim (1 req/sec)
            if result and result.get('source') == 'nominatim':
                time.sleep(delay)

        return results


# Instance globale réutilisable
class _GeocodeurSingleton:
    """Singleton pour l'instance du géocodeur"""
    _instance: GeocodeurCommunes | None = None

    @classmethod
    def get_instance(cls) -> GeocodeurCommunes:
        """Retourne l'instance unique du géocodeur"""
        if cls._instance is None:
            cls._instance = GeocodeurCommunes()
        return cls._instance


def get_geocodeur() -> GeocodeurCommunes:
    """Retourne une instance singleton du géocodeur"""
    return _GeocodeurSingleton.get_instance()
