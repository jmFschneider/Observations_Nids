"""
Command Django pour charger les altitudes des communes françaises
Utilise l'API Open-Elevation (gratuite, open source)
"""

import time

import requests
from django.core.management.base import BaseCommand
from django.db import transaction

from geo.models import CommuneFrance


class Command(BaseCommand):
    help = "Charge les altitudes des communes françaises via Open-Elevation API"

    def add_arguments(self, parser):
        parser.add_argument(
            '--batch-size',
            type=int,
            default=100,
            help='Nombre de communes par requête (défaut: 100)',
        )
        parser.add_argument(
            '--delay',
            type=float,
            default=1.0,
            help='Délai entre requêtes en secondes (défaut: 1.0)',
        )

    def handle(self, *args, **options):
        batch_size = options['batch_size']
        delay = options['delay']

        # Récupérer toutes les communes sans altitude
        communes_sans_altitude = CommuneFrance.objects.filter(altitude__isnull=True)
        total = communes_sans_altitude.count()

        if total == 0:
            self.stdout.write(self.style.SUCCESS('Toutes les communes ont déjà une altitude'))
            return

        self.stdout.write(f"[INFO] {total} communes sans altitude trouvees")
        self.stdout.write(f"[INFO] Traitement par batch de {batch_size} communes")

        # API Open-Elevation (peut gérer des batch requests)
        api_url = "https://api.open-elevation.com/api/v1/lookup"

        processed = 0
        errors = 0

        # Traiter par batch
        for i in range(0, total, batch_size):
            batch = list(communes_sans_altitude[i : i + batch_size])

            # Préparer les locations pour l'API
            locations = [
                {"latitude": float(c.latitude), "longitude": float(c.longitude)} for c in batch
            ]

            try:
                # Requête API
                response = requests.post(api_url, json={"locations": locations}, timeout=30)

                if response.status_code == 200:
                    data = response.json()

                    # Mettre à jour les altitudes
                    with transaction.atomic():
                        for commune, result in zip(batch, data['results'], strict=False):
                            altitude = result.get('elevation')
                            if altitude is not None:
                                commune.altitude = int(round(altitude))
                                commune.save(update_fields=['altitude'])
                                processed += 1

                    self.stdout.write(
                        f"[OK] Batch {i // batch_size + 1}/{(total + batch_size - 1) // batch_size}: "
                        f"{len(batch)} communes mises a jour"
                    )
                else:
                    self.stdout.write(
                        self.style.ERROR(
                            f"[ERR] Erreur API (status {response.status_code}): {response.text[:100]}"
                        )
                    )
                    errors += len(batch)

            except requests.exceptions.RequestException as e:
                self.stdout.write(self.style.ERROR(f"[ERR] Erreur reseau: {e}"))
                errors += len(batch)

            except Exception as e:
                self.stdout.write(self.style.ERROR(f"[ERR] Erreur: {e}"))
                errors += len(batch)

            # Délai entre requêtes pour ne pas surcharger l'API
            if i + batch_size < total:
                time.sleep(delay)

        # Résumé
        self.stdout.write("\n" + "=" * 50)
        self.stdout.write(self.style.SUCCESS(f"[OK] {processed} altitudes chargees"))
        if errors > 0:
            self.stdout.write(self.style.ERROR(f"[ERR] {errors} erreurs"))
        self.stdout.write("=" * 50)
