"""
Commande Django pour analyser les correspondances entre le CSV GONM et la base de données.

Cette commande génère un CSV d'analyse avec des scores de correspondance
pour chaque espèce, permettant de déterminer le meilleur seuil d'importation.

Usage:
    python manage.py analyser_correspondances_gonm
    python manage.py analyser_correspondances_gonm --output analyse.csv
"""

import csv
from difflib import SequenceMatcher
from pathlib import Path
from typing import TypedDict

from django.core.management.base import BaseCommand

from taxonomy.models import Espece


class StatsDict(TypedDict):
    """Type definition for stats dictionary."""

    total_lignes: int
    avec_correspondance: int
    sans_correspondance: int
    scores: list[float]


class Command(BaseCommand):
    help = "Analyse les correspondances entre le CSV GONM et la base de données"

    # Chemin par défaut du fichier CSV
    DEFAULT_CSV_PATH = r"C:\Projets\GONM\codes-especes-normandie.csv"
    DEFAULT_OUTPUT_PATH = r"C:\Projets\GONM\analyse-correspondances-gonm.csv"

    def add_arguments(self, parser):
        parser.add_argument(
            '--file',
            type=str,
            default=self.DEFAULT_CSV_PATH,
            help='Chemin vers le fichier CSV GONM source',
        )
        parser.add_argument(
            '--output',
            type=str,
            default=self.DEFAULT_OUTPUT_PATH,
            help='Chemin du fichier CSV de sortie pour l\'analyse',
        )

    def handle(self, *args, **options):
        """Point d'entrée principal de la commande."""
        self.stdout.write(
            self.style.MIGRATE_HEADING('\n=== Analyse des correspondances GONM ===\n')
        )

        # Vérifier que le fichier source existe
        csv_file = Path(options['file'])
        if not csv_file.exists():
            self.stdout.write(self.style.ERROR(f"Fichier source introuvable: {csv_file}"))
            return

        output_file = Path(options['output'])

        self.stdout.write(f"Fichier source: {csv_file}")
        self.stdout.write(f"Fichier d'analyse: {output_file}\n")

        # Analyser les correspondances
        stats = self._analyser_correspondances(csv_file, output_file)

        # Afficher le rapport
        self._display_report(stats, output_file)

    def _calculer_similarite(self, str1: str, str2: str) -> float:
        """
        Calcule la similarité entre deux chaînes (0.0 à 1.0).
        Utilise SequenceMatcher de difflib.
        """
        if not str1 or not str2:
            return 0.0

        # Normaliser : minuscules et strip
        str1 = str1.lower().strip()
        str2 = str2.lower().strip()

        return SequenceMatcher(None, str1, str2).ratio()

    def _nettoyer_nom_scientifique(self, nom: str) -> str:
        """
        Nettoie un nom scientifique en enlevant l'auteur et la date.
        Ex: "Anas platyrhynchos Linnaeus, 1758" -> "Anas platyrhynchos"
        """
        if not nom:
            return ""

        # Enlever tout ce qui suit après les 2 premiers mots (genre + espèce)
        parts = nom.strip().split()
        if len(parts) >= 2:
            return f"{parts[0]} {parts[1]}"
        return nom.strip()

    def _trouver_meilleure_correspondance(self, nom_sci_csv: str, nom_fr_csv: str, nom_en_csv: str):
        """
        Trouve la meilleure correspondance en base pour une espèce du CSV.
        Retourne l'espèce trouvée et les scores de correspondance.
        """
        meilleure_espece = None
        meilleur_score = 0.0
        meilleurs_scores_details = {
            'nom_scientifique': 0.0,
            'nom_francais': 0.0,
            'nom_anglais': 0.0,
        }

        # Nettoyer le nom scientifique CSV
        nom_sci_csv_clean = self._nettoyer_nom_scientifique(nom_sci_csv)

        # Parcourir toutes les espèces en base
        for espece in Espece.objects.all():
            scores = {}

            # Score nom scientifique (nettoyé)
            nom_sci_base_clean = self._nettoyer_nom_scientifique(espece.nom_scientifique)
            scores['nom_scientifique'] = self._calculer_similarite(
                nom_sci_csv_clean, nom_sci_base_clean
            )

            # Score nom français
            scores['nom_francais'] = self._calculer_similarite(nom_fr_csv, espece.nom)

            # Score nom anglais
            scores['nom_anglais'] = self._calculer_similarite(nom_en_csv, espece.nom_anglais)

            # Calculer le score moyen (uniquement sur les champs non vides)
            scores_valides = [v for v in scores.values() if v > 0]
            score_moyen = sum(scores_valides) / len(scores_valides) if scores_valides else 0.0

            # Bonus : si au moins un champ matche parfaitement, augmenter le score minimal
            if scores['nom_scientifique'] == 1.0:
                # Nom scientifique parfait = très forte indication
                score_moyen = max(score_moyen, 0.95)
            elif scores['nom_francais'] == 1.0 or scores['nom_anglais'] == 1.0:
                # Nom français ou anglais parfait = forte indication
                score_moyen = max(score_moyen, 0.85)

            # Garder la meilleure correspondance
            if score_moyen > meilleur_score:
                meilleur_score = score_moyen
                meilleure_espece = espece
                meilleurs_scores_details = scores

        return meilleure_espece, meilleur_score, meilleurs_scores_details

    def _analyser_correspondances(self, csv_file: Path, output_file: Path) -> StatsDict:
        """
        Analyse toutes les correspondances et génère le CSV de résultats.
        """
        stats: StatsDict = {
            'total_lignes': 0,
            'avec_correspondance': 0,
            'sans_correspondance': 0,
            'scores': [],
        }

        # Préparer le fichier de sortie
        output_rows = []

        self.stdout.write("Analyse en cours...\n")

        try:
            # Lire le fichier CSV source
            with open(csv_file, encoding='utf-8-sig') as f:
                reader = csv.DictReader(f, delimiter=';')

                for row in reader:
                    code = row.get('Code', '').strip()
                    nom_sci = row.get('Nom scientifique', '').strip()
                    nom_fr = row.get('Nom français vernaculaire', '').strip()
                    nom_en = row.get('Nom anglais', '').strip()

                    # Ignorer les lignes vides
                    if not code or not nom_sci:
                        continue

                    stats['total_lignes'] += 1

                    # Trouver la meilleure correspondance
                    espece, score_moyen, scores_details = self._trouver_meilleure_correspondance(
                        nom_sci, nom_fr, nom_en
                    )

                    # Préparer la ligne de sortie
                    output_row = {
                        'code_gonm': code,
                        'nom_scientifique_csv': nom_sci,
                        'nom_francais_csv': nom_fr,
                        'nom_anglais_csv': nom_en,
                        'espece_trouvee_id': espece.id if espece else '',
                        'espece_trouvee_nom': espece.nom if espece else '',
                        'espece_trouvee_nom_sci': espece.nom_scientifique if espece else '',
                        'espece_trouvee_nom_en': espece.nom_anglais if espece else '',
                        'score_nom_scientifique': f"{scores_details['nom_scientifique']:.4f}",
                        'score_nom_francais': f"{scores_details['nom_francais']:.4f}",
                        'score_nom_anglais': f"{scores_details['nom_anglais']:.4f}",
                        'score_moyen': f"{score_moyen:.4f}",
                        'score_pourcent': f"{score_moyen * 100:.2f}%",
                    }

                    output_rows.append(output_row)
                    stats['scores'].append(score_moyen)

                    if espece:
                        stats['avec_correspondance'] += 1
                    else:
                        stats['sans_correspondance'] += 1

                    # Afficher la progression
                    if stats['total_lignes'] % 50 == 0:
                        self.stdout.write(f"\rLignes traitées: {stats['total_lignes']}", ending='')

            self.stdout.write()  # Nouvelle ligne

            # Trier les résultats par score décroissant
            output_rows.sort(key=lambda x: float(x['score_moyen']), reverse=True)

            # Écrire le fichier de sortie
            if output_rows:
                with open(output_file, 'w', encoding='utf-8-sig', newline='') as f:
                    fieldnames = output_rows[0].keys()
                    writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=';')
                    writer.writeheader()
                    writer.writerows(output_rows)

                self.stdout.write(
                    self.style.SUCCESS(f"\n[OK] Fichier d'analyse cree: {output_file}")
                )

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'\nErreur lors de l\'analyse: {e}'))
            return stats

        return stats

    def _display_report(self, stats: StatsDict, output_file: Path):
        """Affiche le rapport d'analyse."""
        self.stdout.write(self.style.MIGRATE_HEADING("\n=== Rapport d'analyse ===\n"))

        self.stdout.write(
            f"Lignes analysées: {stats['total_lignes']}\n"
            f"Avec correspondance: {stats['avec_correspondance']}\n"
            f"Sans correspondance: {stats['sans_correspondance']}\n"
        )

        if stats['scores']:
            scores = stats['scores']
            self.stdout.write(self.style.MIGRATE_HEADING("\n=== Distribution des scores ===\n"))

            # Statistiques de base
            score_min = min(scores) * 100
            score_max = max(scores) * 100
            score_moyen = (sum(scores) / len(scores)) * 100

            self.stdout.write(
                f"Score minimum: {score_min:.2f}%\n"
                f"Score maximum: {score_max:.2f}%\n"
                f"Score moyen: {score_moyen:.2f}%\n"
            )

            # Répartition par tranches
            tranches = {
                '100%': 0,
                '90-99%': 0,
                '80-89%': 0,
                '70-79%': 0,
                '60-69%': 0,
                '< 60%': 0,
            }

            for score in scores:
                pct = score * 100
                if pct >= 100:
                    tranches['100%'] += 1
                elif pct >= 90:
                    tranches['90-99%'] += 1
                elif pct >= 80:
                    tranches['80-89%'] += 1
                elif pct >= 70:
                    tranches['70-79%'] += 1
                elif pct >= 60:
                    tranches['60-69%'] += 1
                else:
                    tranches['< 60%'] += 1

            self.stdout.write("\nRepartition par tranches:\n")
            for tranche, count in tranches.items():
                pct_total = (count / len(scores)) * 100 if scores else 0
                barre = '#' * int(pct_total / 2)
                self.stdout.write(f"  {tranche:8} : {count:4} ({pct_total:5.1f}%) {barre}")

            self.stdout.write(
                self.style.SUCCESS(
                    f"\n[OK] Analyse terminee avec succes!\n"
                    f"[OK] Consultez le fichier: {output_file}\n"
                )
            )
