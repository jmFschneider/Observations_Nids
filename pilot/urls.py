"""
URLs pour l'app pilot - Optimisation OCR
"""

from django.urls import path

from . import views

app_name = 'pilot'

urlpatterns = [
    # Page principale d'optimisation OCR
    path('optimisation-ocr/', views.optimisation_ocr_home, name='optimisation_ocr_home'),

    # Sélection de répertoire pour transcription batch
    path(
        'optimisation-ocr/selection-repertoire/',
        views.selection_repertoire_ocr,
        name='selection_repertoire_ocr',
    ),

    # Analyse des correspondances images/fiches
    path(
        'optimisation-ocr/analyser-correspondances/',
        views.analyser_correspondances,
        name='analyser_correspondances',
    ),

    # Lancement de la transcription batch
    path(
        'optimisation-ocr/lancer-transcription-batch/',
        views.lancer_transcription_batch,
        name='lancer_transcription_batch',
    ),

    # Suivi de progression du batch
    path(
        'optimisation-ocr/verifier-progression/',
        views.check_batch_progress,
        name='check_batch_progress',
    ),

    # Résultats du traitement batch
    path(
        'optimisation-ocr/resultats/',
        views.batch_results,
        name='batch_results',
    ),
]
