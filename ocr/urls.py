"""
URLs pour l'app OCR - Transcription OCR
"""

from django.urls import path

from . import views

app_name = 'ocr'

urlpatterns = [
    # Page principale
    path('', views.optimisation_ocr_home, name='optimisation_ocr_home'),
    # Sélection de répertoire pour transcription batch
    path(
        'selection-repertoire/',
        views.selection_repertoire_ocr,
        name='selection_repertoire_ocr',
    ),
    # Analyse des correspondances images/fiches
    path(
        'analyser-correspondances/',
        views.analyser_correspondances,
        name='analyser_correspondances',
    ),
    # Lancement de la transcription batch
    path(
        'lancer-transcription-batch/',
        views.lancer_transcription_batch,
        name='lancer_transcription_batch',
    ),
    # Suivi de progression du batch
    path(
        'verifier-progression/',
        views.check_batch_progress,
        name='check_batch_progress',
    ),
    # Résultats du traitement batch
    path(
        'resultats/',
        views.batch_results,
        name='batch_results',
    ),
]
