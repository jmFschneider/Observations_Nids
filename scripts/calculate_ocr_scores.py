import os
import sys
import django

# Setup Django
sys.path.append(os.getcwd())
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "observations_nids.settings")
django.setup()

from ocr.models import TranscriptionOCR
from ocr.tasks import comparer_ocr_fichier_task

def calculate_all_scores():
    # Sélectionner les transcriptions non évaluées qui ont une fiche liée
    transcriptions = TranscriptionOCR.objects.filter(
        statut_evaluation='non_evaluee',
        fiche__isnull=False
    )
    
    total = transcriptions.count()
    print(f"🚀 Démarrage du calcul des scores pour {total} transcriptions...")
    
    success = 0
    errors = 0

    for i, t in enumerate(transcriptions):
        try:
            print(f"[{i+1}/{total}] 🔄 Calcul pour : {t.chemin_json}")
            
            # Appeler la tâche de comparaison (force=True pour écraser si besoin)
            # On passe le chemin relatif tel que stocké en BDD
            resultat = comparer_ocr_fichier_task(t.chemin_json, options={'force': True})
            
            if resultat.get('statut') == 'OK':
                success += 1
                # On récupère l'objet à nouveau pour l'affichage (mis à jour par la task)
                t.refresh_from_db()
                print(f"   ✅ Global: {t.score_global:.1f}% | Texte: {t.score_texte:.1f}% | Num: {t.score_numerique:.1f}%")
            else:
                print(f"   ⚠️ Échec : {resultat.get('statut')}")
                errors += 1
                
        except Exception as e:
            print(f"   ❌ Erreur système : {e}")
            errors += 1

    print("-" * 60)
    print(f"🏁 Terminé !")
    print(f"   - Succès : {success}")
    print(f"   - Échecs : {errors}")

    # Export CSV
    export_csv()

def export_csv():
    import csv
    from django.utils import timezone
    
    output_file = "ocr_results.csv"
    print(f"\n📊 Export des résultats vers {output_file}...")
    
    qs = TranscriptionOCR.objects.exclude(statut_evaluation='non_evaluee').order_by('fiche__num_fiche', 'modele_ocr')
    
    if not qs.exists():
        print("   ⚠️ Aucune donnée à exporter.")
        return

    with open(output_file, 'w', newline='', encoding='utf-8-sig') as csvfile:
        fieldnames = [
            'Fiche', 
            'Modele OCR', 
            'Type Image', 
            'Traitement', 
            'Score Global', 
            'Score Texte', 
            'Score Numerique',
            'Err. Dates',
            'Err. Nombres',
            'Err. Texte',
            'Err. Especes',
            'Err. Lieux',
            'Temps Traitement (s)'
        ]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter=';')
        writer.writeheader()
        
        count = 0
        for t in qs:
            writer.writerow({
                'Fiche': f"#{t.fiche.num_fiche}" if t.fiche else "Inconnue",
                'Modele OCR': t.modele_ocr,
                'Type Image': t.type_image,
                'Traitement': t.traitement_image,
                'Score Global': f"{t.score_global:.2f}".replace('.', ',') if t.score_global is not None else "",
                'Score Texte': f"{t.score_texte:.2f}".replace('.', ',') if t.score_texte is not None else "",
                'Score Numerique': f"{t.score_numerique:.2f}".replace('.', ',') if t.score_numerique is not None else "",
                'Err. Dates': t.nombre_erreurs_dates,
                'Err. Nombres': t.nombre_erreurs_nombres,
                'Err. Texte': t.nombre_erreurs_texte,
                'Err. Especes': t.nombre_erreurs_especes,
                'Err. Lieux': t.nombre_erreurs_lieux,
                'Temps Traitement (s)': f"{t.temps_traitement_secondes:.2f}".replace('.', ',') if t.temps_traitement_secondes else ""
            })
            count += 1
            
    print(f"   ✅ Export terminé : {count} lignes écrites.")

if __name__ == "__main__":
    calculate_all_scores()
