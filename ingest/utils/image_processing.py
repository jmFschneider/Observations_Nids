"""
Utilitaires pour l'optimisation d'images destinées à l'OCR.

Ce module contient des fonctions de prétraitement qui améliorent
la qualité de reconnaissance du texte par Tesseract :
- Amélioration du contraste (CLAHE)
- Débruitage
- Binarisation adaptative
- Sharpening (netteté)
"""

import logging
from typing import Optional, Tuple

import cv2
import numpy as np

logger = logging.getLogger(__name__)


def optimize_for_ocr(
    image: np.ndarray,
    apply_clahe: bool = True,
    apply_denoise: bool = True,
    apply_sharpen: bool = True,
    apply_binarize: bool = False,
) -> Tuple[np.ndarray, list[str]]:
    """
    Applique une série d'optimisations pour améliorer la reconnaissance OCR.

    Args:
        image: Image en couleur (BGR) ou niveaux de gris
        apply_clahe: Activer l'amélioration du contraste adaptatif
        apply_denoise: Activer le débruitage
        apply_sharpen: Activer le renforcement de la netteté
        apply_binarize: Activer la binarisation (noir et blanc strict)

    Returns:
        Tuple (image_optimisee, liste_operations_appliquees)
    """
    if image is None or image.size == 0:
        raise ValueError("Image invalide ou vide")

    operations = []
    result = image.copy()

    # Convertir en BGR si grayscale
    if len(result.shape) == 2:
        result = cv2.cvtColor(result, cv2.COLOR_GRAY2BGR)

    # 1. CLAHE (Contrast Limited Adaptive Histogram Equalization)
    if apply_clahe:
        result = apply_clahe_enhancement(result)
        operations.append("clahe")
        logger.debug("CLAHE appliqué")

    # 2. Débruitage
    if apply_denoise:
        result = apply_fastNlMeans_denoising(result)
        operations.append("denoise")
        logger.debug("Débruitage appliqué")

    # 3. Sharpening (netteté)
    if apply_sharpen:
        result = apply_unsharp_mask(result)
        operations.append("sharpen")
        logger.debug("Sharpening appliqué")

    # 4. Binarisation (optionnel, pour documents très dégradés)
    if apply_binarize:
        result = apply_adaptive_threshold(result)
        operations.append("binarize")
        logger.debug("Binarisation appliquée")

    return result, operations


def apply_clahe_enhancement(
    image: np.ndarray, clip_limit: float = 2.0, tile_grid_size: Tuple[int, int] = (8, 8)
) -> np.ndarray:
    """
    Applique CLAHE pour améliorer le contraste de manière adaptative.

    CLAHE améliore le contraste localement, ce qui est idéal pour
    les documents avec un éclairage non uniforme.

    Args:
        image: Image BGR
        clip_limit: Limite de contraste (2.0 = bon équilibre)
        tile_grid_size: Taille des tuiles pour l'adaptation locale

    Returns:
        Image avec contraste amélioré
    """
    # Convertir en LAB (meilleur pour le contraste)
    lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)

    # Séparer les canaux
    l, a, b = cv2.split(lab)

    # Appliquer CLAHE sur le canal L (luminosité)
    clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=tile_grid_size)
    l_clahe = clahe.apply(l)

    # Recombiner et reconvertir en BGR
    lab_clahe = cv2.merge([l_clahe, a, b])
    result = cv2.cvtColor(lab_clahe, cv2.COLOR_LAB2BGR)

    return result


def apply_fastNlMeans_denoising(
    image: np.ndarray, h: int = 10, h_color: int = 10, template_window_size: int = 7, search_window_size: int = 21
) -> np.ndarray:
    """
    Applique un débruitage non local pour réduire le bruit tout en préservant les détails.

    Cette méthode est plus lente mais plus efficace que le flou gaussien.

    Args:
        image: Image BGR
        h: Force du filtrage pour luminosité (10 = bon équilibre)
        h_color: Force du filtrage pour couleur
        template_window_size: Taille de la fenêtre de template (impair)
        search_window_size: Taille de la zone de recherche (impair)

    Returns:
        Image débruitée
    """
    if len(image.shape) == 3:
        # Image en couleur
        denoised = cv2.fastNlMeansDenoisingColored(
            image,
            None,
            h=h,
            hColor=h_color,
            templateWindowSize=template_window_size,
            searchWindowSize=search_window_size,
        )
    else:
        # Image en niveaux de gris
        denoised = cv2.fastNlMeansDenoising(
            image,
            None,
            h=h,
            templateWindowSize=template_window_size,
            searchWindowSize=search_window_size,
        )

    return denoised


def apply_unsharp_mask(
    image: np.ndarray, sigma: float = 1.0, amount: float = 1.5, threshold: int = 0
) -> np.ndarray:
    """
    Applique un masque flou inversé (unsharp mask) pour améliorer la netteté.

    Cette technique soustrait une version floue de l'image pour renforcer
    les contours et le texte.

    Args:
        image: Image BGR ou grayscale
        sigma: Écart-type du flou gaussien
        amount: Force du sharpening (1.0-2.0 recommandé)
        threshold: Seuil en dessous duquel le sharpening n'est pas appliqué

    Returns:
        Image avec netteté améliorée
    """
    # Créer une version floue
    blurred = cv2.GaussianBlur(image, (0, 0), sigma)

    # Calculer l'unsharp mask
    sharpened = cv2.addWeighted(image, 1.0 + amount, blurred, -amount, 0)

    # Appliquer le seuil si nécessaire
    if threshold > 0:
        low_contrast_mask = np.absolute(image - blurred) < threshold
        np.copyto(sharpened, image, where=low_contrast_mask)

    return sharpened


def apply_adaptive_threshold(
    image: np.ndarray, block_size: int = 11, C: int = 2
) -> np.ndarray:
    """
    Applique une binarisation adaptative pour convertir en noir et blanc.

    Utile pour les documents très dégradés ou avec un fond non uniforme.

    Args:
        image: Image BGR ou grayscale
        block_size: Taille de la zone de voisinage (impair, ex: 11, 15, 21)
        C: Constante soustraite de la moyenne (ajuste le seuil)

    Returns:
        Image binarisée (noir et blanc)
    """
    # Convertir en niveaux de gris si nécessaire
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image.copy()

    # Binarisation adaptative (Gaussian)
    binary = cv2.adaptiveThreshold(
        gray,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        block_size,
        C,
    )

    # Reconvertir en BGR pour uniformité
    result = cv2.cvtColor(binary, cv2.COLOR_GRAY2BGR)

    return result


def resize_for_ocr(
    image: np.ndarray, target_dpi: int = 300, current_dpi: Optional[int] = None
) -> np.ndarray:
    """
    Redimensionne l'image pour atteindre une résolution optimale pour l'OCR.

    Tesseract fonctionne mieux avec des images à 300 DPI.

    Args:
        image: Image à redimensionner
        target_dpi: DPI cible (300 recommandé)
        current_dpi: DPI actuel (si None, on suppose 72 DPI)

    Returns:
        Image redimensionnée
    """
    if current_dpi is None:
        current_dpi = 72  # DPI par défaut pour les écrans

    if current_dpi == target_dpi:
        return image

    # Calculer le facteur d'échelle
    scale_factor = target_dpi / current_dpi

    # Redimensionner
    new_width = int(image.shape[1] * scale_factor)
    new_height = int(image.shape[0] * scale_factor)

    # Utiliser INTER_CUBIC pour upscaling, INTER_AREA pour downscaling
    interpolation = cv2.INTER_CUBIC if scale_factor > 1 else cv2.INTER_AREA

    resized = cv2.resize(image, (new_width, new_height), interpolation=interpolation)

    logger.debug(f"Redimensionnement: {current_dpi} DPI → {target_dpi} DPI (facteur: {scale_factor:.2f}x)")

    return resized


def remove_borders(
    image: np.ndarray, threshold: int = 240, border_size: int = 10
) -> np.ndarray:
    """
    Supprime les bordures blanches/claires autour d'un document scanné.

    Args:
        image: Image BGR ou grayscale
        threshold: Seuil de luminosité pour détecter les zones blanches
        border_size: Taille minimale de bordure à conserver (pixels)

    Returns:
        Image sans bordures
    """
    # Convertir en niveaux de gris
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image.copy()

    # Binarisation inverse (texte en blanc)
    _, binary = cv2.threshold(gray, threshold, 255, cv2.THRESH_BINARY_INV)

    # Trouver les contours
    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    if not contours:
        return image

    # Rectangle englobant du contenu
    x, y, w, h = cv2.boundingRect(np.vstack(contours))

    # Ajouter une marge
    x = max(0, x - border_size)
    y = max(0, y - border_size)
    w = min(image.shape[1] - x, w + border_size * 2)
    h = min(image.shape[0] - y, h + border_size * 2)

    # Recadrer
    cropped = image[y : y + h, x : x + w]

    return cropped


def assess_image_quality(image: np.ndarray) -> dict:
    """
    Évalue la qualité d'une image pour l'OCR.

    Returns:
        Dictionnaire avec scores de qualité :
        {
            "sharpness": float (0-1),
            "contrast": float (0-1),
            "brightness": float (0-255),
            "warnings": list[str]
        }
    """
    # Convertir en niveaux de gris
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image.copy()

    warnings = []

    # 1. Netteté (variance du Laplacien)
    laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
    sharpness_score = min(1.0, laplacian_var / 500.0)  # Normalisé

    if sharpness_score < 0.3:
        warnings.append("Image floue détectée")

    # 2. Contraste (écart-type)
    contrast_score = min(1.0, gray.std() / 80.0)  # Normalisé

    if contrast_score < 0.4:
        warnings.append("Contraste faible")

    # 3. Luminosité moyenne
    brightness = gray.mean()

    if brightness < 50:
        warnings.append("Image trop sombre")
    elif brightness > 200:
        warnings.append("Image trop claire")

    return {
        "sharpness": round(sharpness_score, 2),
        "contrast": round(contrast_score, 2),
        "brightness": round(brightness, 1),
        "warnings": warnings,
    }


# Exemple d'utilisation
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python image_processing.py <image_path>")
        sys.exit(1)

    image_path = sys.argv[1]
    image = cv2.imread(image_path)

    if image is None:
        print(f"Erreur: Impossible de charger l'image {image_path}")
        sys.exit(1)

    # Évaluer la qualité
    quality = assess_image_quality(image)
    print(f"Qualité de l'image:")
    print(f"  - Netteté: {quality['sharpness']}")
    print(f"  - Contraste: {quality['contrast']}")
    print(f"  - Luminosité: {quality['brightness']}")
    if quality["warnings"]:
        print(f"  - Avertissements: {', '.join(quality['warnings'])}")

    # Optimiser
    optimized, operations = optimize_for_ocr(image)
    print(f"\nOpérations appliquées: {', '.join(operations)}")

    # Sauvegarder
    from pathlib import Path

    output_path = str(Path(image_path).with_stem(Path(image_path).stem + "_optimized"))
    cv2.imwrite(output_path, optimized)
    print(f"Image optimisée sauvegardée: {output_path}")
