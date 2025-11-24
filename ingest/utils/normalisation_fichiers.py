"""
Utilitaires pour la normalisation des noms de fichiers de scans.
"""

import re
from pathlib import Path
from typing import Literal, TypedDict


class FichierNormalise(TypedDict):
    """Structure d'un fichier normalisé."""

    numero: str
    type: Literal["recto", "verso"]
    chemin_original: str
    nom_normalise: str
    detecte: bool


def detecter_pattern_fichier(nom_fichier: str) -> tuple[str | None, str | None]:
    """
    Détecte le numéro de fiche et le type (recto/verso) depuis le nom de fichier.

    Patterns supportés :
    - xxx-R.jpeg / xxx-V.jpeg
    - xxx_recto.jpg / xxx_verso.jpg
    - xxx_page1.jpg / xxx_page2.jpg
    - 001_recto.jpg / 001_verso.jpg

    Args:
        nom_fichier: Nom du fichier (avec ou sans extension)

    Returns:
        Tuple (numero, type) où type est "recto" ou "verso"
        Retourne (None, None) si pattern non reconnu
    """
    nom_sans_ext = Path(nom_fichier).stem.lower()

    # Pattern 1 : xxx-R.jpeg / xxx-V.jpeg
    match = re.match(r"^(.+?)[-_]([rv])$", nom_sans_ext, re.IGNORECASE)
    if match:
        numero = match.group(1)
        lettre = match.group(2).lower()
        type_fiche = "recto" if lettre == "r" else "verso"
        return numero, type_fiche

    # Pattern 2 : xxx_recto.jpg / xxx_verso.jpg
    match = re.match(r"^(.+?)[-_](recto|verso)$", nom_sans_ext, re.IGNORECASE)
    if match:
        numero = match.group(1)
        type_fiche = match.group(2).lower()
        return numero, type_fiche

    # Pattern 3 : xxx_page1.jpg (page1=recto, page2=verso)
    match = re.match(r"^(.+?)[-_]page([12])$", nom_sans_ext, re.IGNORECASE)
    if match:
        numero = match.group(1)
        page = match.group(2)
        type_fiche = "recto" if page == "1" else "verso"
        return numero, type_fiche

    # Pattern 4 : Numéro seul (on essaie de deviner avec le contexte)
    match = re.match(r"^(\d+)$", nom_sans_ext)
    if match:
        # Retourne le numéro mais pas de type déterminé
        return match.group(1), None

    return None, None


def normaliser_nom_fichier(
    nom_fichier: str, numero: str | None = None, type_fiche: str | None = None
) -> str:
    """
    Génère un nom de fichier normalisé.

    Format : {numero}_recto.jpg ou {numero}_verso.jpg

    Args:
        nom_fichier: Nom original du fichier
        numero: Numéro de fiche (détecté automatiquement si None)
        type_fiche: "recto" ou "verso" (détecté automatiquement si None)

    Returns:
        Nom de fichier normalisé (ex: "001_recto.jpg")

    Raises:
        ValueError: Si le pattern n'est pas reconnu
    """
    extension = Path(nom_fichier).suffix.lower()
    if not extension:
        extension = ".jpg"

    # Si numéro et type non fournis, les détecter
    if numero is None or type_fiche is None:
        num_detecte, type_detecte = detecter_pattern_fichier(nom_fichier)

        if numero is None:
            numero = num_detecte
        if type_fiche is None:
            type_fiche = type_detecte

        if numero is None or type_fiche is None:
            raise ValueError(
                f"Impossible de détecter le pattern du fichier '{nom_fichier}'. "
                f"Patterns supportés : xxx-R.jpeg, xxx_recto.jpg, xxx_page1.jpg"
            )

    # Normaliser le numéro (padding avec zéros si nécessaire)
    if numero.isdigit():
        numero = numero.zfill(3)  # Padding à 3 chiffres minimum

    return f"{numero}_{type_fiche}{extension}"


def normaliser_paire_fichiers(
    fichier_1: str, fichier_2: str
) -> tuple[FichierNormalise, FichierNormalise]:
    """
    Normalise une paire de fichiers recto/verso.

    Args:
        fichier_1: Chemin du premier fichier
        fichier_2: Chemin du second fichier

    Returns:
        Tuple de deux dictionnaires FichierNormalise (recto, verso)

    Raises:
        ValueError: Si les fichiers ne forment pas une paire valide
    """
    path1 = Path(fichier_1)
    path2 = Path(fichier_2)

    num1, type1 = detecter_pattern_fichier(path1.name)
    num2, type2 = detecter_pattern_fichier(path2.name)

    # Vérifier que les deux fichiers ont le même numéro
    if num1 != num2:
        raise ValueError(
            f"Les fichiers ne semblent pas former une paire : "
            f"numéros différents ({num1} vs {num2})"
        )

    # Vérifier qu'on a bien un recto et un verso
    if type1 == type2:
        raise ValueError(
            f"Les fichiers ne semblent pas former une paire : "
            f"même type détecté ({type1})"
        )

    if type1 is None or type2 is None:
        raise ValueError(
            f"Impossible de détecter le type (recto/verso) pour les fichiers"
        )

    # Créer les dictionnaires normalisés
    fichiers_normalises = []
    for path, num, type_fiche in [(path1, num1, type1), (path2, num2, type2)]:
        nom_normalise = normaliser_nom_fichier(path.name, num, type_fiche)
        fichiers_normalises.append(
            FichierNormalise(
                numero=num,
                type=type_fiche,  # type: ignore
                chemin_original=str(path),
                nom_normalise=nom_normalise,
                detecte=True,
            )
        )

    # Trier pour avoir recto puis verso
    fichiers_normalises.sort(key=lambda x: 0 if x["type"] == "recto" else 1)

    return fichiers_normalises[0], fichiers_normalises[1]


def detecter_paires_dans_dossier(fichiers: list[str]) -> list[tuple[str, str]]:
    """
    Détecte automatiquement les paires recto/verso dans une liste de fichiers.

    Args:
        fichiers: Liste de chemins de fichiers

    Returns:
        Liste de tuples (recto, verso) avec les chemins originaux
    """
    # Grouper par numéro
    fichiers_par_numero: dict[str, dict[str, str]] = {}

    for fichier in fichiers:
        numero, type_fiche = detecter_pattern_fichier(Path(fichier).name)

        if numero is None or type_fiche is None:
            # Ignorer les fichiers non reconnus
            continue

        if numero not in fichiers_par_numero:
            fichiers_par_numero[numero] = {}

        fichiers_par_numero[numero][type_fiche] = fichier

    # Créer les paires
    paires = []
    for numero, fichiers_dict in sorted(fichiers_par_numero.items()):
        if "recto" in fichiers_dict and "verso" in fichiers_dict:
            paires.append((fichiers_dict["recto"], fichiers_dict["verso"]))

    return paires


# Exemples d'utilisation
if __name__ == "__main__":
    # Test des différents patterns
    test_fichiers = [
        "001-R.jpeg",
        "001-V.jpeg",
        "042_recto.jpg",
        "042_verso.jpg",
        "123_page1.jpg",
        "123_page2.jpg",
    ]

    print("Test de détection de patterns :")
    for fichier in test_fichiers:
        numero, type_fiche = detecter_pattern_fichier(fichier)
        nom_normalise = normaliser_nom_fichier(fichier)
        print(f"{fichier:20} → N°{numero}, {type_fiche:6} → {nom_normalise}")

    print("\nTest de détection de paires :")
    paires = detecter_paires_dans_dossier(test_fichiers)
    for i, (recto, verso) in enumerate(paires, 1):
        print(f"Paire {i}: {Path(recto).name} + {Path(verso).name}")
