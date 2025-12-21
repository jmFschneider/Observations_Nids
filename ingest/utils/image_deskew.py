"""
Utilitaires pour la détection et correction automatique de l'inclinaison des images.

Utilise plusieurs algorithmes de deskewing pour garantir la robustesse :
1. Bibliothèque deskew (méthode par projection)
2. Détection de contours + minAreaRect (OpenCV)
3. Projection horizontale avec variance maximale

L'algorithme le plus fiable est sélectionné automatiquement.
"""

import logging
from pathlib import Path

import cv2
import numpy as np

logger = logging.getLogger(__name__)

# Tenter d'importer la bibliothèque deskew (optionnelle mais recommandée)
try:
    from deskew import determine_skew

    HAS_DESKEW = True
except ImportError:
    HAS_DESKEW = False
    logger.warning(
        "Bibliothèque 'deskew' non installée. Utilisez 'pip install deskew' pour de meilleurs résultats."
    )


def auto_deskew_image(image: np.ndarray, max_angle: float = 45.0) -> tuple[np.ndarray, float, str]:
    """
    Détecte et corrige automatiquement l'inclinaison d'une image.

    Essaie plusieurs méthodes dans l'ordre :
    1. Bibliothèque deskew (projection)
    2. Contours + minAreaRect
    3. Projection horizontale

    Args:
        image: Image en couleur (BGR) ou niveaux de gris
        max_angle: Angle maximum acceptable (en degrés)

    Returns:
        Tuple (image_corrigee, angle_detecte, methode_utilisee)
        Si aucune méthode ne fonctionne, retourne (image_originale, 0.0, "none")
    """
    if image is None or image.size == 0:
        raise ValueError("Image invalide ou vide")

    # Convertir en niveaux de gris si nécessaire
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image.copy()

    # Méthode 1 : Bibliothèque deskew (la plus fiable)
    if HAS_DESKEW:
        try:
            angle = determine_skew(gray)
            if angle is not None and abs(angle) < max_angle:
                rotated = rotate_image(image, angle)
                logger.info(f"Deskew réussi (bibliothèque): {angle:.2f}°")
                return rotated, angle, "deskew_library"
        except Exception as e:
            logger.debug(f"Échec méthode deskew: {e}")

    # Méthode 2 : Contours + minAreaRect
    try:
        angle = detect_skew_contours(gray)
        if angle is not None and abs(angle) < max_angle:
            rotated = rotate_image(image, angle)
            logger.info(f"Deskew réussi (contours): {angle:.2f}°")
            return rotated, angle, "contours_minarearect"
    except Exception as e:
        logger.debug(f"Échec méthode contours: {e}")

    # Méthode 3 : Projection horizontale
    try:
        angle = detect_skew_projection(gray)
        if angle is not None and abs(angle) < max_angle:
            rotated = rotate_image(image, angle)
            logger.info(f"Deskew réussi (projection): {angle:.2f}°")
            return rotated, angle, "horizontal_projection"
    except Exception as e:
        logger.debug(f"Échec méthode projection: {e}")

    # Aucune méthode n'a fonctionné
    logger.warning("Aucune méthode de deskew n'a réussi, image retournée sans modification")
    return image, 0.0, "none"


def detect_skew_contours(gray: np.ndarray) -> float | None:
    """
    Détecte l'inclinaison via les contours et minAreaRect.

    Cette méthode est efficace pour les images avec des bordures
    ou des blocs de texte bien définis.

    Args:
        gray: Image en niveaux de gris

    Returns:
        Angle de correction en degrés, ou None si échec
    """
    # Prétraitement : flou + seuillage
    blur = cv2.GaussianBlur(gray, (9, 9), 0)
    thresh = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]

    # Opérations morphologiques pour fusionner les régions de texte
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (30, 5))
    dilate = cv2.dilate(thresh, kernel, iterations=2)

    # Trouver les contours
    contours, _ = cv2.findContours(dilate, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    if not contours:
        return None

    # Prendre le plus grand contour (supposé être le document)
    contour = max(contours, key=cv2.contourArea)

    # Rectangle englobant minimal
    rect = cv2.minAreaRect(contour)
    angle = rect[-1]

    # Normaliser l'angle
    # OpenCV retourne un angle entre -90 et 0
    if angle < -45:
        angle = 90 + angle
    elif angle > 45:
        angle = angle - 90

    return -angle  # Inverser pour correction


def detect_skew_projection(
    gray: np.ndarray, angle_range: tuple[float, float] = (-10, 10), step: float = 0.5
) -> float | None:
    """
    Détecte l'inclinaison par projection horizontale et maximisation de variance.

    Cette méthode teste différents angles et sélectionne celui qui maximise
    la variance de la projection horizontale (lignes de texte bien séparées).

    Args:
        gray: Image en niveaux de gris
        angle_range: Tuple (min_angle, max_angle) à tester
        step: Pas d'incrémentation des angles

    Returns:
        Angle de correction en degrés, ou None si échec
    """
    # Binarisation
    _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

    angles = np.arange(angle_range[0], angle_range[1], step)
    max_variance = 0
    best_angle = 0

    for angle in angles:
        # Rotation temporaire
        rotated = rotate_image(binary, angle)

        # Projection horizontale (somme par ligne)
        projection = np.sum(rotated, axis=1)

        # Calculer la variance
        variance = np.var(projection)

        if variance > max_variance:
            max_variance = variance
            best_angle = angle

    # Vérifier que la variance trouvée est significative
    if max_variance == 0:
        return None

    return best_angle


def rotate_image(
    image: np.ndarray, angle: float, border_value: tuple[int, int, int] = (255, 255, 255)
) -> np.ndarray:
    """
    Effectue une rotation d'image avec ajustement automatique de taille.

    Args:
        image: Image à faire pivoter (BGR ou grayscale)
        angle: Angle de rotation en degrés (positif = sens horaire)
        border_value: Couleur de remplissage des zones vides (BGR)

    Returns:
        Image pivotée avec dimensions ajustées
    """
    (h, w) = image.shape[:2]
    center = (w // 2, h // 2)

    # Matrice de rotation
    rotation_matrix = cv2.getRotationMatrix2D(center, angle, 1.0)

    # Calculer les nouvelles dimensions pour éviter de couper l'image
    cos = np.abs(rotation_matrix[0, 0])
    sin = np.abs(rotation_matrix[0, 1])

    new_w = int((h * sin) + (w * cos))
    new_h = int((h * cos) + (w * sin))

    # Ajuster la matrice de translation pour centrer l'image
    rotation_matrix[0, 2] += (new_w / 2) - center[0]
    rotation_matrix[1, 2] += (new_h / 2) - center[1]

    # Rotation avec fond blanc (ou couleur spécifiée)
    rotated = cv2.warpAffine(
        image,
        rotation_matrix,
        (new_w, new_h),
        flags=cv2.INTER_CUBIC,
        borderMode=cv2.BORDER_CONSTANT,
        borderValue=border_value,
    )

    return rotated


def batch_deskew_images(
    input_paths: list[Path], output_dir: Path | None = None, overwrite: bool = False
) -> list[dict]:
    """
    Traite plusieurs images en batch pour le deskewing.

    Args:
        input_paths: Liste des chemins d'images à traiter
        output_dir: Dossier de sortie (si None, remplace in-place)
        overwrite: Si True, écrase les fichiers existants

    Returns:
        Liste de dictionnaires contenant les résultats :
        [
            {
                "input": Path,
                "output": Path,
                "angle": float,
                "method": str,
                "success": bool,
                "error": Optional[str]
            },
            ...
        ]
    """
    results = []

    for input_path in input_paths:
        result = {
            "input": input_path,
            "output": None,
            "angle": 0.0,
            "method": "none",
            "success": False,
            "error": None,
        }

        try:
            # Charger l'image
            image = cv2.imread(str(input_path))
            if image is None:
                result["error"] = "Impossible de lire l'image"
                results.append(result)
                continue

            # Deskew
            deskewed, angle, method = auto_deskew_image(image)

            # Déterminer le chemin de sortie
            output_path = output_dir / input_path.name if output_dir else input_path

            # Vérifier si le fichier existe déjà
            if output_path.exists() and not overwrite:
                result["error"] = "Fichier de sortie existe déjà (overwrite=False)"
                results.append(result)
                continue

            # Sauvegarder
            cv2.imwrite(str(output_path), deskewed, [cv2.IMWRITE_JPEG_QUALITY, 95])

            result["output"] = output_path
            result["angle"] = angle
            result["method"] = method
            result["success"] = True

        except Exception as e:
            result["error"] = str(e)
            logger.error(f"Erreur lors du traitement de {input_path}: {e}")

        results.append(result)

    return results


# Exemple d'utilisation
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python image_deskew.py <image_path>")
        sys.exit(1)

    image_path = sys.argv[1]
    image = cv2.imread(image_path)

    if image is None:
        print(f"Erreur: Impossible de charger l'image {image_path}")
        sys.exit(1)

    deskewed, angle, method = auto_deskew_image(image)
    print(f"Angle détecté: {angle:.2f}° (méthode: {method})")

    output_path = str(Path(image_path).with_stem(Path(image_path).stem + "_deskewed"))
    cv2.imwrite(output_path, deskewed)
    print(f"Image corrigée sauvegardée: {output_path}")
