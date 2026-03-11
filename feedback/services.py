import json
import logging

from django.conf import settings
from google import genai
from google.genai import types

logger = logging.getLogger(__name__)


def analyze_feedback_with_ai(feedback_content):
    """
    Utilise Gemini pour analyser un feedback utilisateur.
    Retourne un dictionnaire avec : category, urgency, sentiment, summary.
    """
    if not hasattr(settings, 'GEMINI_API_KEY') or not settings.GEMINI_API_KEY:
        logger.warning("GEMINI_API_KEY non configurée. Analyse IA désactivée.")
        return None

    try:
        client = genai.Client(api_key=settings.GEMINI_API_KEY)
        model_name = 'gemini-2.0-flash'  # Modèle rapide et efficace

        prompt = f"""
        Analyse le retour utilisateur suivant pour une application d'observation de nids d'oiseaux.
        Retourne uniquement un objet JSON valide avec les clés suivantes :
        - category: une valeur parmi ["BUG", "IDEA", "DATA", "QUESTION", "OCR", "INGEST", "OTHER"]
          * OCR : problème lié à la transcription Gemini (lecture de fiches papier, prompt OCR)
          * INGEST : problème lié à l'import du JSON (correspondance espèce, observateur, géocodage, données incohérentes après import)
          * BUG : autre problème technique de l'application
          * DATA : donnée erronée dans une fiche
          * IDEA : suggestion d'amélioration
          * QUESTION : demande d'information
          * OTHER : autre
        - urgency: un entier de 1 (faible) à 5 (critique)
        - sentiment: un court texte décrivant l'humeur (ex: "Frustré", "Constructif", "Satisfait")
        - summary: un résumé très court (max 10 mots) du problème ou de l'idée.

        Texte utilisateur :
        "{feedback_content}"
        """

        response = client.models.generate_content(
            model=model_name,
            contents=[prompt],
            config=types.GenerateContentConfig(
                response_mime_type='application/json',
            ),
        )

        # Extraction du JSON
        analysis = json.loads(response.text)
        return analysis

    except Exception as e:
        logger.error(f"Erreur lors de l'analyse IA du feedback : {e}")
        return None
