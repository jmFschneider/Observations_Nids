"""
Script de transcription PDF via Google Gemini.
Usage : python transcribe_pdf.py <fichier.pdf> [--output fichier.md]
La clé API Gemini doit être dans la variable d'environnement GEMINI_API_KEY
ou dans un fichier .env à côté de ce script.
"""

import argparse
import contextlib
import os
import sys
import time
from pathlib import Path

from google import genai
from google.genai import types


def charger_env():
    """Charge un fichier .env local si présent."""
    env_path = Path(__file__).parent / ".env"
    if env_path.exists():
        with open(env_path, encoding="utf-8") as f:
            for raw_line in f:
                stripped = raw_line.strip()
                if stripped and not stripped.startswith("#") and "=" in stripped:
                    key, _, value = stripped.partition("=")
                    os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


PROMPT_TRANSCRIPTION = """Tu es un expert en transcription de documents scientifiques.

Transcris intégralement le contenu de ce document PDF en respectant les règles suivantes :

1. **Mise en page colonne unique** : tout le texte doit être présenté en une seule colonne,
   même si le document original est sur deux colonnes. Commence par le titre, les auteurs,
   le résumé, puis le corps du texte dans l'ordre de lecture logique.

2. **Tableaux** : reproduis chaque tableau en Markdown (syntaxe `| col | col |`),
   avec en-têtes et alignement. Conserve toutes les valeurs, unités et notes de bas de tableau.

3. **Formules** : transcris les formules mathématiques en LaTeX inline ($...$) ou bloc ($$...$$).

4. **Figures** : pour chaque figure, indique `[Figure N : légende complète]` à l'emplacement approprié.

5. **Références bibliographiques** : transcris la section références telle quelle, une référence par ligne.

6. **Fidélité** : ne résume pas, ne paraphrase pas — transcris tout le texte original,
   y compris les notes de bas de page et les informations de l'en-tête/pied de page.

7. **Format de sortie** : Markdown pur, sans balises HTML, sans commentaires de ta part.
   Commence directement par le contenu transcrit.
"""


def transcrire_pdf(pdf_path: Path, model_name: str = "gemini-2.5-pro") -> str:
    """Envoie le PDF à Gemini et retourne la transcription."""
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("ERREUR : variable d'environnement GEMINI_API_KEY non définie.")
        print("Définissez-la ou créez un fichier .env contenant : GEMINI_API_KEY=votre_clé")
        sys.exit(1)

    client = genai.Client(api_key=api_key)

    print(f"Envoi du fichier à Gemini ({pdf_path.name})...")
    uploaded_file = client.files.upload(
        file=str(pdf_path),
        config=types.UploadFileConfig(mime_type="application/pdf"),
    )

    # Attendre que le fichier soit prêt
    print("Attente de la disponibilité du fichier...", end="", flush=True)
    while uploaded_file.state is not None and uploaded_file.state.name == "PROCESSING":
        time.sleep(2)
        file_name = uploaded_file.name or ""
        uploaded_file = client.files.get(name=file_name)
        print(".", end="", flush=True)
    print()

    if uploaded_file.state is not None and uploaded_file.state.name == "FAILED":
        raise RuntimeError(f"Échec du traitement du fichier par Gemini : {uploaded_file.state}")

    print(f"Transcription en cours avec {model_name}...")
    response = client.models.generate_content(
        model=model_name,
        contents=[uploaded_file, PROMPT_TRANSCRIPTION],  # type: ignore[arg-type]
        config=types.GenerateContentConfig(
            temperature=0.1,  # Faible température pour maximiser la fidélité
        ),
    )

    # Nettoyage des balises Markdown éventuelles ajoutées par Gemini
    text = response.text or ""
    if text.startswith("```markdown"):
        text = text[len("```markdown") :].lstrip("\n")
        if text.endswith("```"):
            text = text[:-3].rstrip("\n")

    # Suppression du fichier uploadé (bonne pratique)
    with contextlib.suppress(Exception):
        client.files.delete(name=uploaded_file.name or "")  # type: ignore[arg-type]

    return text


def main():
    charger_env()

    parser = argparse.ArgumentParser(description="Transcrit un PDF via Google Gemini.")
    parser.add_argument("pdf", help="Chemin vers le fichier PDF à transcrire")
    parser.add_argument(
        "--output",
        "-o",
        help="Fichier de sortie (défaut : <nom_pdf>_transcription.md)",
    )
    parser.add_argument(
        "--model",
        "-m",
        default="gemini-2.5-pro",
        help="Modèle Gemini à utiliser (défaut : gemini-2.5-pro)",
    )
    args = parser.parse_args()

    pdf_path = Path(args.pdf)
    if not pdf_path.exists():
        print(f"ERREUR : fichier introuvable : {pdf_path}")
        sys.exit(1)
    if pdf_path.suffix.lower() != ".pdf":
        print(f"ERREUR : le fichier doit être un PDF ({pdf_path})")
        sys.exit(1)

    output_path = (
        Path(args.output)
        if args.output
        else pdf_path.with_name(pdf_path.stem + "_transcription.md")
    )

    transcription = transcrire_pdf(pdf_path, model_name=args.model)

    output_path.write_text(transcription, encoding="utf-8")
    print(f"\nTranscription sauvegardée dans : {output_path}")
    print(f"Taille : {len(transcription):,} caractères")


if __name__ == "__main__":
    main()
