import csv
from datetime import datetime
from django.core.management.base import BaseCommand
from geo.models import AncienneCommune, CommuneFrance


class Command(BaseCommand):
    help = "Importe les anciennes communes fusionnées depuis le fichier CSV officiel (data.gouv.fr)"

    def add_arguments(self, parser):
        parser.add_argument(
            '--file',
            type=str,
            default='communes_nouvelles.csv',
            help='Chemin vers le fichier CSV des communes nouvelles',
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Supprimer toutes les anciennes communes avant l\'import',
        )

    def handle(self, *args, **options):
        fichier_csv = options['file']

        if options['clear']:
            count = AncienneCommune.objects.count()
            AncienneCommune.objects.all().delete()
            self.stdout.write(self.style.WARNING(f'{count} anciennes communes supprimées'))

        self.stdout.write(f"Lecture du fichier {fichier_csv}...")

        try:
            with open(fichier_csv, 'r', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)

                stats = {
                    'importees': 0,
                    'ignorees': 0,
                    'erreurs': 0,
                    'commune_actuelle_introuvable': 0,
                }

                for row in reader:
                    try:
                        # Extraire les données
                        code_insee_nouvelle = row['Code INSEE Commune Nouvelle']
                        nom_nouvelle = row['Nom Commune Nouvelle Siège']
                        code_insee_ancienne = row['Code INSEE Commune Déléguée (non actif)']
                        nom_ancienne = row['Nom Commune Déléguée']
                        date_fusion_str = row['Date']

                        # Ignorer les lignes où la commune déléguée est la même que la nouvelle
                        # (c'est la commune siège)
                        if code_insee_ancienne == code_insee_nouvelle:
                            stats['ignorees'] += 1
                            continue

                        # Chercher la commune actuelle dans notre base
                        try:
                            commune_actuelle = CommuneFrance.objects.get(code_insee=code_insee_nouvelle)
                        except CommuneFrance.DoesNotExist:
                            self.stdout.write(
                                self.style.WARNING(
                                    f"Commune actuelle introuvable: {nom_nouvelle} ({code_insee_nouvelle})"
                                )
                            )
                            stats['commune_actuelle_introuvable'] += 1
                            continue

                        # Parser la date de fusion (format : "MOIS ANNÉE" ex: "AVRIL 2016")
                        date_fusion = self.parser_date_fusion(date_fusion_str)

                        # Créer ou mettre à jour l'ancienne commune
                        ancienne, created = AncienneCommune.objects.update_or_create(
                            code_insee=code_insee_ancienne,
                            defaults={
                                'nom': nom_ancienne,
                                'commune_actuelle': commune_actuelle,
                                'date_fusion': date_fusion,
                                'code_departement': commune_actuelle.code_departement,
                                'departement': commune_actuelle.departement,
                                'commentaire': f"Fusionnée avec {nom_nouvelle} ({date_fusion_str})",
                            },
                        )

                        stats['importees'] += 1

                        if created:
                            self.stdout.write(f"  + {nom_ancienne} -> {nom_nouvelle}")

                    except KeyError as e:
                        stats['erreurs'] += 1
                        self.stdout.write(
                            self.style.ERROR(f"Colonne manquante dans le CSV: {e}")
                        )
                    except Exception as e:
                        stats['erreurs'] += 1
                        self.stdout.write(
                            self.style.ERROR(f"Erreur lors de l'import: {e}")
                        )

                # Afficher les statistiques
                self.stdout.write(
                    self.style.SUCCESS(
                        f"\n{'='*60}\n"
                        f"Import terminé !\n"
                        f"{'='*60}\n"
                        f"Anciennes communes importées : {stats['importees']}\n"
                        f"Lignes ignorées (commune siège) : {stats['ignorees']}\n"
                        f"Communes actuelles introuvables : {stats['commune_actuelle_introuvable']}\n"
                        f"Erreurs : {stats['erreurs']}\n"
                        f"{'='*60}"
                    )
                )

        except FileNotFoundError:
            self.stdout.write(
                self.style.ERROR(
                    f"Fichier {fichier_csv} introuvable.\n"
                    f"Téléchargez-le depuis: https://www.data.gouv.fr/fr/datasets/communes-nouvelles/"
                )
            )
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Erreur fatale: {e}"))

    def parser_date_fusion(self, date_str):
        """
        Parse les dates au format 'MOIS ANNÉE' (ex: 'AVRIL 2016')
        Retourne une date au 1er jour du mois
        """
        mois_fr = {
            'JANVIER': 1,
            'FÉVRIER': 2,
            'FEVRIER': 2,
            'MARS': 3,
            'AVRIL': 4,
            'MAI': 5,
            'JUIN': 6,
            'JUILLET': 7,
            'AOÛT': 8,
            'AOUT': 8,
            'SEPTEMBRE': 9,
            'OCTOBRE': 10,
            'NOVEMBRE': 11,
            'DÉCEMBRE': 12,
            'DECEMBRE': 12,
        }

        try:
            parts = date_str.strip().split()
            if len(parts) == 2:
                mois_nom = parts[0].upper()
                annee = int(parts[1])
                mois = mois_fr.get(mois_nom, 1)
                return datetime(annee, mois, 1).date()
        except (ValueError, IndexError):
            pass

        # Fallback : 1er janvier de l'année en cours
        return datetime.now().date()
