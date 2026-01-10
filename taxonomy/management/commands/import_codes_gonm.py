"""
Commande Django pour importer les codes GONM des espèces d'oiseaux.

Cette commande met à jour le champ code_gonm des espèces existantes
à partir du fichier TSV validé contenant les correspondances analysées.

Usage:
    python manage.py import_codes_gonm
    python manage.py import_codes_gonm --file /chemin/vers/analyse-correspondances-gonm.tsv
    python manage.py import_codes_gonm --dry-run  # Simulation sans modification
"""

import csv
from pathlib import Path
from typing import Any, TypedDict

from django.core.management.base import BaseCommand

from taxonomy.models import Espece


class ImportStats(TypedDict):
    """Type definition for import statistics."""

    total_lines: int
    especes_updated: int
    especes_not_found: int
    empty_codes: int
    erreurs: int
    especes_non_trouvees_details: list[dict[str, Any]]


class Command(BaseCommand):
    help = "Importe les codes GONM des espèces depuis le fichier TSV validé"

    # Chemin par défaut du fichier TSV validé
    DEFAULT_TSV_PATH = r"C:\Projets\observations_nids\analyse-correspondances-gonm____80%.xlsx - analyse-correspondances-gonm.tsv"

    def add_arguments(self, parser):
        parser.add_argument(
            '--file',
            type=str,
            default=self.DEFAULT_TSV_PATH,
            help='Chemin vers le fichier TSV validé contenant les correspondances GONM',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Simule l\'importation sans modifier la base de données',
        )

    def handle(self, *args, **options):
        """Point d'entrée principal de la commande."""
        self.stdout.write(self.style.MIGRATE_HEADING('\n=== Import des codes GONM ===\n'))

        # Vérifier que le fichier existe
        csv_file = Path(options['file'])
        if not csv_file.exists():
            self.stdout.write(self.style.ERROR(f"Fichier introuvable: {csv_file}"))
            return

        self.stdout.write(f"Fichier à importer: {csv_file}\n")

        # Mode dry-run
        dry_run = options['dry_run']
        if dry_run:
            self.stdout.write(
                self.style.WARNING("MODE DRY-RUN: Aucune modification ne sera effectuée\n")
            )

        # Importer les codes
        stats = self._import_codes(csv_file, dry_run=dry_run)

        # Afficher le rapport final
        self._display_report(stats)

    def _import_codes(self, csv_file: Path, dry_run: bool = False) -> ImportStats:
        """
        Importe les codes GONM depuis le fichier TSV validé.

        Le matching se fait par nom français (case-insensitive) qui est plus stable que l'ID.
        """
        stats: ImportStats = {
            'total_lines': 0,
            'especes_updated': 0,
            'especes_not_found': 0,
            'empty_codes': 0,
            'erreurs': 0,
            'especes_non_trouvees_details': [],
        }

        especes_non_trouvees = []

        # Essayer différents encodages
        encodings = ['utf-8-sig', 'utf-8', 'cp1252', 'iso-8859-1', 'latin-1']
        file_content = None
        used_encoding = None

        for encoding in encodings:
            try:
                with open(csv_file, encoding=encoding) as f:
                    file_content = f.read()
                    used_encoding = encoding
                    break
            except UnicodeDecodeError:
                continue

        if not file_content:
            self.stdout.write(
                self.style.ERROR(
                    f"Impossible de lire le fichier avec les encodages: {', '.join(encodings)}"
                )
            )
            return stats

        self.stdout.write(f"Encodage détecté: {used_encoding}\n")

        try:
            # Parser le TSV (délimiteur tabulation)
            lines = file_content.split('\n')
            if not lines:
                return stats

            # Le TSV utilise des tabulations comme délimiteur
            reader = csv.DictReader(lines, delimiter='\t')

            # Vérifier les colonnes attendues
            if not reader.fieldnames:
                self.stdout.write(self.style.ERROR("Impossible de lire les en-têtes du TSV"))
                return stats

            self.stdout.write(f"Colonnes détectées: {', '.join(reader.fieldnames)}\n")

            # Vérifier que les colonnes nécessaires sont présentes
            required_cols = ['code_gonm', 'espece_trouvee_id', 'espece_trouvee_nom']
            missing_cols = [col for col in required_cols if col not in reader.fieldnames]
            if missing_cols:
                self.stdout.write(
                    self.style.ERROR(f"Colonnes manquantes dans le TSV: {', '.join(missing_cols)}")
                )
                return stats

            # Traiter chaque ligne
            for row in reader:
                stats['total_lines'] += 1

                # Récupérer les valeurs du TSV validé
                code_gonm = (row.get('code_gonm') or '').strip()
                espece_id = (row.get('espece_trouvee_id') or '').strip()
                espece_nom = (row.get('espece_trouvee_nom') or '').strip()
                score = (row.get('score_pourcent') or '').strip()

                # Ignorer les lignes vides
                if not espece_id:
                    continue

                # Ignorer les lignes sans code GONM
                if not code_gonm:
                    stats['empty_codes'] += 1
                    continue

                try:
                    # Récupérer l'espèce par son nom français (plus stable que l'ID)
                    espece = Espece.objects.filter(nom__iexact=espece_nom).first()

                    if espece:
                        # Mettre à jour le code GONM
                        if not dry_run:
                            espece.code_gonm = code_gonm
                            espece.save(update_fields=['code_gonm'])

                        stats['especes_updated'] += 1

                        if stats['especes_updated'] % 50 == 0:
                            self.stdout.write(
                                f"\rEspèces mises à jour: {stats['especes_updated']}", ending=''
                            )
                    else:
                        stats['especes_not_found'] += 1
                        especes_non_trouvees.append(
                            {
                                'code': code_gonm,
                                'espece_id': espece_id,
                                'nom_francais': espece_nom,
                                'score': score,
                            }
                        )

                except ValueError:
                    stats['erreurs'] += 1
                    self.stdout.write(
                        self.style.WARNING(
                            f"\nErreur ligne {stats['total_lines']}: Données invalides\n"
                            f"  Code: {code_gonm} - {espece_nom}"
                        )
                    )
                except Exception as e:
                    stats['erreurs'] += 1
                    self.stdout.write(
                        self.style.WARNING(
                            f"\nErreur ligne {stats['total_lines']}: {e}\n"
                            f"  Code: {code_gonm} - {espece_nom}"
                        )
                    )

            self.stdout.write()  # Nouvelle ligne après la progression

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'\nErreur lors de la lecture du fichier: {e}'))
            return stats

        # Stocker les espèces non trouvées pour le rapport
        stats['especes_non_trouvees_details'] = especes_non_trouvees

        return stats

    def _display_report(self, stats: ImportStats):
        """Affiche le rapport final d'import."""
        self.stdout.write(self.style.MIGRATE_HEADING("\n=== Rapport d'import ===\n"))

        self.stdout.write(
            self.style.SUCCESS(
                f"Lignes traitées: {stats['total_lines']}\n"
                f"\nRésultats:\n"
                f"   - Espèces mises à jour: {stats['especes_updated']}\n"
                f"   - Espèces non trouvées: {stats['especes_not_found']}\n"
                f"   - Lignes sans code: {stats['empty_codes']}\n"
            )
        )

        if stats['erreurs'] > 0:
            self.stdout.write(self.style.WARNING(f"Erreurs: {stats['erreurs']}"))

        # Afficher quelques espèces non trouvées
        if stats['especes_not_found'] > 0:
            self.stdout.write(
                self.style.WARNING(
                    f"\n=== Espèces non trouvées en base ({stats['especes_not_found']}) ===\n"
                )
            )

            especes_non_trouvees = stats.get('especes_non_trouvees_details', [])
            for esp in especes_non_trouvees[:10]:  # Afficher les 10 premières
                self.stdout.write(
                    f"  - {esp['code']}: {esp['nom_francais']} (ID: {esp['espece_id']}, Score: {esp.get('score', 'N/A')})"
                )

            if len(especes_non_trouvees) > 10:
                self.stdout.write(f"\n  ... et {len(especes_non_trouvees) - 10} autres")

        # Statistiques finales
        self.stdout.write(
            self.style.MIGRATE_HEADING('\n=== Exemples d\'espèces avec code GONM ===')
        )
        exemples = Espece.objects.exclude(code_gonm='')[:5]

        if exemples.exists():
            for espece in exemples:
                self.stdout.write(
                    f"  - [{espece.code_gonm}] {espece.nom} ({espece.nom_scientifique})"
                )
        else:
            self.stdout.write("  Aucune espèce avec code GONM trouvée")

        self.stdout.write(self.style.SUCCESS('\n[OK] Import terminé avec succès!\n'))
