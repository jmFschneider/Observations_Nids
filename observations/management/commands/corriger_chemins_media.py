"""
Commande Django pour corriger les chemins des fichiers média (images et JSON).

Cette commande met à jour les champs chemin_image et chemin_json des FicheObservation
pour refléter la nouvelle structure de dossiers média.

Usage:
    python manage.py corriger_chemins_media --dry-run  # Simuler sans modifier
    python manage.py corriger_chemins_media            # Appliquer les modifications
"""

from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction

from observations.models import FicheObservation


class Command(BaseCommand):
    help = "Corrige les chemins des fichiers média (images et JSON) dans la base de données"

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Simule les modifications sans les appliquer',
        )

    def handle(self, *args, **options):
        """Point d'entrée principal de la commande."""
        dry_run = options['dry_run']

        self.stdout.write(self.style.MIGRATE_HEADING('\n=== Correction des chemins media ===\n'))

        if dry_run:
            self.stdout.write(
                self.style.WARNING('MODE DRY-RUN: Aucune modification ne sera effectuee\n')
            )

        # Statistiques
        stats = {
            'fichiers_trouves': 0,
            'fiches_mises_a_jour': 0,
            'fiches_non_trouvees': 0,
            'erreurs': 0,
        }

        # Répertoire racine des médias
        media_root = Path(settings.MEDIA_ROOT)

        # Scanner les deux dossiers
        dossiers_scan = [
            'jpeg/TRI_ANCIEN/FUSION_FULL',
            'jpeg/TRI_NOUVEAU/FUSION_CROPPED',
        ]

        fichiers_media = []

        # Collecter tous les fichiers JPEG
        for dossier in dossiers_scan:
            chemin_complet = media_root / dossier
            if not chemin_complet.exists():
                self.stdout.write(self.style.WARNING(f'Dossier non trouve: {chemin_complet}'))
                continue

            # Lister les fichiers JPEG
            for fichier in chemin_complet.glob('*.jpg'):
                stats['fichiers_trouves'] += 1

                # Construire les chemins relatifs
                chemin_image = f"{dossier}/{fichier.name}"

                # Construire le chemin JSON correspondant
                # Ex: transcription_results/jpeg/TRI_ANCIEN/FUSION_FULL/gemini_3_flash/fiche 25FINAL_result.json
                nom_sans_ext = fichier.stem  # "fiche 25FINAL"
                chemin_json = (
                    f"transcription_results/{dossier}/gemini_3_flash/{nom_sans_ext}_result.json"
                )

                # Vérifier que le JSON existe
                json_complet = media_root / chemin_json
                json_existe = json_complet.exists()

                fichiers_media.append(
                    {
                        'nom_fichier': fichier.name,
                        'chemin_image': chemin_image,
                        'chemin_json': chemin_json,
                        'json_existe': json_existe,
                        'dossier': dossier,
                    }
                )

        self.stdout.write(f"\nFichiers JPEG trouves: {stats['fichiers_trouves']}\n")

        if not fichiers_media:
            self.stdout.write(self.style.ERROR('Aucun fichier a traiter!'))
            return

        # Afficher la correspondance proposée
        self.stdout.write(self.style.MIGRATE_HEADING('\n=== Correspondances proposees ===\n'))

        for i, fm in enumerate(fichiers_media, 1):
            self.stdout.write(f"\n{i}. Fichier: {fm['nom_fichier']}")
            self.stdout.write(f"   Dossier: {fm['dossier']}")
            self.stdout.write(f"   Chemin image: {fm['chemin_image']}")
            self.stdout.write(f"   Chemin JSON:  {fm['chemin_json']}")
            if fm['json_existe']:
                self.stdout.write(self.style.SUCCESS('   JSON existe: OUI'))
            else:
                self.stdout.write(self.style.WARNING('   JSON existe: NON'))

        # Demander la correspondance avec les fiches
        self.stdout.write(self.style.MIGRATE_HEADING('\n=== Recherche des fiches en base ===\n'))

        # Stratégie 1: Chercher par nom de fichier dans chemin_image actuel
        # Stratégie 2: Demander manuellement les IDs

        fiches_a_mettre_a_jour = []

        for fm in fichiers_media:
            # Chercher les fiches qui contiennent ce nom de fichier
            fiches = FicheObservation.objects.filter(chemin_image__icontains=fm['nom_fichier'])

            if fiches.count() == 1:
                fiche = fiches.first()
                self.stdout.write(f"\n[OK] Fiche trouvee: {fiche.num_fiche} - {fm['nom_fichier']}")
                self.stdout.write(f"     Ancien chemin image: {fiche.chemin_image}")
                self.stdout.write(f"     Nouveau chemin image: {fm['chemin_image']}")
                self.stdout.write(f"     Ancien chemin JSON: {fiche.chemin_json}")
                self.stdout.write(f"     Nouveau chemin JSON: {fm['chemin_json']}")

                fiches_a_mettre_a_jour.append(
                    {
                        'fiche': fiche,
                        'nouveau_chemin_image': fm['chemin_image'],
                        'nouveau_chemin_json': fm['chemin_json'],
                    }
                )
            elif fiches.count() == 0:
                self.stdout.write(
                    self.style.WARNING(f"\n[!] Aucune fiche trouvee pour: {fm['nom_fichier']}")
                )
                stats['fiches_non_trouvees'] += 1
            else:
                self.stdout.write(
                    self.style.WARNING(
                        f"\n[!] Plusieurs fiches trouvees pour: {fm['nom_fichier']} ({fiches.count()})"
                    )
                )
                stats['fiches_non_trouvees'] += 1

        # Appliquer les modifications
        if fiches_a_mettre_a_jour:
            self.stdout.write(
                self.style.MIGRATE_HEADING(
                    f'\n=== Mise a jour de {len(fiches_a_mettre_a_jour)} fiches ===\n'
                )
            )

            if not dry_run:
                with transaction.atomic():
                    for maj in fiches_a_mettre_a_jour:
                        fiche = maj['fiche']
                        fiche.chemin_image = maj['nouveau_chemin_image']
                        fiche.chemin_json = maj['nouveau_chemin_json']
                        fiche.save(update_fields=['chemin_image', 'chemin_json'])
                        stats['fiches_mises_a_jour'] += 1

                        self.stdout.write(
                            self.style.SUCCESS(f'[OK] Fiche {fiche.num_fiche} mise a jour')
                        )
            else:
                self.stdout.write(
                    self.style.WARNING('Mode DRY-RUN: Aucune modification effectuee\n')
                )
                stats['fiches_mises_a_jour'] = len(fiches_a_mettre_a_jour)

        # Rapport final
        self._display_report(stats, dry_run)

    def _display_report(self, stats: dict, dry_run: bool):
        """Affiche le rapport final."""
        self.stdout.write(self.style.MIGRATE_HEADING('\n=== Rapport final ===\n'))

        self.stdout.write(
            f"Fichiers JPEG trouves: {stats['fichiers_trouves']}\n"
            f"Fiches mises a jour: {stats['fiches_mises_a_jour']}\n"
            f"Fiches non trouvees: {stats['fiches_non_trouvees']}\n"
            f"Erreurs: {stats['erreurs']}\n"
        )

        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    '\n[INFO] Mode DRY-RUN: Relancez sans --dry-run pour appliquer les modifications'
                )
            )
        else:
            self.stdout.write(self.style.SUCCESS('\n[OK] Modifications appliquees avec succes!'))
