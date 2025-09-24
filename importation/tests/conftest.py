"""Fixtures spécifiques au module importation."""
import pytest

from importation.models import EspeceCandidate, TranscriptionBrute


@pytest.fixture
def json_data_valid():
    """Données JSON valides pour test."""
    return {
        "informations_generales": {
            "n_fiche": "1234",
            "observateur": "Jean Dupont",
            "n_espece": "42",
            "espece": "Buse variable",
            "annee": "2024",
        },
        "localisation": {
            "IGN_50000": "Paris",
            "commune": "Paris",
            "dep_t": "75",
            "coordonnees_et_ou_lieu_dit": "48.8566, 2.3522",
            "altitude": "35",
            "paysage": "Urbain",
            "alentours": "Parc",
        },
        "nid": {
            "nid_prec_t_meme_c_ple": "Non",
            "haut_nid": "5",
            "h_c_vert": "10",
            "nid": "Grand nid",
        },
        "tableau_donnees": [
            {"Jour": "15", "Mois": "4", "Heure": "14", "Nombre_oeuf": "3", "Nombre_pou": "0"}
        ],
        "tableau_donnees_2": {
            "1er_o_pondu": {"jour": "10", "Mois": "4"},
            "1er_p_eclos": {"jour": "5", "Mois": "5"},
            "1er_p_volant": {"jour": "20", "Mois": "6"},
            "nombre_oeufs": {"pondus": "3", "eclos": "2", "n_ecl": "1"},
            "nombre_poussins": {"1/2": "2", "3/4": "1", "vol_t": "1"},
        },
        "causes_echec": {"causes_d_echec": "Prédation"},
    }


@pytest.fixture
def transcription_brute(json_data_valid):
    """Transcription brute de test."""
    return TranscriptionBrute.objects.create(
        fichier_source="test_result.json", json_brut=json_data_valid
    )


@pytest.fixture
def espece_candidate():
    """Espèce candidate de test."""
    return EspeceCandidate.objects.create(nom_transcrit="Buse variable")