"""
Interface d'administration pour l'app OCR
"""

from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe

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
        'score_texte_colored',
        'score_numerique_colored',
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
                    'score_texte',
                    'score_numerique',
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

    @admin.display(description='Fiche')
    def fiche_numero(self, obj):
        """Affiche le numéro de fiche avec lien"""
        if not obj.fiche:
            return mark_safe('<span style="color: #dc3545;">Aucune fiche</span>')
        return mark_safe(
            f'<a href="/admin/observations/ficheobservation/{obj.fiche.pk}/change/">Fiche #{obj.fiche.num_fiche}</a>'
        )

    @admin.display(description='Modèle')
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

    @admin.display(description='Image')
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

    @admin.display(description='Statut')
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

    def _get_score_color(self, score):
        if score is None:
            return None
        if score >= 90:
            return '#28a745'  # vert
        elif score >= 75:
            return '#ffc107'  # jaune
        elif score >= 50:
            return '#fd7e14'  # orange
        else:
            return '#dc3545'  # rouge

    @admin.display(description='Global', ordering='score_global')
    def score_global_colored(self, obj):
        """Affiche le score global coloré"""
        color = self._get_score_color(obj.score_global)
        if not color:
            return '-'
        return format_html(
            '<span style="color: {}; font-weight: bold;">{:.1f}%</span>', color, obj.score_global
        )

    @admin.display(description='Texte', ordering='score_texte')
    def score_texte_colored(self, obj):
        """Affiche le score texte coloré"""
        color = self._get_score_color(obj.score_texte)
        if not color:
            return '-'
        return format_html(
            '<span style="color: {}; font-weight: bold;">{:.1f}%</span>', color, obj.score_texte
        )

    @admin.display(description='Num.', ordering='score_numerique')
    def score_numerique_colored(self, obj):
        """Affiche le score numérique coloré"""
        color = self._get_score_color(obj.score_numerique)
        if not color:
            return '-'
        return format_html(
            '<span style="color: {}; font-weight: bold;">{:.1f}%</span>', color, obj.score_numerique
        )

    @admin.display(description='Taux de précision')
    def taux_precision_display(self, obj):
        """Affiche le taux de précision calculé"""
        taux = obj.taux_precision
        if taux is None:
            return '-'
        return f'{taux:.1f}%'

    @admin.display(description='Erreurs totales')
    def nombre_erreurs_total_display(self, obj):
        """Affiche le nombre total d'erreurs"""
        total = obj.nombre_erreurs_total
        if total == 0:
            return mark_safe('<span style="color: #28a745;">✓ Aucune</span>')
        return mark_safe(f'<span style="color: #dc3545;">✗ {total}</span>')

    # Actions personnalisées
    actions = ['marquer_comme_evaluee', 'marquer_comme_non_evaluee']

    @admin.action(description='Marquer comme évaluée')
    def marquer_comme_evaluee(self, request, queryset):
        """Marque les transcriptions sélectionnées comme évaluées"""
        updated = queryset.update(statut_evaluation='evaluee')
        self.message_user(request, f'{updated} transcription(s) marquée(s) comme évaluée(s).')

    @admin.action(description='Marquer comme non évaluée')
    def marquer_comme_non_evaluee(self, request, queryset):
        """Marque les transcriptions sélectionnées comme non évaluées"""
        updated = queryset.update(statut_evaluation='non_evaluee')
        self.message_user(request, f'{updated} transcription(s) marquée(s) comme non évaluée(s).')
