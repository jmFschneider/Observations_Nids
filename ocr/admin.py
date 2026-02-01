"""
Interface d'administration pour l'app OCR en production.
"""

from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe

from .models import TranscriptionOCR


@admin.register(TranscriptionOCR)
class TranscriptionOCRAdmin(admin.ModelAdmin):
    """Interface d'administration simplifiée pour la production."""

    list_display = [
        'id',
        'fiche_numero',
        'statut_badge',
        'modele_ocr',
        'temps_traitement_secondes',
        'date_transcription',
    ]

    list_filter = [
        'statut',
        'modele_ocr',
        'date_transcription',
    ]

    search_fields = [
        'fiche__num_fiche',
        'chemin_json',
        'chemin_image',
        'erreur_message',
    ]

    readonly_fields = [
        'date_transcription',
    ]

    fieldsets = [
        (
            '🔗 Références',
            {
                'fields': [
                    'fiche',
                    'chemin_image',
                    'chemin_json',
                ]
            },
        ),
        (
            '⚙️ Métadonnées OCR',
            {
                'fields': [
                    'modele_ocr',
                    'statut',
                    'temps_traitement_secondes',
                    'date_transcription',
                ]
            },
        ),
        (
            '❌ Erreur',
            {
                'fields': [
                    'erreur_message',
                ],
                'classes': ['collapse'],
            },
        ),
    ]

    @admin.display(description='Fiche')
    def fiche_numero(self, obj):
        """Affiche le numéro de fiche avec lien"""
        if not obj.fiche:
            return mark_safe('<span style="color: #6c757d;">Non importée</span>')
        return mark_safe(
            f'<a href="/admin/observations/ficheobservation/{obj.fiche.pk}/change/">Fiche #{obj.fiche.num_fiche}</a>'
        )

    @admin.display(description='Statut')
    def statut_badge(self, obj):
        """Affiche le statut avec un badge coloré"""
        colors = {
            'succes': '#28a745',  # success
            'erreur': '#dc3545',  # danger
            'en_cours': '#ffc107',  # warning
        }
        color = colors.get(obj.statut, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 3px; font-size: 11px;">{}</span>',
            color,
            obj.get_statut_display(),
        )
