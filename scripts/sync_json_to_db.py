import os
import sys
import django
import json
from pathlib import Path

# Setup Django
sys.path.append(os.getcwd())
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "observations_nids.settings")
django.setup()

from django.conf import settings
from ocr.models import TranscriptionOCR
from ocr.services.fichier_matcher import FichierMatcher

def sync_json_to_db():
    media_root = Path(settings.MEDIA_ROOT)
    transcription_dir = media_root / "transcription_results"
    
    print(f"🔍 Scan du dossier : {transcription_dir}")
    
    if not transcription_dir.exists():
        print("❌ Dossier introuvable !")
        return

    # Lister tous les fichiers JSON récursivement
    fichiers_json = list(transcription_dir.rglob("*_result.json"))
    print(f"📂 {len(fichiers_json)} fichiers JSON trouvés.")
    
    created_count = 0
    skipped_count = 0
    errors = 0

    for json_path in fichiers_json:
        try:
            # Chemin relatif pour la BDD (ex: transcription_results/...)
            rel_path = json_path.relative_to(media_root)
            chemin_bdd = rel_path.as_posix()
            
            # Vérifier si existe déjà
            if TranscriptionOCR.objects.filter(chemin_json=chemin_bdd).exists():
                skipped_count += 1
                continue

            # Retrouver les métadonnées et la fiche
            fiche, metadata = FichierMatcher.trouver_fiche_depuis_json(chemin_bdd)
            
            # Créer l'entrée
            TranscriptionOCR.objects.create(
                fiche=fiche,
                chemin_json=chemin_bdd,
                chemin_image=metadata.get("chemin_image_attendu", ""),
                type_image=metadata.get("type_image", "inconnu"),
                traitement_image=metadata.get("traitement_image", ""),
                modele_ocr=metadata.get("modele_ocr", "inconnu"),
                statut_evaluation="non_evaluee"
            )
            created_count += 1
            print(f"✅ Créé : {chemin_bdd} (Fiche #{fiche.num_fiche if fiche else '?'})")
            
        except Exception as e:
            print(f"❌ Erreur sur {json_path.name}: {e}")
            errors += 1

    print("-" * 60)
    print(f"🎉 Terminé !")
    print(f"   - Créés : {created_count}")
    print(f"   - Ignorés (déjà existants) : {skipped_count}")
    print(f"   - Erreurs : {errors}")

if __name__ == "__main__":
    sync_json_to_db()
