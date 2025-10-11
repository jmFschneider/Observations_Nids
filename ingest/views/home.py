import logging

from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render

from accounts.models import Utilisateur
from geo.models import CommuneFrance, Localisation
from ingest.models import EspeceCandidate, ImportationEnCours, TranscriptionBrute
from observations.models import FicheObservation

from .auth import est_admin

logger = logging.getLogger(__name__)


@login_required
@user_passes_test(est_admin)
def accueil_importation(request):
    """Vue d'accueil pour le système d'importation"""
    # Statistiques
    total_transcriptions = TranscriptionBrute.objects.count()
    transcriptions_traitees = TranscriptionBrute.objects.filter(traite=True).count()
    especes_candidates = EspeceCandidate.objects.count()
    especes_validees = EspeceCandidate.objects.exclude(espece_validee=None).count()
    observateurs_transcription = Utilisateur.objects.filter(est_transcription=True).count()
    total_observateurs = Utilisateur.objects.count()

    # Statistiques communes
    communes_en_base = CommuneFrance.objects.count()
    # Communes trouvées lors de cette transcription (fiches issues de transcription avec code INSEE)
    communes_transcription = Localisation.objects.filter(
        fiche__transcription=True,
        code_insee__isnull=False
    ).exclude(code_insee='').values('code_insee').distinct().count()
    # Communes dans l'ensemble des fiches (toutes fiches avec code INSEE)
    communes_fiches = Localisation.objects.filter(
        code_insee__isnull=False
    ).exclude(code_insee='').values('code_insee').distinct().count()

    importations_en_attente = ImportationEnCours.objects.filter(statut='en_attente').count()
    importations_erreur = ImportationEnCours.objects.filter(statut='erreur').count()
    importations_completees = ImportationEnCours.objects.filter(statut='complete').count()

    context = {
        'total_transcriptions': total_transcriptions,
        'transcriptions_traitees': transcriptions_traitees,
        'especes_candidates': especes_candidates,
        'especes_validees': especes_validees,
        'observateurs_transcription': observateurs_transcription,
        'total_observateurs': total_observateurs,
        'communes_en_base': communes_en_base,
        'communes_transcription': communes_transcription,
        'communes_fiches': communes_fiches,
        'importations_en_attente': importations_en_attente,
        'importations_erreur': importations_erreur,
        'importations_completees': importations_completees,
    }

    return render(request, 'ingest/accueil.html', context)


@login_required
@user_passes_test(est_admin)
def resume_importation(request):
    """Vue pour afficher un résumé des importations"""
    # Statistiques
    total_transcriptions = TranscriptionBrute.objects.count()
    transcriptions_traitees = TranscriptionBrute.objects.filter(traite=True).count()

    # Espèces
    especes_candidates = EspeceCandidate.objects.count()
    especes_validees = EspeceCandidate.objects.exclude(espece_validee=None).count()

    # Observateurs
    observateurs_transcription = Utilisateur.objects.filter(est_transcription=True).count()

    # Fiches
    fiches_importees = FicheObservation.objects.filter(observateur__est_transcription=True).count()

    # Récentes importations
    recentes_importations = ImportationEnCours.objects.filter(statut='complete').order_by(
        '-date_creation'
    )[:10]

    context = {
        'total_transcriptions': total_transcriptions,
        'transcriptions_traitees': transcriptions_traitees,
        'especes_candidates': especes_candidates,
        'especes_validees': especes_validees,
        'observateurs_transcription': observateurs_transcription,
        'fiches_importees': fiches_importees,
        'recentes_importations': recentes_importations,
    }

    return render(request, 'ingest/resume_importation.html', context)
