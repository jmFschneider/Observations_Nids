from pathlib import Path
from typing import Any

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from ocr.tasks import comparer_ocr_fichier_task


class Command(BaseCommand):
    help = "Lance les comparaisons OCR ↔ BDD pour des fichiers JSON."

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            "--repertoire",
            required=True,
            help="Chemin relatif sous MEDIA_ROOT contenant les fichiers OCR.",
        )
        parser.add_argument(
            "--modele-ocr",
            dest="modele_ocr",
            help="Filtrer sur le nom du modèle OCR présent dans le chemin.",
        )
        parser.add_argument(
            "--force",
            action="store_true",
            help="Forcer la réévaluation des comparaisons existantes.",
        )
        parser.add_argument(
            "--async",
            dest="async_mode",
            action="store_true",
            help="Lancer les tâches via Celery (sinon exécution synchrone).",
        )
        parser.add_argument(
            "--dry-run",
            dest="dry_run",
            action="store_true",
            help="Ne rien écrire en base.",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        repertoire: str = options["repertoire"]
        modele_ocr: str | None = options.get("modele_ocr") or None
        force: bool = bool(options.get("force"))
        dry_run: bool = bool(options.get("dry_run"))
        async_mode: bool = bool(options.get("async_mode"))

        if not repertoire or not repertoire.strip():
            raise CommandError("Le paramètre --repertoire est obligatoire.")

        media_root = Path(settings.MEDIA_ROOT).resolve()
        target_dir = (media_root / repertoire).resolve()

        try:
            target_dir.relative_to(media_root)
        except ValueError as exc:
            raise CommandError("Le répertoire doit être sous MEDIA_ROOT.") from exc

        if not target_dir.exists() or not target_dir.is_dir():
            raise CommandError(f"Répertoire introuvable sous MEDIA_ROOT: {repertoire}")

        fichiers = sorted(target_dir.rglob("*_result.json"))
        chemins_relatifs = [str(path.resolve().relative_to(media_root)) for path in fichiers]
        total_trouves = len(chemins_relatifs)

        if modele_ocr:
            chemins_relatifs = [chemin for chemin in chemins_relatifs if modele_ocr in chemin]

        options_task = {"force": force, "dry_run": dry_run}
        total_lances = 0

        for chemin in chemins_relatifs:
            if async_mode:
                comparer_ocr_fichier_task.delay(chemin, options_task)
            else:
                comparer_ocr_fichier_task(chemin, options_task)
            total_lances += 1

        self.stdout.write("Comparaison OCR - lancement")
        self.stdout.write(f"Répertoire: {repertoire}")
        self.stdout.write(f"Mode: {'async' if async_mode else 'sync'}")
        self.stdout.write(f"Fichiers trouvés: {total_trouves}")
        self.stdout.write(f"Fichiers lancés: {total_lances}")

        if modele_ocr:
            self.stdout.write(f"Filtre modèle OCR: {modele_ocr}")

        options_actives = []
        if force:
            options_actives.append("force")
        if dry_run:
            options_actives.append("dry_run")
        if not options_actives:
            options_actives.append("aucune")

        self.stdout.write(f"Options actives: {', '.join(options_actives)}")
