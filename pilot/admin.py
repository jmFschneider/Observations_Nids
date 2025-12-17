"""
Interface d'administration pour l'app de pilote OCR
"""

from django.contrib import admin
from django.utils.html import format_html

from .models import TranscriptionOCR


@admin.register(TranscriptionOCR)
class TranscriptionOCRAdmin(admin.ModelAdmin):
    """Interface d'administration pour les transcriptions OCR de test"""

    list_display = [
        'id',
        'fiche_numero',
        'modele_ocr_badge',
        'type_image_badge',
        'statut_evaluation_badge',
        'score_global_colored',
        'taux_precision_display',
        'nombre_erreurs_total_display',
        'date_transcription',
    ]

    list_filter = [
        'modele_ocr',
        'type_image',
        'statut_evaluation',
        'date_transcription',
        'date_evaluation',
    ]

    search_fields = [
        'fiche__num_fiche',
        'chemin_json',
        'notes_evaluation',
    ]

    readonly_fields = [
        'date_transcription',
        'taux_precision_display',
        'nombre_erreurs_total_display',
    ]

    fieldsets = [
        (
            '🔗 Référence',
            {
                'fields': [
                    'fiche',
                    'chemin_json',
                    'chemin_image',
                ]
            },
        ),
        (
            '⚙️ Configuration OCR',
            {
                'fields': [
                    'type_image',
                    'modele_ocr',
                    'date_transcription',
                    'temps_traitement_secondes',
                ]
            },
        ),
        (
            '📊 Évaluation de la qualité',
            {
                'fields': [
                    'statut_evaluation',
                    'date_evaluation',
                    'score_global',
                    'nombre_champs_corrects',
                    'nombre_champs_total',
                    'taux_precision_display',
                ]
            },
        ),
        (
            '❌ Détail des erreurs',
            {
                'fields': [
                    'nombre_erreurs_dates',
                    'nombre_erreurs_nombres',
                    'nombre_erreurs_texte',
                    'nombre_erreurs_especes',
                    'nombre_erreurs_lieux',
                    'nombre_erreurs_total_display',
                ]
            },
        ),
        (
            '📝 Détails et notes',
            {
                'fields': [
                    'details_comparaison',
                    'notes_evaluation',
                ],
                'classes': ['collapse'],
            },
        ),
    ]

    def fiche_numero(self, obj):
        """Affiche le numéro de fiche avec lien"""
        return format_html(
            '<a href="/admin/observations/ficheobservation/{}/change/">Fiche #{}</a>',
            obj.fiche.pk,
            obj.fiche.num_fiche,
        )

    fiche_numero.short_description = 'Fiche'

    def modele_ocr_badge(self, obj):
        """Affiche le modèle OCR avec un badge coloré"""
        colors = {
            'gemini_flash': '#17a2b8',  # info
            'gemini_1.5_pro': '#28a745',  # success
            'gemini_2_pro': '#007bff',  # primary
            'gemini_2_flash': '#6c757d',  # secondary
        }
        color = colors.get(obj.modele_ocr, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 3px; font-size: 11px;">{}</span>',
            color,
            obj.get_modele_ocr_display(),
        )

    modele_ocr_badge.short_description = 'Modèle'

    def type_image_badge(self, obj):
        """Affiche le type d'image avec un badge"""
        colors = {'brute': '#ffc107', 'optimisee': '#28a745'}
        color = colors.get(obj.type_image, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 3px; font-size: 11px;">{}</span>',
            color,
            obj.get_type_image_display(),
        )

    type_image_badge.short_description = 'Image'

    def statut_evaluation_badge(self, obj):
        """Affiche le statut d'évaluation avec un badge"""
        colors = {
            'non_evaluee': '#6c757d',
            'en_cours': '#ffc107',
            'evaluee': '#28a745',
            'erreur': '#dc3545',
        }
        color = colors.get(obj.statut_evaluation, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 3px; font-size: 11px;">{}</span>',
            color,
            obj.get_statut_evaluation_display(),
        )

    statut_evaluation_badge.short_description = 'Statut'

    def score_global_colored(self, obj):
        """Affiche le score global avec une couleur selon la qualité"""
        if obj.score_global is None:
            return '-'

        if obj.score_global >= 90:
            color = '#28a745'  # vert
        elif obj.score_global >= 75:
            color = '#ffc107'  # jaune
        elif obj.score_global >= 50:
            color = '#fd7e14'  # orange
        else:
            color = '#dc3545'  # rouge

        return format_html(
            '<span style="color: {}; font-weight: bold;">{:.1f}%</span>', color, obj.score_global
        )

    score_global_colored.short_description = 'Score'
    score_global_colored.admin_order_field = 'score_global'

    def taux_precision_display(self, obj):
        """Affiche le taux de précision calculé"""
        taux = obj.taux_precision
        if taux is None:
            return '-'
        return f'{taux:.1f}%'

    taux_precision_display.short_description = 'Taux de précision'

    def nombre_erreurs_total_display(self, obj):
        """Affiche le nombre total d'erreurs"""
        total = obj.nombre_erreurs_total
        if total == 0:
            return format_html('<span style="color: #28a745;">✓ Aucune</span>')
        return format_html('<span style="color: #dc3545;">✗ {}</span>', total)

    nombre_erreurs_total_display.short_description = 'Erreurs totales'

    # Actions personnalisées
    actions = ['marquer_comme_evaluee', 'marquer_comme_non_evaluee']

    def marquer_comme_evaluee(self, request, queryset):
        """Marque les transcriptions sélectionnées comme évaluées"""
        updated = queryset.update(statut_evaluation='evaluee')
        self.message_user(
            request, f'{updated} transcription(s) marquée(s) comme évaluée(s).'
        )

    marquer_comme_evaluee.short_description = 'Marquer comme évaluée'

    def marquer_comme_non_evaluee(self, request, queryset):
        """Marque les transcriptions sélectionnées comme non évaluées"""
        updated = queryset.update(statut_evaluation='non_evaluee')
        self.message_user(
            request, f'{updated} transcription(s) marquée(s) comme non évaluée(s).'
        )

    marquer_comme_non_evaluee.short_description = 'Marquer comme non évaluée'
