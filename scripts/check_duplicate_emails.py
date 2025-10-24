#!/usr/bin/env python
"""Script pour vérifier les emails en double dans la base de données"""
import os  # noqa: I001
import django  # noqa: I001

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'observations_nids.settings')
django.setup()

from django.db.models import Count  # noqa: E402, I001
from accounts.models import Utilisateur  # noqa: E402, I001

# Trouver les emails en double
duplicates = (
    Utilisateur.objects.values('email')
    .annotate(count=Count('email'))
    .filter(count__gt=1)
)

if duplicates:
    print("ERREUR: Emails en double detectes:\n")
    for dup in duplicates:
        email = dup['email']
        count = dup['count']
        print(f"  Email: {email} - {count} comptes")

        # Afficher les détails des utilisateurs
        users = Utilisateur.objects.filter(email=email)
        for user in users:
            status = "actif" if user.is_active else "inactif"
            print(f"     -> {user.username} (ID: {user.id}) - {status} - {user.role}")
        print()

    print("\nRECOMMANDATION:")
    print("Les emails devraient etre uniques. Vous devriez:")
    print("1. Supprimer ou desactiver les comptes en double")
    print("2. Ajouter une contrainte unique sur le champ email")
else:
    print("OK: Aucun email en double trouve")
