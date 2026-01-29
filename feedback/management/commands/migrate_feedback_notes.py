from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from feedback.models import Feedback, FeedbackMessage

class Command(BaseCommand):
    help = "Migre les notes administrateur existantes vers le modèle FeedbackMessage."

    def add_arguments(self, parser):
        parser.add_argument(
            "--commit",
            action="store_true",
            dest="commit",
            default=False,
            help="Appliquer réellement les changements en base de données.",
        )

    def handle(self, *args, **options):
        commit = options["commit"]
        if not commit:
            self.stdout.write(self.style.WARNING("MODE DRY-RUN : Aucun changement ne sera appliqué. Utilisez --commit pour valider."))

        feedbacks_with_notes = Feedback.objects.exclude(admin_note="")
        self.stdout.write(f"Trouvé {feedbacks_with_notes.count()} feedbacks avec des notes à migrer.")

        count = 0
        with transaction.atomic():
            for feedback in feedbacks_with_notes:
                self.stdout.write(f"Migration du feedback #{feedback.id} ({feedback.user})")
                
                if commit:
                    # Création du message (auteur None car on ne sait pas quel admin a écrit la note historiquement)
                    FeedbackMessage.objects.create(
                        feedback=feedback,
                        content=feedback.admin_note,
                        author=None,
                        created_at=feedback.updated_at
                    )
                    # Mise à jour de last_activity
                    feedback.last_activity = feedback.updated_at
                    feedback.save(update_fields=["last_activity"])
                    count += 1
                else:
                    self.stdout.write(f"  [Simulé] Création d'un message : {feedback.admin_note[:50]}...")

        if commit:
            self.stdout.write(self.style.SUCCESS(f"Migration terminée : {count} notes migrées."))
        else:
            self.stdout.write(self.style.WARNING("Fin de la simulation. Relancez avec --commit pour appliquer."))
