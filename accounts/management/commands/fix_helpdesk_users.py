from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from helpdesk.models import UserSettings
from helpdesk.settings import DEFAULT_USER_SETTINGS


class Command(BaseCommand):
    help = "Vérifie et crée les paramètres Helpdesk (UserSettings) manquants pour les utilisateurs."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Simule l'opération sans modifier la base de données.",
        )

    def handle(self, *args, **options):
        user_model = get_user_model()
        dry_run = options["dry_run"]

        self.stdout.write(self.style.MIME("--- Correction des paramètres Helpdesk ---"))

        users = user_model.objects.all()
        count = 0
        fixed = 0

        for user in users:
            count += 1
            try:
                # Tente d'accéder aux settings
                _ = user.usersettings_helpdesk
            except UserSettings.DoesNotExist:
                self.stdout.write(f"  - 🔧 MANQUANT : Paramètres pour {user.username}")
                if not dry_run:
                    UserSettings.objects.create(user=user, settings=DEFAULT_USER_SETTINGS)
                    fixed += 1
                else:
                    self.stdout.write(
                        self.style.WARNING("    [Simulation] Aucune action effectuée.")
                    )
            except Exception as e:
                self.stderr.write(self.style.ERROR(f"  - ❌ ERREUR pour {user.username}: {e}"))

        if dry_run:
            self.stdout.write(
                self.style.SUCCESS(
                    f"\nSimulation terminée. {count} utilisateurs traités, {fixed} auraient été corrigés."
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f"\nOpération terminée. {count} utilisateurs traités, {fixed} paramètres créés."
                )
            )
