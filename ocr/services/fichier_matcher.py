import re
from pathlib import PurePath

from observations.models import FicheObservation


class FichierMatcher:
    @staticmethod
    def trouver_fiche_depuis_json(
        chemin_json: str,
    ) -> tuple[FicheObservation | None, dict[str, str]]:
        """
        Retourne (fiche, metadata_dict).

        - fiche : instance FicheObservation ou None
        - metadata_dict : dict exploitable par TranscriptionOCR
        """
        metadata = FichierMatcher._construire_metadata(chemin_json)
        nom_fichier_base = metadata["nom_fichier_base"]  # ex: "fiche 27FINAL_binarisation..."

        # Stratégie : Extraire la racine commune "fiche XXFINAL"
        # On suppose que le nom commence par "fiche XXFINAL" ou "fiche XX"

        # Regex pour capturer "fiche" + espaces + chiffres + optionnellement "FINAL"
        # et s'arrêter avant le premier underscore ou la fin
        match = re.match(r'^(fiche\s*\d+(?:FINAL)?)', nom_fichier_base, re.IGNORECASE)

        if match:
            racine = match.group(1)  # ex: "fiche 27FINAL"

            # On cherche une fiche dont l'image correspond exactement à cette racine + extension
            extensions = ['.jpg', '.jpeg', '.png']
            for ext in extensions:
                # 1. Match exact sur le nom de fichier (prioritaire)
                # On cherche dans le champ chemin_image si ça finit par "fiche 27FINAL.jpg"
                fiches = list(
                    FicheObservation.objects.filter(chemin_image__endswith=f"{racine}{ext}")[:2]
                )
                if len(fiches) == 1:
                    return fiches[0], metadata

                # 2. Si pas de match exact, match 'contains' (plus large)
                if not fiches:
                    fiches = list(
                        FicheObservation.objects.filter(chemin_image__icontains=f"{racine}{ext}")[
                            :2
                        ]
                    )
                    if len(fiches) == 1:
                        return fiches[0], metadata

        return None, metadata

    @staticmethod
    def _construire_metadata(chemin_json: str) -> dict[str, str]:
        (
            type_image,
            lot,
            traitement,
            modele_ocr,
            nom_fichier_base,
        ) = FichierMatcher._extraire_segments(chemin_json)

        # On garde .jpg par défaut pour le chemin 'attendu' théorique
        chemin_image_attendu = "/".join([type_image, lot, traitement, f"{nom_fichier_base}.jpg"])

        return {
            "type_image": type_image,
            "lot": lot,
            "traitement_image": traitement,
            "modele_ocr": modele_ocr,
            "nom_fichier_base": nom_fichier_base,
            "chemin_image_attendu": chemin_image_attendu,
        }

    @staticmethod
    def _extraire_segments(chemin_json: str) -> tuple[str, str, str, str, str]:
        if not isinstance(chemin_json, str):
            raise TypeError("chemin_json doit etre une chaine.")

        chemin = chemin_json.strip()
        if not chemin:
            raise ValueError("chemin_json est vide.")

        parts = PurePath(chemin).parts
        try:
            index = parts.index("transcription_results")
        except ValueError as exc:
            raise ValueError(
                "chemin_json invalide: segment 'transcription_results' introuvable."
            ) from exc

        segments = list(parts[index + 1 :])
        if len(segments) != 5:
            raise ValueError(
                "chemin_json invalide: structure attendue "
                "transcription_results/{type_image}/{lot}/{traitement}/"
                "{modele_ocr}/{nom_base}_result.json."
            )

        type_image, lot, traitement, modele_ocr, nom_fichier = segments
        suffix = "_result.json"
        if not nom_fichier.endswith(suffix):
            raise ValueError(
                "chemin_json invalide: le fichier doit se terminer par '_result.json'."
            )

        nom_fichier_base = nom_fichier[: -len(suffix)]
        if not nom_fichier_base:
            raise ValueError("chemin_json invalide: nom de fichier base manquant.")

        return type_image, lot, traitement, modele_ocr, nom_fichier_base
