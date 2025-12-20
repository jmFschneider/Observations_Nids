"""
Script de test simple pour vérifier le fonctionnement de Gemini API.

Ce script teste:
1. La connexion à l'API Gemini
2. Les différents noms de modèles possibles
3. La transcription d'une seule image
4. Le parsing du JSON retourné

Usage:
    python pilot/test_gemini_simple.py <chemin_image>

Exemple:
    python pilot/test_gemini_simple.py "media/jpeg_pdf/TRI_ANCIEN/FUSION_FULL/fiche 25_FINAL.jpg"
"""

import json
import os
import sys
from pathlib import Path

import django
import google.generativeai as genai
from dotenv import load_dotenv
from PIL import Image

# Charger le fichier .env
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)
print(f"📁 Chargement du fichier .env depuis: {env_path}")

# Configuration Django
sys.path.insert(0, str(Path(__file__).parent.parent))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'observations_nids.settings')
django.setup()

from django.conf import settings  # noqa: E402


def tester_modeles_gemini():
    """Liste les modèles disponibles via l'API Gemini."""
    print("\n" + "=" * 80)
    print("📋 LISTE DES MODÈLES GEMINI DISPONIBLES")
    print("=" * 80)

    try:
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            print("❌ GEMINI_API_KEY non trouvée dans le fichier .env")
            return False

        genai.configure(api_key=api_key)

        print("\nModèles supportant generateContent:")
        for model in genai.list_models():
            if 'generateContent' in model.supported_generation_methods:
                print(f"  ✓ {model.name}")
                print(f"    Display name: {model.display_name}")
                print(f"    Description: {model.description[:100]}...")
                print()

        return True
    except Exception as e:
        print(f"❌ Erreur lors de la récupération des modèles: {e}")
        return False


def charger_prompt(type_prompt='standard'):
    """Charge le fichier prompt."""
    print("\n" + "=" * 80)
    print(f"📄 CHARGEMENT DU PROMPT ({type_prompt.upper()})")
    print("=" * 80)

    if type_prompt == 'ancien':
        prompt_filename = 'prompt_gemini_transcription_Ancienne_Fiche.txt'
    else:
        prompt_filename = 'prompt_gemini_transcription.txt'

    prompt_path = Path(settings.BASE_DIR) / 'observations' / 'json_rep' / prompt_filename

    try:
        with open(prompt_path, encoding='utf-8') as f:
            prompt_content = f.read()
        print(f"✓ Prompt chargé: {prompt_filename}")
        print(f"  Longueur: {len(prompt_content)} caractères")
        print(f"  Premières lignes:\n{prompt_content[:200]}...")
        return prompt_content
    except FileNotFoundError:
        print(f"❌ Fichier prompt introuvable: {prompt_path}")
        return None


def tester_transcription(image_path, model_name, prompt):
    """Teste la transcription d'une image avec un modèle spécifique."""
    print("\n" + "=" * 80)
    print("🧪 TEST DE TRANSCRIPTION")
    print("=" * 80)
    print(f"Image: {image_path}")
    print(f"Modèle: {model_name}")
    print()

    try:
        # Charger l'image
        print("1️⃣ Chargement de l'image...")
        img = Image.open(image_path)
        print(f"   ✓ Image chargée: {img.size[0]}x{img.size[1]} pixels, mode {img.mode}")

        # Configurer Gemini
        print("\n2️⃣ Configuration de l'API Gemini...")
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            print("   ❌ GEMINI_API_KEY non trouvée dans le fichier .env")
            return None

        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(model_name)
        print(f"   ✓ Modèle configuré: {model_name}")

        # Appeler l'API
        print("\n3️⃣ Appel de l'API Gemini...")
        print("   ⏳ En attente de la réponse...")
        response = model.generate_content([prompt, img])
        print("   ✓ Réponse reçue!")

        # Extraire le texte
        print("\n4️⃣ Extraction du texte de la réponse...")
        if not response.text:
            print("   ❌ Réponse vide!")
            return None

        response_text = response.text.strip()
        print(f"   ✓ Texte extrait ({len(response_text)} caractères)")

        # Parser le JSON
        print("\n5️⃣ Parsing du JSON...")

        # Nettoyer le texte (enlever les backticks markdown si présents)
        if response_text.startswith('```'):
            lines = response_text.split('\n')
            # Enlever la première ligne (```json ou ```)
            if lines[0].strip() in ['```json', '```']:
                lines = lines[1:]
            # Enlever la dernière ligne (```)
            if lines and lines[-1].strip() == '```':
                lines = lines[:-1]
            response_text = '\n'.join(lines).strip()

        try:
            json_data = json.loads(response_text)
            print("   ✓ JSON valide!")

            # Afficher la structure
            print("\n📊 STRUCTURE DU JSON:")
            print(f"   Clés principales: {list(json_data.keys())}")

            if 'informations_generales' in json_data:
                info_gen = json_data['informations_generales']
                print("\n   Informations générales:")
                print(f"     - Espèce: {info_gen.get('espece', 'N/A')}")
                print(f"     - Observateur: {info_gen.get('observateur', 'N/A')}")
                print(f"     - Année: {info_gen.get('annee', 'N/A')}")

            if 'tableau_donnees' in json_data:
                nb_obs = len(json_data['tableau_donnees'])
                print(f"\n   Tableau de données: {nb_obs} observation(s)")

            return json_data

        except json.JSONDecodeError as e:
            print(f"   ❌ JSON invalide: {e}")
            print(f"\n   Texte brut reçu:\n{response_text[:500]}...")
            return None

    except Exception as e:
        print(f"\n❌ ERREUR: {e}")
        import traceback  # noqa: PLC0415
        traceback.print_exc()
        return None


def main():
    print("\n" + "=" * 80)
    print("🔬 SCRIPT DE TEST GEMINI - VERSION SIMPLE")
    print("=" * 80)

    # Vérifier les arguments
    if len(sys.argv) < 2:
        print("\n❌ Usage: python pilot/test_gemini_simple.py <chemin_image>")
        print("\nExemple:")
        print('  python pilot/test_gemini_simple.py "media/jpeg_pdf/TRI_ANCIEN/FUSION_FULL/fiche 25_FINAL.jpg"')
        sys.exit(1)

    image_path = sys.argv[1]

    # Vérifier que l'image existe
    if not os.path.exists(image_path):
        print(f"\n❌ Image introuvable: {image_path}")
        sys.exit(1)

    # 1. Lister les modèles disponibles
    if not tester_modeles_gemini():
        print("\n⚠️ Impossible de lister les modèles, mais on continue...")

    # 2. Charger le prompt
    type_prompt = 'ancien' if 'ancien' in image_path.lower() else 'standard'
    prompt = charger_prompt(type_prompt)
    if not prompt:
        print("\n❌ Impossible de charger le prompt. Arrêt.")
        sys.exit(1)

    # 3. Tester différents noms de modèles (compte payant)
    modeles_a_tester = [
        'gemini-3-flash-preview',
        'gemini-3-pro-preview',
        'gemini-2.5-pro',
        'gemini-2.5-flash-lite',
    ]

    print("\n" + "=" * 80)
    print("🎯 TESTS DES DIFFÉRENTS MODÈLES")
    print("=" * 80)

    resultats = {}
    for model_name in modeles_a_tester:
        print(f"\n{'─' * 80}")
        print(f"Test avec: {model_name}")
        print('─' * 80)

        json_data = tester_transcription(image_path, model_name, prompt)
        resultats[model_name] = json_data is not None

        if json_data:
            print(f"\n✅ SUCCÈS avec {model_name}!")
            break
        else:
            print(f"\n❌ ÉCHEC avec {model_name}")

    # Résumé final
    print("\n" + "=" * 80)
    print("📈 RÉSUMÉ DES TESTS")
    print("=" * 80)
    for model_name, succes in resultats.items():
        statut = "✅ SUCCÈS" if succes else "❌ ÉCHEC"
        print(f"{statut} - {model_name}")

    print("\n" + "=" * 80)


if __name__ == '__main__':
    main()
