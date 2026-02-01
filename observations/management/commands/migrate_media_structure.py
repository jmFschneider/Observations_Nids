"""
Commande de management pour migrer la structure des médias.
Déplace les dossiers d'images dans 'media/images/' et met à jour la base de données.
"""

import os
import shutil

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction

from ingest.models import TranscriptionBrute
from observations.models import FicheObservation, ImageSource
from ocr.models import TranscriptionOCR


class Command(BaseCommand):
    help = "Migre la structure des médias (jpeg -> images/jpeg) et met à jour la base de données."

    def handle(self, *args, **options):
        media_root = str(settings.MEDIA_ROOT)
        images_dir = os.path.join(media_root, 'images')

        self.stdout.write(f"🚀 Démarrage de la migration vers: {images_dir}")

        # 1. Création du dossier cible
        if not os.path.exists(images_dir):
            os.makedirs(images_dir)
            self.stdout.write(self.style.SUCCESS(f"✅ Dossier créé: {images_dir}"))
        else:
            self.stdout.write(f"ℹ️ Dossier déjà existant: {images_dir}")

        # Dossiers à déplacer
        folders_to_move = ['jpeg', 'jpeg_full']
        moved_folders = []

        # 2. Déplacement physique
        for folder_name in folders_to_move:
            src = os.path.join(media_root, folder_name)
            dst = os.path.join(images_dir, folder_name)

            if os.path.exists(src):
                if os.path.exists(dst):
                    self.stdout.write(
                        self.style.WARNING(f"⚠️ Destination {dst} existe déjà. Ignoré.")
                    )
                else:
                    self.stdout.write(f"📦 Déplacement de {src} vers {dst}...")
                    try:
                        shutil.move(src, dst)
                        moved_folders.append(folder_name)
                        self.stdout.write(self.style.SUCCESS("✅ Déplacement réussi."))
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f"❌ Erreur lors du déplacement: {e}"))
            else:
                self.stdout.write(f"ℹ️ Source {folder_name} introuvable.")

        # 3. Mise à jour de la base de données
        self.stdout.write("\n🔄 Mise à jour de la base de données...")

        with transaction.atomic():
            # FicheObservation
            count = 0
            qs = FicheObservation.objects.filter(chemin_image__startswith='jpeg')
            for obj in qs:
                if not obj.chemin_image.startswith('images/'):
                    obj.chemin_image = f"images/{obj.chemin_image}"
                    obj.save(update_fields=['chemin_image'])
                    count += 1
            self.stdout.write(
                self.style.SUCCESS(f"✅ FicheObservation: {count} chemins mis à jour.")
            )

            # TranscriptionOCR
            count = 0
            qs = TranscriptionOCR.objects.filter(chemin_image__startswith='jpeg')
            for obj in qs:
                if not obj.chemin_image.startswith('images/'):
                    obj.chemin_image = f"images/{obj.chemin_image}"
                    obj.save(update_fields=['chemin_image'])
                    count += 1
            self.stdout.write(
                self.style.SUCCESS(f"✅ TranscriptionOCR: {count} chemins mis à jour.")
            )

            # TranscriptionBrute
            count = 0
            qs = TranscriptionBrute.objects.filter(fichier_source__startswith='jpeg')
            for obj in qs:
                if not obj.fichier_source.startswith('images/'):
                    obj.fichier_source = f"images/{obj.fichier_source}"
                    obj.save(update_fields=['fichier_source'])
                    count += 1
            self.stdout.write(
                self.style.SUCCESS(f"✅ TranscriptionBrute: {count} chemins mis à jour.")
            )

            # ImageSource
            count = 0
            qs = ImageSource.objects.filter(image__startswith='jpeg')
            for obj in qs:
                path_str = str(obj.image)
                if path_str.startswith('jpeg') and not path_str.startswith('images/'):
                    obj.image = f"images/{path_str}"
                    obj.save(update_fields=['image'])
                    count += 1
            self.stdout.write(self.style.SUCCESS(f"✅ ImageSource: {count} chemins mis à jour."))

        self.stdout.write(self.style.SUCCESS("\n✨ Migration terminée."))
