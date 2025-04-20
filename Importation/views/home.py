# Importation/views/home.py
import logging

from django.shortcuts import render
from django.contrib.auth.decorators import login_required, user_passes_test

from Administration.models import Utilisateur
from Observations.models import FicheObservation
from Importation.models import TranscriptionBrute, EspeceCandidate, ImportationEnCours
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

    importations_en_attente = ImportationEnCours.objects.filter(statut='en_attente').count()
    importations_erreur = ImportationEnCours.objects.filter(statut='erreur').count()
    importations_completees = ImportationEnCours.objects.filter(statut='complete').count()

    context = {
        'total_transcriptions': total_transcriptions,
        'transcriptions_traitees': transcriptions_traitees,
        'especes_candidates': especes_candidates,
        'especes_validees': especes_validees,
        'observateurs_transcription': observateurs_transcription,
        'importations_en_attente': importations_en_attente,
        'importations_erreur': importations_erreur,
        'importations_completees': importations_completees,
    }

    return render(request, 'importation/accueil.html', context)


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
    fiches_importees = FicheObservation.objects.filter(
        observateur__est_transcription=True
    ).count()

    # Récentes importations
    recentes_importations = ImportationEnCours.objects.filter(
        statut='complete'
    ).order_by('-date_creation')[:10]

    context = {
        'total_transcriptions': total_transcriptions,
        'transcriptions_traitees': transcriptions_traitees,
        'especes_candidates': especes_candidates,
        'especes_validees': especes_validees,
        'observateurs_transcription': observateurs_transcription,
        'fiches_importees': fiches_importees,
        'recentes_importations': recentes_importations,
    }

    return render(request, 'importation/resume_importation.html', context)