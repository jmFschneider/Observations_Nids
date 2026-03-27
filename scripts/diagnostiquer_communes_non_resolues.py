"""
Diagnostic des communes non résolues : affiche le nom OCR brut et les
communes les plus proches trouvées en BDD (par département).

Permet d'identifier visuellement les patterns d'échec (accents, tirets,
abréviations, fautes OCR...) avant d'implémenter des corrections.

Usage :
    docker compose exec web python scripts/diagnostiquer_communes_non_resolues.py
    docker compose exec web python scripts/diagnostiquer_communes_non_resolues.py --top 5
    docker compose exec web python scripts/diagnostiquer_communes_non_resolues.py --dept 14
"""

import argparse
import difflib
import os
import sys
import unicodedata

import django

if __name__ == '__main__':
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'observations_nids.settings')
    django.setup()

from geo.models import CommuneFrance, Localisation  # noqa: E402


def strip_accents(s: str) -> str:
    return ''.join(
        c for c in unicodedata.normalize('NFD', s)
        if unicodedata.category(c) != 'Mn'
    )


def normaliser(s: str) -> str:
    return strip_accents(s.strip().upper().replace('-', ' '))


def communes_proches(nom_ocr: str, departement: str | None, top: int) -> list[tuple[float, str]]:
    """Retourne les `top` communes les plus proches par similarité de chaîne."""
    qs = CommuneFrance.objects.all()
    if departement and departement != '00':
        dept = str(departement)
        if dept.isdigit() and len(dept) <= 3:
            qs = qs.filter(code_departement=dept)
        else:
            qs = qs.filter(departement__icontains=dept)

    noms_bdd = list(qs.values_list('nom', flat=True))
    if not noms_bdd:
        noms_bdd = list(CommuneFrance.objects.values_list('nom', flat=True))

    nom_normalise = normaliser(nom_ocr)
    noms_normalises = [normaliser(n) for n in noms_bdd]

    scores = [
        (difflib.SequenceMatcher(None, nom_normalise, n).ratio(), noms_bdd[i])
        for i, n in enumerate(noms_normalises)
    ]
    scores.sort(reverse=True)
    return scores[:top]


def run(top: int = 3, dept: str | None = None) -> None:
    dept_filtre = dept
    qs = Localisation.objects.filter(commune_non_resolue=True).select_related('fiche')
    if dept_filtre:
        qs = qs.filter(departement=dept_filtre)

    total = qs.count()
    if total == 0:
        print("Aucune commune non résolue.")
        return

    print(f"{total} commune(s) non résolue(s)\n")
    print(f"{'Fiche':<12} {'Dept':<6} {'Nom OCR brut':<35} {'Suggestions BDD (score)'}")
    print("-" * 110)

    for loc in qs.order_by('departement', 'commune_ocr_brute'):
        nom_brut = loc.commune_ocr_brute or loc.commune
        dept = loc.departement or '?'
        num_fiche = loc.fiche.num_fiche if loc.fiche_id else f"loc#{loc.pk}"

        suggestions = communes_proches(nom_brut, loc.departement, top)
        suggestions_str = '  |  '.join(
            f"{nom} ({score:.0%})" for score, nom in suggestions
        )

        print(f"{num_fiche:<12} {dept:<6} {nom_brut:<35} {suggestions_str}")

    print("-" * 110)
    print(f"\nTotal : {total} communes non résolues")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="Diagnostique les communes non résolues en affichant les proches voisins BDD."
    )
    parser.add_argument('--top', type=int, default=3, help="Nombre de suggestions par commune (défaut: 3)")
    parser.add_argument('--dept', type=str, default=None, help="Filtrer sur un département (ex: 14)")
    args = parser.parse_args()
    run(top=args.top, dept=args.dept)
