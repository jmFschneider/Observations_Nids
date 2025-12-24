"""
Management command pour exporter les utilisateurs avec leurs droits et mots de passe hashés.
Usage: python manage.py export_users [--output fichier.json]
"""

import json

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

User = get_user_model()


class Command(BaseCommand):
    help = 'Exporte tous les utilisateurs avec leurs groupes, permissions et mots de passe hashés'

    def add_arguments(self, parser):
        parser.add_argument(
            '--output',
            type=str,
            default='users_export.json',
            help='Fichier de sortie (défaut: users_export.json)',
        )

    def handle(self, *args, **options):
        output_file = options['output']

        users_data = []

        for user in User.objects.all().order_by('id'):
            # Récupérer les groupes
            groups = list(user.groups.values_list('name', flat=True))

            # Récupérer les permissions spécifiques
            user_permissions = list(user.user_permissions.values_list('codename', flat=True))

            # Construire les données de l'utilisateur
            user_dict = {
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'password': user.password,  # Hash du mot de passe (sécurisé)
                'is_staff': user.is_staff,
                'is_active': user.is_active,
                'is_superuser': user.is_superuser,
                'date_joined': user.date_joined.isoformat() if user.date_joined else None,
                'last_login': user.last_login.isoformat() if user.last_login else None,
                # Champs personnalisés de Utilisateur
                'role': user.role,
                'est_valide': user.est_valide,
                'est_refuse': user.est_refuse,
                'est_transcription': user.est_transcription,
                # Relations
                'groups': groups,
                'user_permissions': user_permissions,
            }

            users_data.append(user_dict)

        # Exporter les données
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(users_data, f, indent=2, ensure_ascii=False)

        self.stdout.write(
            self.style.SUCCESS(
                f'Exportation réussie de {len(users_data)} utilisateurs vers {output_file}'
            )
        )
        self.stdout.write(
            self.style.WARNING(
                'IMPORTANT: Ce fichier contient des mots de passe hashés. '
                'Gardez-le sécurisé et supprimez-le après l\'import.'
            )
        )
