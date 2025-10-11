#!/usr/bin/env python
"""
Script de test pour vérifier le fallback automatique entre MariaDB et SQLite.

Ce script permet de tester que la configuration bascule automatiquement vers SQLite
lorsque MariaDB n'est pas accessible.
"""

import os
import sys
from pathlib import Path

import django

# Ajouter le répertoire du projet au PYTHONPATH
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

# Configurer Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'observations_nids.settings')
django.setup()

from django.conf import settings  # noqa: E402


def test_database_config():
    """Test et affiche la configuration de base de données active."""

    print("=" * 60)
    print("TEST DE CONFIGURATION BASE DE DONNÉES")
    print("=" * 60)

    db_config = settings.DATABASES['default']
    engine = db_config['ENGINE']

    if 'sqlite3' in engine:
        print("[OK] Base de données active: SQLite")
        print(f"  Fichier: {db_config['NAME']}")

        # Vérifier si le fichier existe
        if os.path.exists(db_config['NAME']):
            print(f"  Taille: {os.path.getsize(db_config['NAME'])} bytes")
        else:
            print("  Le fichier de base de données n'existe pas encore")

    elif 'mysql' in engine:
        print("[OK] Base de données active: MariaDB/MySQL")
        print(f"  Host: {db_config['HOST']}:{db_config['PORT']}")
        print(f"  Database: {db_config['NAME']}")
        print(f"  User: {db_config['USER']}")

    else:
        print(f"[WARN] Engine non reconnu: {engine}")

    print("=" * 60)
    print("Pour forcer l'utilisation de SQLite, décommentez les lignes")
    print("dans settings_local.py ou définissez DJANGO_DB=sqlite")
    print("=" * 60)

if __name__ == "__main__":
    test_database_config()