"""Tests pour le module json_sanitizer."""


from observations.json_rep.json_sanitizer import corriger_json, validate_json_structure


class TestValidateJsonStructure:
    """Tests pour la fonction validate_json_structure()."""

    def test_json_valide_complet(self):
        """Test avec un JSON valide et complet."""
        data: dict[str, dict[str, str] | list[dict[str, str]]] = {
            "informations_generales": {
                "n_fiche": "123",
                "observateur": "Test",
                "n_espece": "1",
                "espece": "Buse variable",
                "annee": "2024"
            },
            "nid": {
                "nid_prec_t_meme_c_ple": "non",
                "haut_nid": "10",
                "h_c_vert": "15",
                "nid": "Détails"
            },
            "localisation": {
                "IGN_50000": "ABC",
                "commune": "Paris",
                "dep_t": "75",
                "coordonnees_et_ou_lieu_dit": "48.8,2.3",
                "altitude": "35",
                "paysage": "Urbain",
                "alentours": "Parc"
            },
            "tableau_donnees": [],
            "tableau_donnees_2": {
                "1er_o_pondu": "01/04",
                "1er_p_eclos": "15/05",
                "1er_p_volant": "01/07",
                "nombre_oeufs": "3",
                "nombre_poussins": "2"
            },
            "causes_echec": {
                "causes_d_echec": "Aucune"
            }
        }

        errors = validate_json_structure(data)
        assert errors == []

    def test_json_cle_manquante_top_level(self):
        """Test avec une clé principale manquante."""
        data: dict[str, dict[str, str] | list[dict[str, str]]] = {
            "informations_generales": {},
            # "nid" manquant
            "localisation": {},
            "tableau_donnees": [],
            "tableau_donnees_2": {},
            "causes_echec": {}
        }

        errors = validate_json_structure(data)
        assert len(errors) > 0
        assert any("nid" in error for error in errors)

    def test_json_informations_generales_incomplete(self):
        """Test avec informations_generales incomplètes."""
        data = {
            "informations_generales": {
                "n_fiche": "123",
                # Champs manquants
            },
            "nid": {"nid_prec_t_meme_c_ple": "", "haut_nid": "", "h_c_vert": "", "nid": ""},
            "localisation": {"IGN_50000": "", "commune": "", "dep_t": "", "coordonnees_et_ou_lieu_dit": "", "altitude": "", "paysage": "", "alentours": ""},
            "tableau_donnees": [],
            "tableau_donnees_2": {"1er_o_pondu": "", "1er_p_eclos": "", "1er_p_volant": "", "nombre_oeufs": "", "nombre_poussins": ""},
            "causes_echec": {"causes_d_echec": ""}
        }

        errors = validate_json_structure(data)
        assert len(errors) > 0
        assert any("informations_generales" in error for error in errors)

    def test_json_tableau_donnees_pas_liste(self):
        """Test que tableau_donnees doit être une liste."""
        data = {
            "informations_generales": {"n_fiche": "", "observateur": "", "n_espece": "", "espece": "", "annee": ""},
            "nid": {"nid_prec_t_meme_c_ple": "", "haut_nid": "", "h_c_vert": "", "nid": ""},
            "localisation": {"IGN_50000": "", "commune": "", "dep_t": "", "coordonnees_et_ou_lieu_dit": "", "altitude": "", "paysage": "", "alentours": ""},
            "tableau_donnees": "pas une liste",  # Erreur
            "tableau_donnees_2": {"1er_o_pondu": "", "1er_p_eclos": "", "1er_p_volant": "", "nombre_oeufs": "", "nombre_poussins": ""},
            "causes_echec": {"causes_d_echec": ""}
        }

        errors = validate_json_structure(data)
        assert any("tableau_donnees doit être une liste" in error for error in errors)

    def test_json_causes_echec_champ_manquant(self):
        """Test avec le champ causes_d_echec manquant."""
        data = {
            "informations_generales": {"n_fiche": "", "observateur": "", "n_espece": "", "espece": "", "annee": ""},
            "nid": {"nid_prec_t_meme_c_ple": "", "haut_nid": "", "h_c_vert": "", "nid": ""},
            "localisation": {"IGN_50000": "", "commune": "", "dep_t": "", "coordonnees_et_ou_lieu_dit": "", "altitude": "", "paysage": "", "alentours": ""},
            "tableau_donnees": [],
            "tableau_donnees_2": {"1er_o_pondu": "", "1er_p_eclos": "", "1er_p_volant": "", "nombre_oeufs": "", "nombre_poussins": ""},
            "causes_echec": {}  # causes_d_echec manquant
        }

        errors = validate_json_structure(data)
        assert any("causes_d_echec" in error for error in errors)


class TestCorrigerJson:
    """Tests pour la fonction corriger_json()."""

    def test_corriger_cle_tableau_resume(self):
        """Test de correction du nom 'tableau_resume' en 'tableau_donnees_2'."""
        data = {
            "tableau_resume": {
                "1er_o_pondu": "01/04"
            }
        }

        corrected = corriger_json(data)
        assert "tableau_donnees_2" in corrected
        assert "tableau_resume" not in corrected

    def test_corriger_cle_causes_echec_accent(self):
        """Test de correction de 'causes_d'échec' en 'causes_echec'."""
        data = {
            "causes_d'échec": {
                "causes_d_echec": "Test"
            }
        }

        corrected = corriger_json(data)
        assert "causes_echec" in corrected
        assert "causes_d'échec" not in corrected

    def test_corriger_preserve_donnees_valides(self):
        """Test que les données valides sont préservées."""
        data = {
            "informations_generales": {
                "n_fiche": "123",
                "observateur": "Test",
                "espece": "Buse",
                "annee": "2024"
            },
            "nid": {
                "haut_nid": "10"
            }
        }

        corrected = corriger_json(data)
        assert corrected["informations_generales"]["n_fiche"] == "123"
        assert corrected["informations_generales"]["observateur"] == "Test"

    def test_corriger_json_vide(self):
        """Test avec un JSON vide."""
        data: dict[str, dict[str, str] | list[dict[str, str]]] = {}
        corrected = corriger_json(data)
        assert isinstance(corrected, dict)

    def test_corriger_ne_modifie_pas_original(self):
        """Test que la fonction ne modifie pas le dictionnaire original."""
        original = {
            "tableau_resume": {"test": "value"},
            "informations_generales": {"n_fiche": "123"}
        }

        corrected = corriger_json(original)

        # L'original ne doit pas être modifié
        assert "tableau_resume" in original
        # Le corrigé doit avoir la nouvelle clé
        assert "tableau_donnees_2" in corrected
        assert "tableau_resume" not in corrected
