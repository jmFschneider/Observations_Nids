"""
Commande de management pour détecter les fichiers media orphelins.

Un fichier orphelin est un fichier présent sur le disque dans MEDIA_ROOT
mais non référencé dans aucune entrée de la base de données.

Modes :
  --dry-run  (défaut) : liste les fichiers orphelins sans rien modifier
  --execute           : déplace les orphelins dans MEDIA_ROOT/sauvegarde/

Usage :
  python manage.py audit_media_orphelins           # dry-run
  python manage.py audit_media_orphelins --execute # déplace les fichiers
"""

import os
import shutil

from django.conf import settings
from django.core.management.base import BaseCommand

from ingest.models import PreparationImage, TranscriptionBrute
from observations.models import FicheObservation, ImageSource
from ocr.models import TranscriptionOCR

# Répertoires à ignorer dans le scan (relatifs à MEDIA_ROOT)
DIRS_TO_SKIP = {"sauvegarde"}


class Command(BaseCommand):
    help = "Détecte les fichiers media orphelins (présents sur disque, absents en BDD)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--execute",
            action="store_true",
            default=False,
            help="Déplace les orphelins dans MEDIA_ROOT/sauvegarde/ (sans ce flag : dry-run).",
        )

    def handle(self, *args, **options):
        execute = options["execute"]
        media_root = str(settings.MEDIA_ROOT)
        sauvegarde_dir = os.path.join(media_root, "sauvegarde")

        mode = "EXÉCUTION" if execute else "DRY-RUN (aucune modification)"
        self.stdout.write(f"\n=== Audit media orphelins — {mode} ===\n")
        self.stdout.write(f"MEDIA_ROOT : {media_root}\n")

        # 1. Collecter tous les chemins référencés en BDD
        referenced = self._collect_referenced_paths()
        self.stdout.write(f"Chemins référencés en BDD : {len(referenced)}\n")

        # 2. Scanner les fichiers sur disque
        orphelins = self._scan_disk(media_root, referenced)

        if not orphelins:
            self.stdout.write(self.style.SUCCESS("\nAucun fichier orphelin trouvé."))
            return

        self.stdout.write(
            self.style.WARNING(f"\n{len(orphelins)} fichier(s) orphelin(s) trouvé(s) :\n")
        )
        for path in sorted(orphelins):
            self.stdout.write(f"  {path}")

        if not execute:
            self.stdout.write(
                self.style.NOTICE(
                    f"\nRelancer avec --execute pour déplacer ces fichiers dans {sauvegarde_dir}"
                )
            )
            return

        # 3. Mode execute : déplacer dans sauvegarde/
        os.makedirs(sauvegarde_dir, exist_ok=True)
        deplaces = 0
        erreurs = 0

        for rel_path in sorted(orphelins):
            src = os.path.join(media_root, rel_path)
            dst = os.path.join(sauvegarde_dir, rel_path)
            dst_dir = os.path.dirname(dst)

            try:
                os.makedirs(dst_dir, exist_ok=True)
                shutil.move(src, dst)
                self.stdout.write(self.style.SUCCESS(f"  Déplacé : {rel_path}"))
                deplaces += 1
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"  Erreur pour {rel_path} : {e}"))
                erreurs += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"\nTerminé : {deplaces} fichier(s) déplacé(s) dans sauvegarde/, "
                f"{erreurs} erreur(s)."
            )
        )

    def _collect_referenced_paths(self):
        """Collecte tous les chemins de fichiers référencés en base de données."""
        paths = set()

        def add(value):
            """Normalise et ajoute un chemin s'il est non vide."""
            if value:
                # Supprimer les slashes de début pour avoir un chemin relatif propre
                normalized = str(value).lstrip("/\\")
                if normalized:
                    paths.add(normalized)

        # ImageSource.image (FileField)
        for obj in ImageSource.objects.exclude(image="").exclude(image__isnull=True):
            add(obj.image.name)

        # PreparationImage.fichier_fusionne (FileField)
        for obj in PreparationImage.objects.exclude(fichier_fusionne="").exclude(
            fichier_fusionne__isnull=True
        ):
            add(obj.fichier_fusionne.name)

        # PreparationImage — chemins bruts (CharField)
        for obj in PreparationImage.objects.all():
            add(obj.fichier_brut_recto)
            add(obj.fichier_brut_verso)

        # FicheObservation (CharField)
        for obj in FicheObservation.objects.all():
            add(obj.chemin_image)
            add(obj.chemin_json)

        # TranscriptionOCR (CharField)
        for obj in TranscriptionOCR.objects.all():
            add(obj.chemin_image)
            add(obj.chemin_json)

        # TranscriptionBrute (CharField)
        for obj in TranscriptionBrute.objects.all():
            add(obj.fichier_source)

        return paths

    def _scan_disk(self, media_root, referenced):
        """Parcourt MEDIA_ROOT et retourne les fichiers non référencés en BDD."""
        orphelins = []

        for dirpath, dirnames, filenames in os.walk(media_root):
            # Exclure les répertoires à ignorer (modification in-place pour os.walk)
            dirnames[:] = [d for d in dirnames if d not in DIRS_TO_SKIP]

            for filename in filenames:
                # Ignorer les fichiers système
                if filename in {".gitkeep", ".DS_Store", "Thumbs.db"}:
                    continue

                abs_path = os.path.join(dirpath, filename)
                rel_path = os.path.relpath(abs_path, media_root).replace("\\", "/")

                if rel_path not in referenced:
                    orphelins.append(rel_path)

        return orphelins
