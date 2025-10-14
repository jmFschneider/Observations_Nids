"""
Commande de gestion Django pour réinitialiser uniquement les transcriptions
sans toucher aux fiches créées manuellement

Usage:
    python manage.py reset_transcriptions
    python manage.py reset_transcriptions --confirm  # Sans confirmation interactive
"""

from django.core.management.base import BaseCommand
from django.db import transaction

from ingest.models import EspeceCandidate, ImportationEnCours, TranscriptionBrute
from observations.models import FicheObservation


class Command(BaseCommand):
    help = "Réinitialise uniquement les données de transcription (pas les fiches manuelles)"

    def add_arguments(self, parser):
        parser.add_argument(
            '--confirm',
            action='store_true',
            help='Confirmer la réinitialisation sans demander',
        )
        parser.add_argument(
            '--delete-fiches',
            action='store_true',
            help='Supprimer également les fiches créées par transcription',
        )

    def handle(self, *args, **options):
        confirm = options.get('confirm', False)
        delete_fiches = options.get('delete_fiches', False)

        # Afficher un avertissement
        self.stdout.write(self.style.WARNING('\n⚠️  Cette opération va supprimer :\n'))
        self.stdout.write('  • Importations en cours')
        self.stdout.write('  • Transcriptions brutes')
        self.stdout.write('  • Espèces candidates')

        if delete_fiches:
            fiches_transcription_count = FicheObservation.objects.filter(transcription=True).count()
            self.stdout.write(f'  • {fiches_transcription_count} fiches créées par transcription')
        else:
            self.stdout.write(
                self.style.SUCCESS('  ✅ Les fiches créées par transcription seront PRÉSERVÉES')
            )

        # Demander confirmation
        if not confirm:
            response = input('\nÊtes-vous sûr de vouloir continuer ? (oui/non) : ')
            if response.lower() not in ['oui', 'o', 'yes', 'y']:
                self.stdout.write(self.style.ERROR('Opération annulée.'))
                return

        # Compter les éléments avant suppression
        self.stdout.write(self.style.WARNING('\n📊 Décompte avant suppression :'))
        importations_count = ImportationEnCours.objects.count()
        transcriptions_count = TranscriptionBrute.objects.count()
        especes_candidates_count = EspeceCandidate.objects.count()

        self.stdout.write(f'  • {importations_count} importations en cours')
        self.stdout.write(f'  • {transcriptions_count} transcriptions brutes')
        self.stdout.write(f'  • {especes_candidates_count} espèces candidates')

        # Effectuer la suppression dans une transaction
        try:
            with transaction.atomic():
                self.stdout.write(self.style.WARNING('\n🗑️  Suppression en cours...'))

                # 1. Supprimer les fiches de transcription si demandé
                if delete_fiches:
                    fiches_deleted = FicheObservation.objects.filter(transcription=True).delete()
                    self.stdout.write(f'  ✓ {fiches_deleted[0]} fiches de transcription supprimées')

                # 2. Supprimer les importations en cours
                ImportationEnCours.objects.all().delete()
                self.stdout.write('  ✓ Importations en cours supprimées')

                # 3. Marquer les transcriptions comme non traitées
                # (au lieu de les supprimer, pour permettre de relancer l'importation)
                TranscriptionBrute.objects.all().update(traite=False)
                self.stdout.write('  ✓ Transcriptions marquées comme non traitées')

                # 4. Supprimer les espèces candidates
                EspeceCandidate.objects.all().delete()
                self.stdout.write('  ✓ Espèces candidates supprimées')

                self.stdout.write(
                    self.style.SUCCESS('\n✅ Réinitialisation des transcriptions terminée !\n')
                )

                self.stdout.write(self.style.SUCCESS('📋 Actions effectuées :'))
                self.stdout.write('  • Importations supprimées : prêtes à être recréées')
                self.stdout.write('  • Transcriptions réinitialisées : prêtes à être retraitées')
                self.stdout.write('  • Espèces candidates supprimées : prêtes à être re-extraites')

                if delete_fiches:
                    self.stdout.write('  • Fiches de transcription supprimées')

                self.stdout.write(
                    self.style.SUCCESS(
                        '\n💡 Vous pouvez maintenant relancer l\'importation depuis le début.'
                    )
                )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'\n❌ Erreur lors de la réinitialisation : {str(e)}')
            )
            raise
