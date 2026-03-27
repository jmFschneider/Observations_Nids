# reset_et_jeu_test.py
import os
import sys
from datetime import datetime

import django
from django.utils import timezone

from accounts.models import Utilisateur
from audit.models import HistoriqueModification

# Imports des modèles
from ingest.models import EspeceCandidate, ImportationEnCours, TranscriptionBrute
from observations.models import (
    CausesEchec,
    FicheObservation,
    Localisation,
    Nid,
    Observation,
    Remarque,
    ResumeObservation,
)
from review.models import HistoriqueValidation, Validation
from taxonomy.models import Espece

# Initialisation Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'observations_nids.settings')
django.setup()

# Confirmation
confirmation = input(
    "⚠️ Cette opération va supprimer toutes les données ET recréer un jeu de test.\nSouhaitez-vous continuer ? (oui/non) : "
)
if confirmation.lower() != "oui":
    print("❌ Opération annulée.")
    sys.exit()

# Étapes de suppression
print("🧹 Suppression des anciennes données...")

Utilisateur.objects.filter(est_transcription=True).delete()
ImportationEnCours.objects.all().delete()
TranscriptionBrute.objects.all().delete()
EspeceCandidate.objects.all().delete()
Remarque.objects.all().delete()
Validation.objects.all().delete()
HistoriqueValidation.objects.all().delete()
HistoriqueModification.objects.all().delete()
Observation.objects.all().delete()
ResumeObservation.objects.all().delete()
Nid.objects.all().delete()
Localisation.objects.all().delete()
CausesEchec.objects.all().delete()
FicheObservation.objects.all().delete()

print("✅ Données nettoyées.")

# Création du jeu de test
print("🧪 Insertion du jeu de test...")

user, created = Utilisateur.objects.get_or_create(
    username='test.obs',
    defaults={
        'first_name': 'Test',
        'last_name': 'Observateur',
        'email': 'test@exemple.com',
        'role': 'observateur',
        'est_valide': True,
        'est_transcription': True,
    },
)
if created:
    user.set_password('mdptest')
    user.save()
print("👤 Utilisateur de test : test.obs (mdp : mdptest)")

espece, _ = Espece.objects.get_or_create(nom="Mésange charbonnière", valide_par_admin=True)
print("🕊️ Espèce : Mésange charbonnière")

fiche = FicheObservation.objects.create(
    observateur=user, espece=espece, annee=2023, chemin_image="test.jpg"
)
print("📄 Fiche d’observation créée.")

fiche.localisation.commune = "Testville"
fiche.localisation.lieu_dit = "Bois des Demoiselles"
fiche.localisation.departement = "14"
fiche.localisation.paysage = "Forêt mixte"
fiche.localisation.alentours = "Chemin, haies, champs"
fiche.localisation.save()

fiche.nid.nid_prec_t_meme_couple = False
fiche.nid.hauteur_nid = 120
fiche.nid.hauteur_couvert = 140
fiche.nid.details_nid = "Nid en cavité dans un vieux tronc"
fiche.nid.save()

Observation.objects.create(
    fiche=fiche,
    date_observation=timezone.make_aware(datetime(2023, 4, 15, 10, 0)),
    nombre_oeufs=6,
    nombre_poussins=4,
    observations="Nourrissage actif",
)

fiche.resume.nombre_oeufs_pondus = 6
fiche.resume.nombre_oeufs_eclos = 5
fiche.resume.nombre_oeufs_non_eclos = 1
fiche.resume.nombre_poussins_1_2 = None
fiche.resume.nombre_poussins_3_4 = 2
fiche.resume.nombre_poussins_vol_t = 4
fiche.resume.save()

fiche.causes_echec.description = "Prédation probable, coquilles au sol"
fiche.causes_echec.save()

print("✅ Jeu de test prêt.")
