#!/usr/bin/env python
"""
Script d'importation des espèces depuis un fichier CSV
"""
import csv
import os
import sys
from collections import defaultdict

import django

# Importer les modèles après avoir configuré Django
from observations.models import Espece, Famille, Ordre

# Configurer l'environnement Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'observations_nids.settings')
django.setup()



def importer_especes(fichier_csv):
    """
    Importer les espèces depuis un fichier CSV
    Structure attendue: Nom anglais, Nom scientifique, Nom français, Statut, Ordre, Famille
    """
    print(f"Importation des données depuis {fichier_csv}")

    # Dictionnaires pour suivre les ordres et familles créés
    ordres = {}
    familles = {}
    especes_importees = 0
    especes_existantes = 0

    # Nettoyer la base si nécessaire
    if input("Voulez-vous supprimer toutes les espèces existantes avant l'importation? (o/n): ").lower() == 'o':
        print("Suppression des données existantes...")
        Espece.objects.all().delete()
        Famille.objects.all().delete()
        Ordre.objects.all().delete()

    # Collecter les statistiques sur les ordres et familles
    stats = defaultdict(lambda: defaultdict(int))

    try:
        with open(fichier_csv, encoding='utf-8') as f:
            reader = csv.reader(f)
            next(reader)  # Ignorer l'en-tête si présent

            for row in reader:
                if len(row) < 6:
                    print(f"Ligne ignorée (format incorrect): {row}")
                    continue

                nom_anglais, nom_scientifique, nom_francais, statut, nom_ordre, nom_famille = row

                # Créer ou récupérer l'ordre
                if nom_ordre not in ordres:
                    ordre, created = Ordre.objects.get_or_create(nom=nom_ordre)
                    ordres[nom_ordre] = ordre
                    if created:
                        print(f"Nouvel ordre créé: {nom_ordre}")
                else:
                    ordre = ordres[nom_ordre]

                # Créer ou récupérer la famille
                famille_key = f"{nom_ordre}|{nom_famille}"
                if famille_key not in familles:
                    famille, created = Famille.objects.get_or_create(
                        nom=nom_famille,
                        defaults={'ordre': ordre}
                    )
                    if created:
                        print(f"Nouvelle famille créée: {nom_famille} (Ordre: {nom_ordre})")
                    elif famille.ordre != ordre:
                        print(f"ATTENTION: La famille {nom_famille} existe déjà avec un ordre différent!")
                        # Mettre à jour l'ordre si nécessaire
                        if input(f"Mettre à jour l'ordre de {nom_famille} vers {nom_ordre}? (o/n): ").lower() == 'o':
                            famille.ordre = ordre
                            famille.save()

                    familles[famille_key] = famille
                else:
                    famille = familles[famille_key]

                # Créer ou récupérer l'espèce
                try:
                    espece, created = Espece.objects.get_or_create(
                        nom=nom_francais,
                        defaults={
                            'nom_anglais': nom_anglais,
                            'nom_scientifique': nom_scientifique,
                            'statut': statut,
                            'famille': famille
                        }
                    )

                    # Mettre à jour les champs si l'espèce existe déjà
                    if not created:
                        espece.nom_anglais = nom_anglais
                        espece.nom_scientifique = nom_scientifique
                        espece.statut = statut
                        espece.famille = famille
                        espece.save()
                        especes_existantes += 1
                        print(f"Espèce mise à jour: {nom_francais}")
                    else:
                        especes_importees += 1

                    # Collecter les statistiques
                    stats[nom_ordre][nom_famille] += 1

                except Exception as e:
                    print(f"Erreur lors de l'importation de {nom_francais}: {e}")

        print("\n=== RÉSUMÉ DE L'IMPORTATION ===")
        print(f"Espèces importées: {especes_importees}")
        print(f"Espèces mises à jour: {especes_existantes}")
        print(f"Nombre d'ordres: {len(ordres)}")
        print(f"Nombre de familles: {len(familles)}")

        print("\n=== STATISTIQUES PAR ORDRE ET FAMILLE ===")
        for ordre_nom, familles_dict in stats.items():
            total_especes = sum(familles_dict.values())
            print(f"\nOrdre: {ordre_nom} ({total_especes} espèces)")
            for famille_nom, nb_especes in sorted(familles_dict.items(), key=lambda x: x[1], reverse=True):
                print(f"  - {famille_nom}: {nb_especes} espèces")

    except Exception as e:
        print(f"Erreur lors de l'importation: {e}")
        return False

    return True


if __name__ == "__main__":
    fichier_csv = sys.argv[1] if len(sys.argv) > 1 else input("Entrez le chemin du fichier CSV: ")
    importer_especes(fichier_csv)
