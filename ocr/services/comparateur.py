import logging
from datetime import date, datetime
from difflib import SequenceMatcher
from typing import Any

from django.db.models.manager import BaseManager
from django.db.models.query import QuerySet

from observations.models import FicheObservation

logger = logging.getLogger(__name__)


class OCRComparator:
    def __init__(self, fiche: FicheObservation, json_ocr: dict[str, Any]) -> None:
        self._fiche = fiche
        self._json_ocr = json_ocr or {}
        self._bdd_data = self._extraire_bdd()

    def comparer(self) -> dict[str, Any]:
        """
        Lance la comparaison complète.
        Retourne un dictionnaire prêt à être stocké
        dans TranscriptionOCR (sans l’écrire en BDD).
        """
        ocr_data = self._json_ocr if isinstance(self._json_ocr, dict) else {}
        stats = self._initialiser_stats()

        details: dict[str, Any] = {
            "informations_generales": self._comparer_dict(
                "informations_generales",
                self._bdd_data.get("informations_generales", {}),
                ocr_data.get("informations_generales", {}),
                stats,
            ),
            "nid": self._comparer_dict(
                "nid",
                self._bdd_data.get("nid", {}),
                ocr_data.get("nid", {}),
                stats,
            ),
            "localisation": self._comparer_dict(
                "localisation",
                self._bdd_data.get("localisation", {}),
                ocr_data.get("localisation", {}),
                stats,
            ),
            "tableau_donnees": self._comparer_tableau(
                "tableau_donnees",
                self._bdd_data.get("tableau_donnees", []),
                ocr_data.get("tableau_donnees", []),
                stats,
            ),
            "resume": self._comparer_dict(
                "resume",
                self._bdd_data.get("resume", {}),
                ocr_data.get("resume", {}),
                stats,
            ),
            "remarque": self._comparer_remarque(
                self._bdd_data.get("remarque"),
                ocr_data.get("remarque"),
                stats,
            ),
        }

        # Calcul des scores
        tous_scores = stats["scores_texte"] + stats["scores_numerique"]
        score_global = sum(tous_scores) / len(tous_scores) if tous_scores else 0.0

        score_texte = (
            sum(stats["scores_texte"]) / len(stats["scores_texte"])
            if stats["scores_texte"]
            else None
        )

        score_numerique = (
            sum(stats["scores_numerique"]) / len(stats["scores_numerique"])
            if stats["scores_numerique"]
            else None
        )

        resultat = {
            "score_global": score_global * 100,  # Conversion en pourcentage ici
            "score_texte": score_texte * 100 if score_texte is not None else None,
            "score_numerique": score_numerique * 100 if score_numerique is not None else None,
            "nombre_champs_total": stats["nombre_champs_total"],
            "nombre_champs_corrects": stats["nombre_champs_corrects"],
            "nombre_erreurs_texte": stats["nombre_erreurs_texte"],
            "nombre_erreurs_nombres": stats["nombre_erreurs_nombres"],
            "nombre_erreurs_dates": stats["nombre_erreurs_dates"],
            "details_comparaison": details,
        }

        logger.info(
            "Comparaison OCR terminée pour fiche %s: Texte=%.1f%%, Num=%.1f%%",
            self._fiche.pk,
            resultat["score_texte"] or 0.0,
            resultat["score_numerique"] or 0.0,
        )

        return resultat

    def _initialiser_stats(self) -> dict[str, Any]:
        return {
            "scores_texte": [],
            "scores_numerique": [],
            "nombre_champs_total": 0,
            "nombre_champs_corrects": 0,
            "nombre_erreurs_texte": 0,
            "nombre_erreurs_nombres": 0,
            "nombre_erreurs_dates": 0,
        }

    def _extraire_bdd(self) -> dict[str, Any]:
        return {
            "informations_generales": {"fiche_id": self._fiche.pk},
            "nid": self._extraire_modele(self._fiche.nid),
            "localisation": self._extraire_modele(self._fiche.localisation),
            "tableau_donnees": [
                self._extraire_modele(observation) for observation in self._fiche.observations.all()
            ],
            "resume": self._extraire_modele(self._fiche.resume),
            "remarque": getattr(self._fiche, "remarques", None),
        }

    def _extraire_modele(self, objet: Any) -> dict[str, Any]:
        if objet is None or not hasattr(objet, "_meta"):
            return {}
        donnees: dict[str, Any] = {}
        for champ in objet._meta.fields:
            donnees[champ.name] = champ.value_from_object(objet)
        return donnees

    def _comparer_dict(
        self,
        prefixe: str,
        bdd_dict: dict[str, Any],
        ocr_dict: dict[str, Any],
        stats: dict[str, Any],
    ) -> list[dict[str, Any]]:
        champs = sorted(set(bdd_dict.keys()) | set(ocr_dict.keys()))
        resultats: list[dict[str, Any]] = []
        for champ in champs:
            valeur_bdd = bdd_dict.get(champ)
            valeur_ocr = ocr_dict.get(champ)
            type_champ = self._determiner_type(valeur_bdd, valeur_ocr)
            comparaison = self._comparer_champ(
                f"{prefixe}.{champ}",
                valeur_bdd,
                valeur_ocr,
                type_champ,
            )
            self._mettre_a_jour_stats(comparaison, stats)
            resultats.append(comparaison)
        return resultats

    def _comparer_tableau(
        self,
        prefixe: str,
        bdd_liste: list[Any],
        ocr_liste: list[Any],
        stats: dict[str, Any],
    ) -> list[dict[str, Any]]:
        bdd = bdd_liste if isinstance(bdd_liste, list) else []
        ocr = ocr_liste if isinstance(ocr_liste, list) else []
        taille = max(len(bdd), len(ocr))
        resultats: list[dict[str, Any]] = []
        for index in range(taille):
            bdd_ligne = bdd[index] if index < len(bdd) else {}
            ocr_ligne = ocr[index] if index < len(ocr) else {}
            bdd_dict = bdd_ligne if isinstance(bdd_ligne, dict) else {"valeur": bdd_ligne}
            ocr_dict = ocr_ligne if isinstance(ocr_ligne, dict) else {"valeur": ocr_ligne}
            champs = self._comparer_dict(
                f"{prefixe}[{index}]",
                bdd_dict,
                ocr_dict,
                stats,
            )
            resultats.append({"index": index, "champs": champs})
        return resultats

    def _comparer_remarque(
        self,
        valeur_bdd: Any,
        valeur_ocr: Any,
        stats: dict[str, Any],
    ) -> list[dict[str, Any]]:
        type_champ = self._determiner_type(valeur_bdd, valeur_ocr)
        comparaison = self._comparer_champ(
            "remarque",
            valeur_bdd,
            valeur_ocr,
            type_champ,
        )
        self._mettre_a_jour_stats(comparaison, stats)
        return [comparaison]

    def _normaliser_valeur(self, valeur: Any, type_champ: str) -> Any:
        if type_champ == "null" or valeur is None:
            return None
        normaliseurs = {
            "texte": self._normaliser_texte,
            "nombre": self._normaliser_nombre,
            "date": self._normaliser_date,
            "booléen": self._normaliser_booleen,
        }
        normaliseur = normaliseurs.get(type_champ)
        return normaliseur(valeur) if normaliseur else valeur

    def _normaliser_texte(self, valeur: Any) -> str | None:
        if valeur is None:
            return None
        texte = str(valeur)
        texte = " ".join(texte.strip().split())
        return texte.lower()

    def _normaliser_nombre(self, valeur: Any) -> int | float | None:
        if valeur is None:
            return None
        if isinstance(valeur, bool):
            return 1 if valeur else 0
        if isinstance(valeur, (int, float)):
            return valeur
        if isinstance(valeur, str):
            nettoye = valeur.strip().replace(",", ".")
            if not nettoye:
                return None
            for caster in (int, float):
                try:
                    return caster(nettoye)
                except ValueError:
                    continue
        return None

    def _normaliser_date(self, valeur: Any) -> tuple[int, int] | None:
        if valeur is None:
            return None
        if isinstance(valeur, datetime):
            valeur = valeur.date()
        if isinstance(valeur, date):
            return (valeur.day, valeur.month)
        if isinstance(valeur, dict):
            jour = valeur.get("jour")
            mois = valeur.get("mois")
            return self._normaliser_date_depuis_jour_mois(jour, mois)
        if isinstance(valeur, str):
            return self._normaliser_date_depuis_texte(valeur)
        return None

    def _normaliser_date_depuis_jour_mois(self, jour: Any, mois: Any) -> tuple[int, int] | None:
        jour_norm = self._normaliser_nombre(jour)
        mois_norm = self._normaliser_nombre(mois)
        if isinstance(jour_norm, int) and isinstance(mois_norm, int):
            return (jour_norm, mois_norm)
        return None

    def _normaliser_date_depuis_texte(self, valeur: str) -> tuple[int, int] | None:
        morceaux = [m for m in valeur.replace("-", "/").split("/") if m.strip()]
        if len(morceaux) >= 2:
            jour = self._normaliser_nombre(morceaux[0])
            mois = self._normaliser_nombre(morceaux[1])
            if isinstance(jour, int) and isinstance(mois, int):
                return (jour, mois)
        return None

    def _normaliser_booleen(self, valeur: Any) -> bool | None:
        if valeur is None:
            return None
        if isinstance(valeur, bool):
            return valeur
        if isinstance(valeur, int):
            return bool(valeur)
        if isinstance(valeur, str):
            texte = valeur.strip().lower()
            if texte in {"true", "vrai", "oui", "1"}:
                return True
            if texte in {"false", "faux", "non", "0"}:
                return False
        return None

    def _determiner_type(self, valeur_bdd: Any, valeur_ocr: Any) -> str:
        valeur = valeur_bdd if valeur_bdd is not None else valeur_ocr
        if valeur is None:
            return "null"
        if isinstance(valeur, bool):
            return "booléen"
        if isinstance(valeur, (int, float)):
            return "nombre"
        if isinstance(valeur, (date, datetime)):
            return "date"
        if isinstance(valeur, dict) and {"jour", "mois"}.issubset(valeur.keys()):
            return "date"
        return "texte"

    def _comparer_champ(
        self,
        nom: str,
        valeur_bdd: Any,
        valeur_ocr: Any,
        type_champ: str,
    ) -> dict[str, Any]:
        bdd_norm = self._normaliser_valeur(valeur_bdd, type_champ)
        ocr_norm = self._normaliser_valeur(valeur_ocr, type_champ)

        if type_champ == "texte":
            bdd_texte = bdd_norm or ""
            ocr_texte = ocr_norm or ""
            score = SequenceMatcher(None, bdd_texte, ocr_texte).ratio()
            match = bdd_texte == ocr_texte
        else:
            match = bdd_norm == ocr_norm
            score = 1.0 if match else 0.0

        return {
            "nom": nom,
            "bdd": self._serialiser_valeur(valeur_bdd),
            "ocr": self._serialiser_valeur(valeur_ocr),
            "type": type_champ,
            "match": match,
            "score": score,
            "statut": "OK" if match else "ERREUR",
        }

    def _serialiser_valeur(self, valeur: Any) -> Any:
        if isinstance(valeur, (datetime, date)):
            return valeur.isoformat()
        if isinstance(valeur, (BaseManager, QuerySet)):
            return str(valeur)
        if isinstance(valeur, dict):
            return {key: self._serialiser_valeur(item) for key, item in valeur.items()}
        if isinstance(valeur, list):
            return [self._serialiser_valeur(item) for item in valeur]
        if isinstance(valeur, (set, tuple)):
            return [self._serialiser_valeur(item) for item in valeur]
        return valeur

    def _mettre_a_jour_stats(self, comparaison: dict[str, Any], stats: dict[str, Any]) -> None:
        stats["nombre_champs_total"] += 1

        type_champ = comparaison["type"]
        score = comparaison["score"]

        if type_champ == "texte":
            stats["scores_texte"].append(score)
        else:
            stats["scores_numerique"].append(score)

        if comparaison["match"]:
            stats["nombre_champs_corrects"] += 1
            return

        if type_champ == "texte":
            stats["nombre_erreurs_texte"] += 1
        elif type_champ == "nombre":
            stats["nombre_erreurs_nombres"] += 1
        elif type_champ == "date":
            stats["nombre_erreurs_dates"] += 1
