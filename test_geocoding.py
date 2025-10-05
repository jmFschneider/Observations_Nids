#!/usr/bin/env python
"""Script de test du système de géocodage"""
import os

import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'observations_nids.settings')
django.setup()

from geo.utils.geocoding import get_geocodeur


def test_geocoding():
    geocodeur = get_geocodeur()

    print("=== Test du système de géocodage ===\n")

    # Test 1: Commune simple
    print("Test 1: Paris")
    result = geocodeur.geocoder_commune("Paris")
    if result:
        print(f"  [OK] Trouve: {result['adresse_complete']}")
        print(f"    Coords: {result['coordonnees_gps']}")
        print(f"    Source: {result['source']}")
    else:
        print("  [ERREUR] Non trouve")

    print()

    # Test 2: Commune avec departement
    print("Test 2: Chamonix-Mont-Blanc (Haute-Savoie)")
    result = geocodeur.geocoder_commune("Chamonix-Mont-Blanc", "Haute-Savoie")
    if result:
        print(f"  [OK] Trouve: {result['adresse_complete']}")
        print(f"    Coords: {result['coordonnees_gps']}")
        print(f"    Source: {result['source']}")
    else:
        print("  [ERREUR] Non trouve")

    print()

    # Test 3: Commune avec code departement
    print("Test 3: Lyon (code 69)")
    result = geocodeur.geocoder_commune("Lyon", "69")
    if result:
        print(f"  [OK] Trouve: {result['adresse_complete']}")
        print(f"    Coords: {result['coordonnees_gps']}")
        print(f"    Source: {result['source']}")
    else:
        print("  [ERREUR] Non trouve")

    print()

    # Test 4: Petite commune
    print("Test 4: Annecy (74)")
    result = geocodeur.geocoder_commune("Annecy", "74")
    if result:
        print(f"  [OK] Trouve: {result['adresse_complete']}")
        print(f"    Coords: {result['coordonnees_gps']}")
        print(f"    Source: {result['source']}")
    else:
        print("  [ERREUR] Non trouve")

    print()

    # Test 5: Commune ambigue (plusieurs communes avec le meme nom)
    print("Test 5: Saint-Martin sans departement (ambigue)")
    result = geocodeur.geocoder_commune("Saint-Martin")
    if result:
        print(f"  [OK] Trouve: {result['adresse_complete']}")
        print(f"    Source: {result['source']}")
    else:
        print("  Note: Plusieurs communes avec ce nom - necessite departement")

    print("\n=== Tests terminés ===")

if __name__ == '__main__':
    test_geocoding()
