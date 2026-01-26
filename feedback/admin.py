from django.contrib import admin

from .models import Feedback


@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ('created_at', 'user', 'category', 'urgency', 'status', 'ai_summary')
    list_filter = ('category', 'status', 'urgency', 'created_at')
    search_fields = ('content', 'user__username', 'ai_summary')
    readonly_fields = ('created_at', 'updated_at', 'ai_summary', 'sentiment', 'category', 'urgency')

    fieldsets = (
        ('Information Utilisateur', {'fields': ('user', 'url_source', 'created_at')}),
        ('Contenu', {'fields': ('content', 'status')}),
        (
            'Analyse IA',
            {
                'fields': ('category', 'urgency', 'sentiment', 'ai_summary'),
                'description': 'Ces champs sont automatiquement remplis par Gemini.',
            },
        ),
    )

    def has_add_permission(self, request):
        return False  # On ne crée pas de feedback manuellement dans l'admin
