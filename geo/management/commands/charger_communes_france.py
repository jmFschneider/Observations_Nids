import requests
from django.core.management.base import BaseCommand

from geo.models import CommuneFrance


class Command(BaseCommand):
    help = "Charge la base des communes françaises depuis l'API Géoplateforme"

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
                    f'{count} communes déjà en base. Utilisez --force pour recharger.'
                )
            )
            return

        # URL de l'API Géoplateforme
        url = "https://geo.api.gouv.fr/communes"
        params = {
            'fields': 'nom,code,codesPostaux,centre,departement,region,population,surface',
            'format': 'json',
            'geometry': 'centre',
        }

        self.stdout.write("Téléchargement des communes depuis l'API Géoplateforme...")

        try:
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            communes = response.json()
        except requests.RequestException as e:
            self.stdout.write(self.style.ERROR(f'Erreur lors du téléchargement: {e}'))
            return

        self.stdout.write(f"{len(communes)} communes récupérées")
        self.stdout.write("Chargement en base de données...")

        # Supprimer les anciennes données si --force
        if options['force']:
            deleted_count = CommuneFrance.objects.all().delete()[0]
            self.stdout.write(f"{deleted_count} anciennes communes supprimées")

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
                    superficie=commune.get('surface', 0) / 10000,  # m² vers km²
                )
                communes_objects.append(commune_obj)

            except (KeyError, IndexError, TypeError) as e:
                erreurs += 1
                self.stdout.write(
                    self.style.WARNING(f"Erreur commune {commune.get('nom', '?')}: {e}")
                )

        # Insertion en masse
        CommuneFrance.objects.bulk_create(communes_objects, batch_size=1000)

        # Rapport final
        self.stdout.write(
            self.style.SUCCESS(
                f"\nChargement terminé:\n"
                f"   - {len(communes_objects)} communes chargées\n"
                f"   - {erreurs} erreurs"
            )
        )

        # Statistiques
        total = CommuneFrance.objects.count()
        depts = CommuneFrance.objects.values('departement').distinct().count()
        self.stdout.write(
            self.style.SUCCESS(
                f"\nBase de données:\n   - {total} communes\n   - {depts} départements"
            )
        )
