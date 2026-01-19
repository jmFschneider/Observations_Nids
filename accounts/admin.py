from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Utilisateur


class UtilisateurAdmin(UserAdmin):
    list_display = (
        'username',
        'email',
        'first_name',
        'last_name',
        'role',
        'est_valide',
        'est_transcription',
        'is_active',
    )
    list_filter = ('role', 'est_valide', 'est_transcription', 'is_active')
    search_fields = ('username', 'email', 'first_name', 'last_name')

    fieldsets = tuple(UserAdmin.fieldsets or ()) + (
        ('Informations supplémentaires', {'fields': ('role', 'est_valide', 'est_transcription')}),
    )

    add_fieldsets = tuple(UserAdmin.add_fieldsets or ()) + (
        ('Informations supplémentaires', {'fields': ('role', 'est_valide', 'est_transcription')}),
    )


admin.site.register(Utilisateur, UtilisateurAdmin)
