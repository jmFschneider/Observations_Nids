import copy


def validate_json_structure(data):
    """
    Valide qu'un dictionnaire JSON respecte la structure attendue.
    Retourne une liste d'erreurs (vide si tout est conforme).
    """

    errors = []

    required_top_keys = [
        "informations_generales",
        "nid",
        "localisation",
        "tableau_donnees",
        "tableau_donnees_2",
        "causes_echec",
    ]
    for key in required_top_keys:
        if key not in data:
            errors.append(f"Clé manquante : {key}")

    # Vérifications détaillées si les clés existent
    if "informations_generales" in data:
        expected = {"n_fiche", "observateur", "n_espece", "espece", "annee"}
        found = set(data["informations_generales"].keys())
        missing = expected - found
        if missing:
            errors.append(f"informations_generales : champs manquants : {missing}")

    if "nid" in data:
        expected = {"nid_prec_t_meme_c_ple", "haut_nid", "h_c_vert", "nid"}
        missing = expected - set(data["nid"].keys())
        if missing:
            errors.append(f"nid : champs manquants : {missing}")

    if "localisation" in data:
        expected = {
            "IGN_50000",
            "commune",
            "dep_t",
            "coordonnees_et_ou_lieu_dit",
            "altitude",
            "paysage",
            "alentours",
        }
        missing = expected - set(data["localisation"].keys())
        if missing:
            errors.append(f"localisation : champs manquants : {missing}")

    if "tableau_donnees" in data and not isinstance(data["tableau_donnees"], list):
        errors.append("tableau_donnees doit être une liste")

    if "tableau_donnees_2" in data:
        expected = {"1er_o_pondu", "1er_p_eclos", "1er_p_volant", "nombre_oeufs", "nombre_poussins"}
        missing = expected - set(data["tableau_donnees_2"].keys())
        if missing:
            errors.append(f"tableau_donnees_2 : champs manquants : {missing}")

    if "causes_echec" in data and "causes_d_echec" not in data["causes_echec"]:
        errors.append("causes_echec : champ 'causes_d_echec' manquant")

    return errors


def corriger_json(data):
    """
    Corrige un JSON issu de la transcription Gemini pour le rendre conforme à la structure cible.
    Cette fonction renomme les clés incohérentes, homogénéise les structures et complète les champs manquants.
    """

    corrected = copy.deepcopy(data)

    # Renommage des clés principales si besoin
    rename_keys_top = {
        "tableau_resume": "tableau_donnees_2",
        "tableau_donnees2": "tableau_donnees_2",
        "tableau_recap": "tableau_donnees_2",
        "causes_d'échec": "causes_echec",
    }
    for old_key, new_key in rename_keys_top.items():
        if old_key in corrected and new_key not in corrected:
            corrected[new_key] = corrected.pop(old_key)

    # Corriger les noms de champs dans "informations_generales"
    if "informations_generales" in corrected:
        info = corrected["informations_generales"]
        info_corrections = {
            "n° fiche": "n_fiche",
            "n° espéce": "n_espece",
            "espèce": "espece",
            "année": "annee",
        }
        for old_key, new_key in info_corrections.items():
            if old_key in info:
                info[new_key] = info.pop(old_key)

    # Corriger les noms dans "nid"
    if "nid" in corrected:
        nid = corrected["nid"]
        nid_corrections = {
            "nid préc't même c'ple": "nid_prec_t_meme_c_ple",
            "haut. nid": "haut_nid",
            "h.c'vert": "h_c_vert",
        }
        for old_key, new_key in nid_corrections.items():
            if old_key in nid:
                nid[new_key] = nid.pop(old_key)

    # Corriger les noms dans "localisation"
    if "localisation" in corrected:
        loc = corrected["localisation"]
        loc_corrections = {
            "IGN/50000": "IGN_50000",
            "dép't": "dep_t",
            "coordonées et/ou lieu-dit": "coordonnees_et_ou_lieu_dit",
            "coordonées_et_ou_lieu_dit": "coordonnees_et_ou_lieu_dit",  # sécurité
        }
        for old_key, new_key in loc_corrections.items():
            if old_key in loc:
                loc[new_key] = loc.pop(old_key)

    # Corriger les noms dans "tableau_donnees"
    if "tableau_donnees" in corrected:
        for entry in corrected["tableau_donnees"]:
            if isinstance(entry, dict):
                entry_corrections = {
                    "Nombre œuf": "Nombre_oeuf",
                    "Nombre oeuf": "Nombre_oeuf",
                    "Nombre pou": "Nombre_pou",
                }
                for old_key, new_key in entry_corrections.items():
                    if old_key in entry:
                        entry[new_key] = entry.pop(old_key)

    # Forcer les sous-éléments de "tableau_donnees_2" à être des objets (et non des listes ou absents)
    def ensure_keys(dct, keys):
        for k in keys:
            if k not in dct or not isinstance(dct[k], dict):
                dct[k] = (
                    {"jour": None, "Mois": None, "Precision": None}
                    if "1er" in k
                    else {"pondus": None, "eclos": None, "n_ecl": None}
                    if k == "nombre_oeufs"
                    else {"1/2": None, "3/4": None, "vol_t": None}
                )

    if "tableau_donnees_2" in corrected:
        td2 = corrected["tableau_donnees_2"]
        ensure_keys(
            td2, ["1er_o_pondu", "1er_p_eclos", "1er_p_volant", "nombre_oeufs", "nombre_poussins"]
        )

        # Corriger cas particuliers où ces champs sont des listes (à plat)
        for key in [
            "1er_o_pondu",
            "1er_p_eclos",
            "1er_p_volant",
            "nombre_oeufs",
            "nombre_poussins",
        ]:
            if isinstance(td2.get(key), list) and len(td2[key]) > 0:
                td2[key] = td2[key][0]

    # Corriger champ 'causes_echec'
    if "causes_echec" in corrected and "causes d'échec" in corrected["causes_echec"]:
        corrected["causes_echec"]["causes_d_echec"] = corrected["causes_echec"].pop(
            "causes d'échec"
        )

    return corrected
