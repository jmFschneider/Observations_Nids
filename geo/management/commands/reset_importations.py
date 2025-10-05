"""
Commande de gestion Django pour réinitialiser les importations
tout en préservant la table geo_commune_france

Usage:
    python manage.py reset_importations
    python manage.py reset_importations --confirm  # Sans confirmation interactive
"""

from django.core.management.base import BaseCommand
from django.db import connection, transaction

from accounts.models import Utilisateur
from audit.models import HistoriqueModification
from ingest.models import EspeceCandidate, ImportationEnCours, TranscriptionBrute
from observations.models import (
    CausesEchec,
    EtatCorrection,
    FicheObservation,
    Nid,
    Observation,
    Remarque,
    ResumeObservation,
)
from review.models import HistoriqueValidation, Validation


class Command(BaseCommand):
    help = "Réinitialise toutes les données d'importation en préservant geo_commune_france"

    def add_arguments(self, parser):
        parser.add_argument(
            '--confirm',
            action='store_true',
            help='Confirmer la réinitialisation sans demander',
        )
        parser.add_argument(
            '--keep-users',
            action='store_true',
            help='Conserver les utilisateurs (sauf ceux créés par transcription)',
        )

    def handle(self, *args, **options):
        confirm = options.get('confirm', False)
        keep_users = options.get('keep_users', False)

        # Afficher un avertissement
        self.stdout.write(
            self.style.WARNING(
                '\n⚠️  ATTENTION : Cette opération va supprimer TOUTES les données suivantes :\n'
            )
        )
        self.stdout.write('  • Fiches d\'observation')
        self.stdout.write('  • Observations')
        self.stdout.write('  • Remarques')
        self.stdout.write('  • Historique des modifications')
        self.stdout.write('  • États de correction')
        self.stdout.write('  • Importations en cours')
        self.stdout.write('  • Transcriptions brutes')
        self.stdout.write('  • Espèces candidates')
        self.stdout.write('  • Validations et historique de révision')

        if not keep_users:
            self.stdout.write('  • Utilisateurs créés par transcription')

        self.stdout.write(
            self.style.SUCCESS(
                '\n✅ Les données suivantes seront PRÉSERVÉES :\n'
            )
        )
        self.stdout.write('  • geo_commune_france (toutes les communes)')
        self.stdout.write('  • taxonomy_espece (catalogue des espèces)')

        if keep_users:
            self.stdout.write('  • Tous les utilisateurs')

        # Demander confirmation
        if not confirm:
            response = input('\nÊtes-vous sûr de vouloir continuer ? (oui/non) : ')
            if response.lower() not in ['oui', 'o', 'yes', 'y']:
                self.stdout.write(self.style.ERROR('Opération annulée.'))
                return

        # Compter les éléments avant suppression
        self.stdout.write(self.style.WARNING('\n📊 Décompte avant suppression :'))
        fiches_count = FicheObservation.objects.count()
        obs_count = Observation.objects.count()
        remarques_count = Remarque.objects.count()
        historique_count = HistoriqueModification.objects.count()
        importations_count = ImportationEnCours.objects.count()
        transcriptions_count = TranscriptionBrute.objects.count()
        especes_candidates_count = EspeceCandidate.objects.count()
        users_transcription_count = Utilisateur.objects.filter(est_transcription=True).count()

        self.stdout.write(f'  • {fiches_count} fiches d\'observation')
        self.stdout.write(f'  • {obs_count} observations')
        self.stdout.write(f'  • {remarques_count} remarques')
        self.stdout.write(f'  • {historique_count} entrées d\'historique')
        self.stdout.write(f'  • {importations_count} importations en cours')
        self.stdout.write(f'  • {transcriptions_count} transcriptions brutes')
        self.stdout.write(f'  • {especes_candidates_count} espèces candidates')
        if not keep_users:
            self.stdout.write(f'  • {users_transcription_count} utilisateurs de transcription')

        # Effectuer la suppression dans une transaction
        try:
            with transaction.atomic():
                self.stdout.write(self.style.WARNING('\n🗑️  Suppression en cours...'))

                # 1. Supprimer l'historique de validation et les validations
                HistoriqueValidation.objects.all().delete()
                Validation.objects.all().delete()
                self.stdout.write('  ✓ Validations et historique supprimés')

                # 2. Supprimer les remarques
                Remarque.objects.all().delete()
                self.stdout.write('  ✓ Remarques supprimées')

                # 3. Supprimer les observations
                Observation.objects.all().delete()
                self.stdout.write('  ✓ Observations supprimées')

                # 4. Supprimer l'historique
                HistoriqueModification.objects.all().delete()
                self.stdout.write('  ✓ Historique des modifications supprimé')

                # 5. Supprimer les objets liés aux fiches (OneToOne)
                # Ces objets seront supprimés en cascade avec les fiches, mais on peut les supprimer explicitement
                ResumeObservation.objects.all().delete()
                CausesEchec.objects.all().delete()
                Nid.objects.all().delete()
                EtatCorrection.objects.all().delete()
                # Localisation sera supprimé via la cascade depuis geo
                self.stdout.write('  ✓ Objets liés aux fiches supprimés')

                # 6. Supprimer les fiches d'observation
                FicheObservation.objects.all().delete()
                self.stdout.write('  ✓ Fiches d\'observation supprimées')

                # 7. Supprimer les importations en cours
                ImportationEnCours.objects.all().delete()
                self.stdout.write('  ✓ Importations en cours supprimées')

                # 8. Supprimer les transcriptions brutes
                TranscriptionBrute.objects.all().delete()
                self.stdout.write('  ✓ Transcriptions brutes supprimées')

                # 9. Supprimer les espèces candidates
                EspeceCandidate.objects.all().delete()
                self.stdout.write('  ✓ Espèces candidates supprimées')

                # 10. Supprimer les utilisateurs de transcription (optionnel)
                if not keep_users:
                    Utilisateur.objects.filter(est_transcription=True).delete()
                    self.stdout.write('  ✓ Utilisateurs de transcription supprimés')

                # 11. Réinitialiser les séquences d'auto-incrémentation (SQLite/PostgreSQL)
                self.reset_sequences()

                self.stdout.write(
                    self.style.SUCCESS(
                        '\n✅ Réinitialisation terminée avec succès !\n'
                    )
                )

                # Afficher le résumé
                self.stdout.write(self.style.SUCCESS('📊 Résumé :'))
                self.stdout.write(f'  • {fiches_count} fiches supprimées')
                self.stdout.write(f'  • {obs_count} observations supprimées')
                self.stdout.write(f'  • {remarques_count} remarques supprimées')
                self.stdout.write(f'  • {historique_count} entrées d\'historique supprimées')
                self.stdout.write(f'  • {importations_count} importations supprimées')
                self.stdout.write(f'  • {transcriptions_count} transcriptions supprimées')
                self.stdout.write(f'  • {especes_candidates_count} espèces candidates supprimées')
                if not keep_users:
                    self.stdout.write(f'  • {users_transcription_count} utilisateurs supprimés')

                # Vérifier que geo_commune_france est intact
                with connection.cursor() as cursor:
                    cursor.execute("SELECT COUNT(*) FROM geo_commune_france")
                    communes_count = cursor.fetchone()[0]
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'\n✅ geo_commune_france intact : {communes_count} communes préservées'
                        )
                    )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(
                    f'\n❌ Erreur lors de la réinitialisation : {str(e)}'
                )
            )
            raise

    def reset_sequences(self):
        """Réinitialise les séquences d'auto-incrémentation"""
        with connection.cursor() as cursor:
            # Déterminer le type de base de données
            db_vendor = connection.vendor

            if db_vendor == 'sqlite':
                # SQLite : réinitialiser la séquence dans sqlite_sequence
                tables = [
                    'observations_ficheobservation',
                    'observations_observation',
                    'observations_remarque',
                    'audit_historiquemodification',
                    'ingest_importationencours',
                    'ingest_transcriptionbrute',
                    'ingest_espececandidate',
                    'geo_localisation',
                    'observations_nid',
                    'observations_resumeobservation',
                    'observations_causesechec',
                    'observations_etatcorrection',
                ]

                for table in tables:
                    try:
                        cursor.execute(
                            f"DELETE FROM sqlite_sequence WHERE name='{table}'"
                        )
                    except Exception:
                        pass  # La table peut ne pas exister dans sqlite_sequence

                self.stdout.write('  ✓ Séquences SQLite réinitialisées')

            elif db_vendor == 'postgresql':
                # PostgreSQL : réinitialiser les séquences
                sequences = [
                    'observations_ficheobservation_num_fiche_seq',
                    'observations_observation_id_seq',
                    'observations_remarque_id_seq',
                    'audit_historiquemodification_id_seq',
                    'ingest_importationencours_id_seq',
                    'ingest_transcriptionbrute_id_seq',
                    'ingest_espececandidate_id_seq',
                    'geo_localisation_id_seq',
                    'observations_nid_id_seq',
                    'observations_resumeobservation_id_seq',
                    'observations_causesechec_id_seq',
                    'observations_etatcorrection_id_seq',
                ]

                for sequence in sequences:
                    try:
                        cursor.execute(f"ALTER SEQUENCE {sequence} RESTART WITH 1")
                    except Exception:
                        pass  # La séquence peut ne pas exister

                self.stdout.write('  ✓ Séquences PostgreSQL réinitialisées')

            else:
                self.stdout.write(
                    f'  ⚠️  Réinitialisation des séquences non supportée pour {db_vendor}'
                )
