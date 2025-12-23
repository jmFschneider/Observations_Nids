"""
Management command pour importer les utilisateurs depuis un export JSON.
Usage: python manage.py import_users [--input fichier.json] [--skip-existing]
"""

import json
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.db import transaction
from django.utils.dateparse import parse_datetime

User = get_user_model()


class Command(BaseCommand):
    help = 'Importe les utilisateurs depuis un fichier JSON avec leurs groupes et permissions'

    def add_arguments(self, parser):
        parser.add_argument(
            '--input',
            type=str,
            default='users_export.json',
            help='Fichier d\'entrée (défaut: users_export.json)',
        )
        parser.add_argument(
            '--skip-existing',
            action='store_true',
            help='Ignore les utilisateurs qui existent déjà (basé sur username)',
        )
        parser.add_argument(
            '--update-existing',
            action='store_true',
            help='Met à jour les utilisateurs existants au lieu de les ignorer',
        )

    def handle(self, *args, **options):
        input_file = options['input']
        skip_existing = options['skip_existing']
        update_existing = options['update_existing']

        # Vérifier que les fichiers existent
        try:
            with open(input_file, 'r', encoding='utf-8') as f:
                users_data = json.load(f)
        except FileNotFoundError:
            self.stdout.write(
                self.style.ERROR(f'Fichier {input_file} introuvable')
            )
            return
        except json.JSONDecodeError as e:
            self.stdout.write(
                self.style.ERROR(f'Erreur de parsing JSON: {e}')
            )
            return

        created_count = 0
        updated_count = 0
        skipped_count = 0

        with transaction.atomic():
            for user_data in users_data:
                username = user_data['username']

                # Vérifier si l'utilisateur existe
                try:
                    user = User.objects.get(username=username)
                    user_exists = True
                except User.DoesNotExist:
                    user_exists = False

                if user_exists:
                    if skip_existing:
                        self.stdout.write(
                            self.style.WARNING(
                                f'Utilisateur {username} ignoré (déjà existant)'
                            )
                        )
                        skipped_count += 1
                        continue
                    elif update_existing:
                        self.stdout.write(
                            self.style.WARNING(
                                f'Mise à jour de l\'utilisateur {username}'
                            )
                        )
                    else:
                        self.stdout.write(
                            self.style.ERROR(
                                f'Utilisateur {username} existe déjà. '
                                'Utilisez --skip-existing ou --update-existing'
                            )
                        )
                        return

                # Créer ou mettre à jour l'utilisateur
                if not user_exists:
                    user = User()

                # Assigner les champs de base
                user.username = username
                user.email = user_data['email']
                user.first_name = user_data['first_name']
                user.last_name = user_data['last_name']
                user.password = user_data['password']  # Déjà hashé
                user.is_staff = user_data['is_staff']
                user.is_active = user_data['is_active']
                user.is_superuser = user_data['is_superuser']

                # Champs personnalisés
                user.role = user_data.get('role', 'observateur')
                user.est_valide = user_data.get('est_valide', False)
                user.est_refuse = user_data.get('est_refuse', False)
                user.est_transcription = user_data.get('est_transcription', False)

                # Dates
                if user_data.get('date_joined'):
                    user.date_joined = parse_datetime(user_data['date_joined'])
                if user_data.get('last_login'):
                    user.last_login = parse_datetime(user_data['last_login'])

                user.save()

                # Gérer les groupes
                user.groups.clear()
                for group_name in user_data.get('groups', []):
                    group, created = Group.objects.get_or_create(name=group_name)
                    user.groups.add(group)

                # Gérer les permissions spécifiques
                user.user_permissions.clear()
                for perm_codename in user_data.get('user_permissions', []):
                    try:
                        permission = Permission.objects.get(codename=perm_codename)
                        user.user_permissions.add(permission)
                    except Permission.DoesNotExist:
                        self.stdout.write(
                            self.style.WARNING(
                                f'Permission {perm_codename} introuvable pour {username}'
                            )
                        )

                if user_exists and update_existing:
                    updated_count += 1
                else:
                    created_count += 1

        # Résumé
        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write(
            self.style.SUCCESS(
                f'Importation terminée:'
            )
        )
        self.stdout.write(
            self.style.SUCCESS(
                f'  - {created_count} utilisateur(s) créé(s)'
            )
        )
        if update_existing:
            self.stdout.write(
                self.style.SUCCESS(
                    f'  - {updated_count} utilisateur(s) mis à jour'
                )
            )
        if skip_existing:
            self.stdout.write(
                self.style.WARNING(
                    f'  - {skipped_count} utilisateur(s) ignoré(s)'
                )
            )
        self.stdout.write(self.style.SUCCESS('=' * 60))
