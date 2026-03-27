"""
Script de correction des communes non résolues en base de données.

Pour chaque Localisation avec commune_non_resolue=True, tente de résoudre
la commune via le géocodeur local (avec la nouvelle tolérance tirets/espaces).
Met à jour les coordonnées, code INSEE, source, etc. si une correspondance est trouvée.

Usage :
    # Dry-run (aucune écriture en BDD, affiche ce qui serait corrigé)
    python scripts/resoudre_communes_non_resolues.py --dry-run

    # Correction réelle
    python scripts/resoudre_communes_non_resolues.py

    # Via manage.py (dry-run par défaut, passer --no-dry-run pour appliquer)
    python manage.py runscript resoudre_communes_non_resolues
"""

import argparse
import os
import sys

import django

# --- Bootstrap Django (si appelé directement sans manage.py) ---
if __name__ == '__main__':
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'observations_nids.settings')
    django.setup()

from geo.models import Localisation  # noqa: E402
from geo.utils.geocoding import get_geocodeur  # noqa: E402


def run(dry_run: bool = True) -> None:
    geocodeur = get_geocodeur()

    localisations = Localisation.objects.filter(commune_non_resolue=True).select_related('fiche')
    total = localisations.count()

    if total == 0:
        print("Aucune commune non résolue en base.")
        return

    mode = "[DRY-RUN — aucune modification en BDD]" if dry_run else "[ÉCRITURE EN BDD]"
    print(f"{total} commune(s) non résolue(s) à traiter... {mode}\n")

    resolues = 0
    echecs = []

    for loc in localisations:
        nom_brut = loc.commune_ocr_brute or loc.commune
        departement = loc.departement or None
        num_fiche = loc.fiche.num_fiche if loc.fiche_id else f"loc#{loc.pk}"

        if not nom_brut or nom_brut == 'Non spécifiée':
            echecs.append((num_fiche, nom_brut, "nom vide ou non spécifié"))
            continue

        try:
            resultat = geocodeur._recherche_base_locale(nom_brut, departement)
        except Exception as exc:
            echecs.append((num_fiche, nom_brut, str(exc)))
            continue

        if resultat:
            commune_resolue = resultat.get('adresse_complete', nom_brut).split(',')[0]
            print(f"  ✓  {num_fiche} : '{nom_brut}' → '{commune_resolue}'")
            resolues += 1

            if not dry_run:
                loc.commune = commune_resolue
                loc.latitude = str(resultat['lat'])
                loc.longitude = str(resultat['lon'])
                loc.coordonnees = resultat['coordonnees_gps']
                loc.source_coordonnees = resultat['source']
                loc.precision_gps = resultat.get('precision_metres', 5000)
                if 'code_insee' in resultat:
                    loc.code_insee = resultat['code_insee']
                if resultat.get('altitude') is not None:
                    loc.altitude = resultat['altitude']
                loc.commune_non_resolue = False
                loc.commune_ocr_brute = ''
                loc.save(
                    update_fields=[
                        'commune', 'latitude', 'longitude', 'coordonnees',
                        'source_coordonnees', 'precision_gps', 'code_insee',
                        'altitude', 'commune_non_resolue', 'commune_ocr_brute',
                    ]
                )
        else:
            echecs.append((num_fiche, nom_brut, "introuvable"))

    print(f"\n--- Résultat {mode} ---")
    print(f"Résolues  : {resolues} / {total}")
    print(f"Échecs    : {len(echecs)} / {total}")

    if echecs:
        print("\nCommunes toujours non résolues :")
        for num_fiche, nom, raison in echecs:
            print(f"  ✗  {num_fiche} : '{nom}' ({raison})")

    if dry_run and resolues > 0:
        print(f"\n→ Relancer sans --dry-run pour appliquer les {resolues} correction(s).")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Résout les communes non résolues en BDD.")
    parser.add_argument(
        '--dry-run',
        action='store_true',
        default=False,
        help="Affiche les corrections sans les appliquer (défaut : False)",
    )
    args = parser.parse_args()
    run(dry_run=args.dry_run)
