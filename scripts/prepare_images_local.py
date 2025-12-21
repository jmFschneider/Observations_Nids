#!/usr/bin/env python
"""
Script de préparation locale d'images pour OCR.

Ce script traite des scans recto/verso sur le PC local (puissant)
et génère des images fusionnées optimisées + métadonnées JSON
pour import ultérieur dans Django (sur Raspberry Pi).

Usage:
    python scripts/prepare_images_local.py --input C:\\scans_bruts --output C:\\prepared

Options:
    --input DIR         Dossier contenant les scans bruts (recto/verso)
    --output DIR        Dossier de sortie (créé automatiquement)
    --crop 55|100       Recadrage du verso en % (défaut: 100)
    --operateur NAME    Nom de l'opérateur (défaut: Utilisateur)
    --skip-deskew       Désactiver le redressement automatique
    --skip-optimize     Désactiver les optimisations OCR
    --preview           Mode aperçu (n'enregistre pas, affiche seulement)
    --verbose           Logs détaillés

Exemple:
    python scripts/prepare_images_local.py \\
        --input test_scans \\
        --output prepared \\
        --crop 100 \\
        --operateur JeanMarc
"""

import argparse
import hashlib
import json
import logging
import socket
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

import cv2
import numpy as np
from tqdm import tqdm

# Imports locaux
sys.path.insert(0, str(Path(__file__).parent.parent))
from ingest.utils.image_deskew import auto_deskew_image
from ingest.utils.image_processing import assess_image_quality, optimize_for_ocr
from ingest.utils.normalisation_fichiers import detecter_paires_dans_dossier

# Configuration du logging
logger = logging.getLogger(__name__)


def main():
    """Point d'entrée principal du script."""
    parser = argparse.ArgumentParser(
        description='Préparation locale d\'images pour OCR',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    parser.add_argument('--input', required=True, help='Dossier contenant les scans bruts')
    parser.add_argument('--output', required=True, help='Dossier de sortie')
    parser.add_argument(
        '--crop',
        type=int,
        default=100,
        choices=[55, 100],
        help='Crop verso en %% (défaut: 100)',
    )
    parser.add_argument(
        '--operateur', default='Utilisateur', help='Nom de l\'opérateur'
    )
    parser.add_argument(
        '--skip-deskew',
        action='store_true',
        help='Désactiver le redressement automatique',
    )
    parser.add_argument(
        '--skip-optimize',
        action='store_true',
        help='Désactiver les optimisations OCR',
    )
    parser.add_argument(
        '--preview', action='store_true', help='Mode aperçu (n\'enregistre pas)'
    )
    parser.add_argument(
        '--verbose', action='store_true', help='Logs détaillés'
    )

    args = parser.parse_args()

    # Configuration du logging
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%H:%M:%S',
    )

    # Validation des chemins
    input_dir = Path(args.input)
    if not input_dir.exists():
        logger.error(f"Dossier d'entrée introuvable: {input_dir}")
        sys.exit(1)

    output_dir = Path(args.output)
    if not args.preview:
        images_dir = output_dir / 'images'
        images_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Dossier de sortie créé: {output_dir}")

    # Détecter les paires recto/verso
    logger.info("Détection des paires recto/verso...")
    fichiers = [f for f in input_dir.rglob('*') if f.is_file() and f.suffix.lower() in ['.jpg', '.jpeg', '.png']]
    paires = detecter_paires_dans_dossier([str(f) for f in fichiers])

    if not paires:
        logger.error("Aucune paire recto/verso détectée!")
        logger.error("Vérifiez que les fichiers suivent un pattern supporté:")
        logger.error("  - xxx-R.jpeg / xxx-V.jpeg")
        logger.error("  - xxx_recto.jpg / xxx_verso.jpg")
        logger.error("  - xxx_page1.jpg / xxx_page2.jpg")
        sys.exit(1)

    logger.info(f"✓ {len(paires)} paire(s) détectée(s)")

    # Préparer la structure de métadonnées
    metadata = {
        "version": "1.0",
        "date_traitement": datetime.now().isoformat(),
        "operateur": args.operateur,
        "machine": {
            "hostname": socket.gethostname(),
            "opencv_version": cv2.__version__,
            "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        },
        "configuration": {
            "crop_verso_default": f"{args.crop}%",
            "auto_deskew": not args.skip_deskew,
            "optimisations_ocr": not args.skip_optimize,
        },
        "fiches": [],
        "statistiques": {},
    }

    # Traiter chaque paire
    errors = []
    warnings = []
    duree_totale = 0

    for i, (recto_path, verso_path) in enumerate(
        tqdm(paires, desc="Traitement des fiches", unit="fiche"), start=1
    ):
        try:
            fiche_data = traiter_paire(
                recto_path=recto_path,
                verso_path=verso_path,
                output_dir=images_dir if not args.preview else None,
                crop_percent=args.crop,
                apply_deskew=not args.skip_deskew,
                apply_optimize=not args.skip_optimize,
            )

            duree_totale += fiche_data.get('duree_traitement_s', 0)
            metadata["fiches"].append(fiche_data)

            # Collecter les warnings
            if fiche_data.get('qualite', {}).get('warnings'):
                warnings.extend(fiche_data['qualite']['warnings'])

        except Exception as e:
            logger.error(f"Erreur fiche {i}: {e}")
            errors.append({"fiche": i, "erreur": str(e)})

    # Statistiques finales
    metadata["statistiques"] = {
        "total_fiches": len(paires),
        "fiches_reussies": len(metadata["fiches"]),
        "fiches_erreurs": len(errors),
        "duree_totale_s": round(duree_totale, 2),
        "duree_moyenne_par_fiche_s": round(duree_totale / len(paires), 2) if len(paires) > 0 else 0,
        "erreurs": errors,
        "warnings_total": len(warnings),
    }

    # Sauvegarder le JSON
    if not args.preview:
        json_path = output_dir / 'metadata.json'
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)

        logger.info(f"\n{'='*60}")
        logger.info(f"✓ Traitement terminé !")
        logger.info(f"  - Fiches traitées: {metadata['statistiques']['fiches_reussies']}/{metadata['statistiques']['total_fiches']}")
        logger.info(f"  - Durée totale: {metadata['statistiques']['duree_totale_s']:.1f}s")
        logger.info(f"  - Durée moyenne: {metadata['statistiques']['duree_moyenne_par_fiche_s']:.1f}s/fiche")
        logger.info(f"  - Métadonnées: {json_path}")
        logger.info(f"  - Images: {images_dir}")
        logger.info(f"{'='*60}\n")

        if errors:
            logger.warning(f"⚠ {len(errors)} erreur(s) détectée(s)")
        if warnings:
            logger.warning(f"⚠ {len(warnings)} avertissement(s) qualité")
    else:
        logger.info("\nMode aperçu : aucun fichier enregistré")


def traiter_paire(
    recto_path: str,
    verso_path: str,
    output_dir: Optional[Path],
    crop_percent: int,
    apply_deskew: bool,
    apply_optimize: bool,
) -> dict:
    """
    Traite une paire recto/verso et retourne les métadonnées.

    Args:
        recto_path: Chemin du fichier recto
        verso_path: Chemin du fichier verso
        output_dir: Dossier de sortie (None en mode preview)
        crop_percent: Pourcentage de recadrage du verso
        apply_deskew: Activer le deskewing
        apply_optimize: Activer les optimisations OCR

    Returns:
        Dictionnaire de métadonnées pour cette fiche
    """
    import time

    start_time = time.time()

    # Extraire le numéro de fiche
    numero = Path(recto_path).stem.split('-')[0].split('_')[0]

    # Charger les images
    recto = cv2.imread(str(recto_path))
    verso = cv2.imread(str(verso_path))

    if recto is None:
        raise ValueError(f"Impossible de lire le recto: {recto_path}")
    if verso is None:
        raise ValueError(f"Impossible de lire le verso: {verso_path}")

    # Métadonnées de base
    metadata = {
        "numero": numero,
        "fichiers_source": {
            "recto": {
                "chemin_absolu": str(Path(recto_path).absolute()),
                "nom_original": Path(recto_path).name,
                "taille_ko": Path(recto_path).stat().st_size // 1024,
                "dimensions": [recto.shape[1], recto.shape[0]],
                "hash_sha256": compute_file_hash(recto_path),
            },
            "verso": {
                "chemin_absolu": str(Path(verso_path).absolute()),
                "nom_original": Path(verso_path).name,
                "taille_ko": Path(verso_path).stat().st_size // 1024,
                "dimensions": [verso.shape[1], verso.shape[0]],
                "hash_sha256": compute_file_hash(verso_path),
            },
        },
        "operations": {},
        "qualite": {},
        "timestamp": datetime.now().isoformat(),
    }

    # Deskewing
    if apply_deskew:
        recto_deskewed, angle_recto, method_recto = auto_deskew_image(recto)
        verso_deskewed, angle_verso, method_verso = auto_deskew_image(verso)

        metadata["operations"]["deskew"] = {
            "recto": {
                "angle_detecte": round(float(angle_recto), 2),
                "methode": method_recto,
            },
            "verso": {
                "angle_detecte": round(float(angle_verso), 2),
                "methode": method_verso,
            },
        }

        logger.debug(
            f"Fiche {numero}: deskew recto={angle_recto:.1f}° ({method_recto}), "
            f"verso={angle_verso:.1f}° ({method_verso})"
        )
    else:
        recto_deskewed = recto
        verso_deskewed = verso
        metadata["operations"]["deskew"] = {"actif": False}

    # Fusion recto/verso
    fused = fusionner_images(recto_deskewed, verso_deskewed, crop_percent)

    metadata["operations"]["fusion"] = {
        "crop_verso_width": f"{crop_percent}%",
        "crop_verso_pixels": int(verso_deskewed.shape[1] * crop_percent / 100),
    }

    # Optimisations OCR
    if apply_optimize:
        optimized, operations_applied = optimize_for_ocr(fused)

        metadata["operations"]["optimisations"] = [
            {"nom": op} for op in operations_applied
        ]

        logger.debug(f"Fiche {numero}: optimisations={', '.join(operations_applied)}")
    else:
        optimized = fused
        metadata["operations"]["optimisations"] = []

    # Évaluation qualité
    quality = assess_image_quality(optimized)
    metadata["qualite"] = quality

    # Sauvegarder (si pas en mode preview)
    if output_dir:
        output_filename = f"{numero}_prepared.jpg"
        output_path = output_dir / output_filename

        cv2.imwrite(str(output_path), optimized, [cv2.IMWRITE_JPEG_QUALITY, 95])

        metadata["fichier_prepare"] = {
            "chemin_relatif": f"images/{output_filename}",
            "nom": output_filename,
            "taille_ko": output_path.stat().st_size // 1024,
            "dimensions": [optimized.shape[1], optimized.shape[0]],
            "hash_sha256": compute_file_hash(output_path),
        }

    # Durée de traitement
    metadata["duree_traitement_s"] = round(time.time() - start_time, 2)

    return metadata


def fusionner_images(
    recto: np.ndarray, verso: np.ndarray, crop_percent: int
) -> np.ndarray:
    """
    Fusionne deux images recto/verso en une seule image verticale.

    Args:
        recto: Image du recto
        verso: Image du verso
        crop_percent: Pourcentage du verso à conserver (55 ou 100)

    Returns:
        Image fusionnée (recto en haut, verso en bas)
    """
    # Calculer la largeur de crop du verso
    crop_width = int(verso.shape[1] * crop_percent / 100)

    # Recadrer le verso
    verso_cropped = verso[:, :crop_width]

    # Créer le canvas final
    # Largeur = max(recto, verso_cropped)
    # Hauteur = recto + verso_cropped
    final_width = max(recto.shape[1], verso_cropped.shape[1])
    final_height = recto.shape[0] + verso_cropped.shape[0]

    # Canvas blanc
    fused = np.full((final_height, final_width, 3), 255, dtype=np.uint8)

    # Coller le recto en haut
    fused[: recto.shape[0], : recto.shape[1]] = recto

    # Coller le verso en bas
    offset_y = recto.shape[0]
    fused[
        offset_y : offset_y + verso_cropped.shape[0], : verso_cropped.shape[1]
    ] = verso_cropped

    return fused


def compute_file_hash(file_path: Path | str) -> str:
    """Calcule le hash SHA256 d'un fichier."""
    sha256 = hashlib.sha256()
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            sha256.update(chunk)
    return sha256.hexdigest()


if __name__ == '__main__':
    main()
