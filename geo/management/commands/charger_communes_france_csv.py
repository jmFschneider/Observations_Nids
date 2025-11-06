import csv

import requests
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Charge la base des communes françaises depuis l'API Géoplateforme et la sauvegarde dans un fichier CSV."

    def handle(self, *args, **options):
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
        self.stdout.write("Écriture dans le fichier CSV...")

        output_filename = 'commune_csv.csv'

        with open(output_filename, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = [
                'nom',
                'code',
                'code_postal',
                'departement',
                'code_departement',
                'region',
                'latitude',
                'longitude',
                'population',
                'surface_km2',
            ]
            writer = csv.writer(csvfile, delimiter='\t')
            writer.writerow(fieldnames)

            erreurs = 0
            lignes_ecrites = 0

            for commune in communes:
                try:
                    centre = commune.get('centre', {}).get('coordinates', [None, None])
                    longitude = centre[0]
                    latitude = centre[1]

                    if latitude is None or longitude is None:
                        erreurs += 1
                        continue

                    writer.writerow(
                        [
                            commune['nom'],
                            commune['code'],
                            commune.get('codesPostaux', [''])[0],
                            commune['departement']['nom'],
                            commune['departement']['code'],
                            commune.get('region', {}).get('nom', ''),
                            latitude,
                            longitude,
                            commune.get('population'),
                            commune.get('surface', 0) / 10000 if commune.get('surface') else 0,
                        ]
                    )
                    lignes_ecrites += 1

                except (KeyError, IndexError, TypeError) as e:
                    erreurs += 1
                    self.stdout.write(
                        self.style.WARNING(f"Erreur pour la commune {commune.get('nom', '?')}: {e}")
                    )

        self.stdout.write(
            self.style.SUCCESS(
                f"\nOpération terminée:\n"
                f"   - {lignes_ecrites} communes écrites dans {output_filename}\n"
                f"   - {erreurs} erreurs rencontrées"
            )
        )
