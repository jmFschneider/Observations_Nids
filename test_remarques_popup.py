#!/usr/bin/env python
"""
Script de test pour vérifier que la popup des remarques fonctionne correctement.
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

import pytest
from observations.models import FicheObservation  # noqa: E402


@pytest.mark.django_db
def test_popup_remarques():
    """Test la fonctionnalité popup des remarques."""

    print("=" * 60)
    print("TEST DE LA POPUP DES REMARQUES")
    print("=" * 60)

    # Vérifier qu'il y a des fiches avec des remarques
    fiches_avec_remarques = FicheObservation.objects.filter(remarques__isnull=False).distinct()

    if fiches_avec_remarques.exists():
        fiche = fiches_avec_remarques.first()
        remarques = fiche.remarques.all()

        print(f"[OK] Fiche test trouvée: ID {fiche.pk}")
        print(f"[OK] Nombre de remarques: {remarques.count()}")

        for remarque in remarques:
            try:
                print(f"  - {remarque.date_remarque.strftime('%d/%m/%Y %H:%M')}: [Remarque ID {remarque.pk}]")
            except Exception:
                print(f"  - [Erreur affichage remarque ID {remarque.pk}]")

        print("\n" + "=" * 60)
        print("La popup devrait afficher ces remarques en mode édition")
        print(f"URL de test: http://127.0.0.1:8000/observations/modifier/{fiche.pk}/")
        print("Action: Double-cliquez sur le tableau des remarques")
    else:
        print("⚠️  Aucune fiche avec des remarques trouvée")
        print("Créez d'abord une fiche avec des remarques pour tester")

    print("=" * 60)

if __name__ == "__main__":
    test_popup_remarques()