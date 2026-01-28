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
        chemin_image = metadata["chemin_image_attendu"]

        fiches = list(FicheObservation.objects.filter(chemin_image=chemin_image)[:2])
        fiche = fiches[0] if len(fiches) == 1 else None

        return fiche, metadata

    @staticmethod
    def _construire_metadata(chemin_json: str) -> dict[str, str]:
        (
            type_image,
            lot,
            traitement,
            modele_ocr,
            nom_fichier_base,
        ) = FichierMatcher._extraire_segments(chemin_json)

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
