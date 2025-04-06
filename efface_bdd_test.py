# efface_bdd_test.py
import os
import django

# Initialisation de l'environnement Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Observations_Nids.settings')
django.setup()

# Imports des modèles
from Observations.models import (
    FicheObservation, Observation, ResumeObservation, Nid,
    Localisation, CausesEchec, Remarque, Validation,
    HistoriqueModification, HistoriqueValidation, Utilisateur
)
from Importation.models import (
    TranscriptionBrute, EspeceCandidate, ImportationEnCours
)

# Confirmation de l'utilisateur
confirmation = input("⚠️ Cette opération va supprimer TOUTES les données liées aux fiches d'observation, aux transcriptions, et aux utilisateurs de test.\nSouhaitez-vous vraiment continuer ? (oui/non) : ")

if confirmation.lower() != "oui":
    print("❌ Opération annulée.")
    exit()

# Suppression des utilisateurs créés pour la transcription
nb_users = Utilisateur.objects.filter(est_transcription=True).count()
Utilisateur.objects.filter(est_transcription=True).delete()
print(f"👤 Utilisateurs de transcription supprimés : {nb_users}")

# Étape 1 : Supprimer les objets liés à l'importation
ImportationEnCours.objects.all().delete()
TranscriptionBrute.objects.all().delete()
EspeceCandidate.objects.all().delete()
print("📦 Données d'importation supprimées.")

# Étape 2 : Supprimer les objets secondaires
Remarque.objects.all().delete()
Validation.objects.all().delete()
HistoriqueValidation.objects.all().delete()
HistoriqueModification.objects.all().delete()
print("📝 Remarques, validations et historiques supprimés.")

# Étape 3 : Supprimer les objets liés aux fiches
Observation.objects.all().delete()
ResumeObservation.objects.all().delete()
Nid.objects.all().delete()
Localisation.objects.all().delete()
CausesEchec.objects.all().delete()
print("📊 Données liées aux fiches supprimées.")

# Étape 4 : Supprimer les fiches d'observation
FicheObservation.objects.all().delete()
print("📁 Fiches d'observation supprimées.")

print("✅ Nettoyage de la base de données terminé avec succès.")
