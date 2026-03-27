"""
URLs pour l'app OCR en production.
"""

from django.urls import path

from . import views

app_name = 'ocr'

urlpatterns = [
    path('', views.ocr_home, name='ocr_home'),
    path('selection/', views.selection_images, name='selection_images'),
    path('lancer/', views.lancer_ocr, name='lancer_ocr'),
    path('progression/', views.verifier_progression, name='verifier_progression'),
    path('historique/', views.historique_ocr, name='historique_ocr'),
    path('annuler/', views.annuler_ocr, name='annuler_ocr'),
]
