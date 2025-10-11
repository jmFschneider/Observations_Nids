"""
Commande Django pour charger les espèces d'oiseaux depuis TaxRef (INPN/MNHN).

Cette commande télécharge et importe les données taxonomiques des oiseaux de France
depuis le référentiel TaxRef du Muséum national d'Histoire naturelle.

Usage:
    python manage.py charger_taxref
    python manage.py charger_taxref --force
    python manage.py charger_taxref --file /chemin/vers/TAXREFv17.txt
    python manage.py charger_taxref --version 18.0

Compatible Raspberry Pi - gestion optimisée de la mémoire.
"""

import csv
import zipfile
from pathlib import Path

import requests
from django.core.management.base import BaseCommand
from django.db import transaction

from taxonomy.models import Espece, Famille, Ordre


class Command(BaseCommand):
    help = "Charge les espèces d'oiseaux depuis le référentiel TaxRef de l'INPN"

    # URL de téléchargement TaxRef (INPN)
    # Note: Les URLs INPN ne permettent pas le téléchargement direct automatisé
    # Il faut télécharger manuellement depuis https://inpn.mnhn.fr/telechargement/referentielEspece/referentielTaxo
    # et utiliser l'option --file
    TAXREF_VERSIONS = {
        '17.0': 'https://inpn.mnhn.fr/telechargement/referentielEspece/taxref/17.0/zip',
        '18.0': 'https://inpn.mnhn.fr/telechargement/referentielEspece/taxref/18.0/zip',
    }

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force le rechargement même si des espèces existent déjà',
        )
        parser.add_argument(
            '--file',
            type=str,
            help='Chemin vers le fichier TAXREFvXX.txt à importer (évite le téléchargement)',
        )
        parser.add_argument(
            '--taxref-version',
            type=str,
            default='17.0',
            choices=['17.0', '18.0'],
            help='Version de TaxRef à télécharger (défaut: 17.0)',
        )
        parser.add_argument(
            '--limit',
            type=int,
            help='Limite le nombre d\'espèces à importer (pour tests)',
        )

    def handle(self, *args, **options):
        """Point d'entrée principal de la commande."""
        self.stdout.write(self.style.MIGRATE_HEADING('\n=== Chargement TaxRef - Oiseaux de France ===\n'))

        # Vérifier si déjà chargé depuis TaxRef
        especes_taxref = Espece.objects.filter(valide_par_admin=True).count()
        if especes_taxref > 100 and not options['force']:
            self.stdout.write(
                self.style.WARNING(
                    f'{especes_taxref} espèces TaxRef déjà en base. '
                    'Utilisez --force pour recharger (ATTENTION: nécessite que les fiches '
                    'n\'utilisent pas ces espèces).'
                )
            )
            return

        # Obtenir le fichier TaxRef
        if options['file']:
            taxref_file = Path(options['file'])
            if not taxref_file.exists():
                self.stdout.write(self.style.ERROR(f"Fichier introuvable: {taxref_file}"))
                return
            self.stdout.write(f"Utilisation du fichier local: {taxref_file}")
        else:
            taxref_file = self._download_taxref(options['taxref_version'])
            if not taxref_file:
                return

        # Supprimer les anciennes données si --force
        if options['force']:
            self._clear_database()

        # Importer les données
        stats = self._import_taxref(taxref_file, limit=options.get('limit'))

        # Afficher le rapport final
        self._display_report(stats)

    def _download_taxref(self, version: str) -> Path | None:
        """Télécharge et extrait le fichier TaxRef."""
        url = self.TAXREF_VERSIONS.get(version)
        if not url:
            self.stdout.write(self.style.ERROR(f"Version TaxRef inconnue: {version}"))
            return None

        # Créer le répertoire de téléchargement
        download_dir = Path('tmp/taxref')
        download_dir.mkdir(parents=True, exist_ok=True)

        zip_path = download_dir / f'TAXREF_v{version}.zip'
        txt_path = download_dir / f'TAXREFv{version.replace(".", "")}.txt'

        # Télécharger le fichier zip si nécessaire
        if not txt_path.exists():
            self.stdout.write(f"Téléchargement de TaxRef v{version}...")
            self.stdout.write(f"URL: {url}")

            try:
                response = requests.get(url, stream=True, timeout=60)
                response.raise_for_status()

                # Téléchargement avec barre de progression
                total_size = int(response.headers.get('content-length', 0))
                with open(zip_path, 'wb') as f:
                    downloaded = 0
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total_size > 0:
                            percent = int(50 * downloaded / total_size)
                            self.stdout.write(
                                f'\rProgrès: [{"=" * percent}{" " * (50 - percent)}] '
                                f'{downloaded / 1024 / 1024:.1f}MB',
                                ending='',
                            )
                    self.stdout.write()  # Nouvelle ligne

                self.stdout.write(self.style.SUCCESS("Téléchargement terminé"))

                # Extraire le fichier
                self.stdout.write("Extraction du fichier...")
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    # Chercher le fichier TAXREFvXX.txt dans l'archive
                    taxref_filename = None
                    for name in zip_ref.namelist():
                        if name.startswith('TAXREF') and name.endswith('.txt'):
                            taxref_filename = name
                            break

                    if not taxref_filename:
                        self.stdout.write(
                            self.style.ERROR("Fichier TAXREF*.txt introuvable dans l'archive")
                        )
                        return None

                    zip_ref.extract(taxref_filename, download_dir)
                    extracted_path = download_dir / taxref_filename

                    # Renommer si nécessaire
                    if extracted_path != txt_path:
                        extracted_path.rename(txt_path)

                self.stdout.write(self.style.SUCCESS("Extraction terminée"))

                # Nettoyer le zip
                zip_path.unlink()

            except requests.RequestException as e:
                self.stdout.write(self.style.ERROR(f'Erreur lors du téléchargement: {e}'))
                return None
            except zipfile.BadZipFile as e:
                self.stdout.write(self.style.ERROR(f'Fichier zip corrompu: {e}'))
                return None

        else:
            self.stdout.write(f"Utilisation du fichier existant: {txt_path}")

        return txt_path

    def _clear_database(self):
        """Supprime les données taxonomiques existantes."""
        self.stdout.write("Suppression des données existantes...")

        with transaction.atomic():
            especes_count = Espece.objects.count()
            familles_count = Famille.objects.count()
            ordres_count = Ordre.objects.count()

            Espece.objects.all().delete()
            Famille.objects.all().delete()
            Ordre.objects.all().delete()

            self.stdout.write(
                self.style.WARNING(
                    f"Supprimé: {especes_count} espèces, "
                    f"{familles_count} familles, {ordres_count} ordres"
                )
            )

    def _import_taxref(self, taxref_file: Path, limit: int | None = None) -> dict:
        """
        Importe les données TaxRef depuis le fichier.
        Optimisé pour Raspberry Pi avec traitement par lots.
        """
        self.stdout.write(f"\nImport des données depuis: {taxref_file}")
        self.stdout.write("Filtrage: Classe Aves (oiseaux) présents en France\n")

        stats = {
            'total_lines': 0,
            'oiseaux_france': 0,
            'ordres_created': 0,
            'familles_created': 0,
            'especes_created': 0,
            'erreurs': 0,
        }

        # Caches pour éviter les requêtes répétées
        ordres_cache: dict[str, Ordre] = {}
        familles_cache: dict[str, Famille] = {}

        # Traitement par lots (optimisation mémoire)
        batch_size = 500
        especes_batch = []

        try:
            with open(taxref_file, encoding='utf-8') as f:
                # Lire l'en-tête pour obtenir les indices des colonnes
                reader = csv.DictReader(f, delimiter='\t')

                for row in reader:
                    stats['total_lines'] += 1

                    # Filtrer: seulement les oiseaux (Aves) présents en France
                    if row.get('CLASSE') != 'Aves':
                        continue

                    # Vérifier présence en France métropolitaine ou outre-mer
                    if row.get('FR') not in ['P', 'E', 'C']:  # P=Présent, E=Endémique, C=Commune
                        continue

                    stats['oiseaux_france'] += 1

                    # Limiter si option --limit
                    if limit and stats['oiseaux_france'] > limit:
                        break

                    # Extraire les données
                    try:
                        ordre_nom = row.get('ORDRE', '').strip()
                        famille_nom = row.get('FAMILLE', '').strip()
                        nom_vernaculaire = row.get('NOM_VERN', '').strip()
                        nom_scientifique = row.get('LB_NOM', '').strip()
                        nom_anglais = row.get('NOM_VERN_ENG', '').strip()

                        # Ignorer les entrées sans nom vernaculaire français
                        if not nom_vernaculaire:
                            continue

                        # Créer/récupérer l'ordre
                        if ordre_nom and ordre_nom not in ordres_cache:
                            ordre, created = Ordre.objects.get_or_create(
                                nom=ordre_nom, defaults={'description': ''}
                            )
                            ordres_cache[ordre_nom] = ordre
                            if created:
                                stats['ordres_created'] += 1

                        # Créer/récupérer la famille
                        famille = None
                        if famille_nom and ordre_nom:
                            famille_key = f"{ordre_nom}|{famille_nom}"
                            if famille_key not in familles_cache:
                                famille, created = Famille.objects.get_or_create(
                                    nom=famille_nom,
                                    defaults={'ordre': ordres_cache[ordre_nom], 'description': ''},
                                )
                                familles_cache[famille_key] = famille
                                if created:
                                    stats['familles_created'] += 1
                            else:
                                famille = familles_cache[famille_key]

                        # Créer l'espèce (en batch)
                        espece = Espece(
                            nom=nom_vernaculaire,
                            nom_scientifique=nom_scientifique,
                            nom_anglais=nom_anglais,
                            famille=famille,
                            statut=row.get('FR', ''),
                            valide_par_admin=True,  # TaxRef est une source officielle
                            commentaire=f"Import TaxRef - Habitat: {row.get('HABITAT', '')}",
                        )
                        especes_batch.append(espece)

                        # Insertion par lots
                        if len(especes_batch) >= batch_size:
                            self._insert_batch(especes_batch, stats)
                            especes_batch = []

                            # Afficher la progression
                            self.stdout.write(
                                f'\rEspèces importées: {stats["especes_created"]}', ending=''
                            )

                    except Exception as e:
                        stats['erreurs'] += 1
                        self.stdout.write(
                            self.style.WARNING(
                                f"\nErreur ligne {stats['total_lines']}: {e}\n"
                                f"  Ordre: {ordre_nom}, Famille: {famille_nom}, "
                                f"Espèce: {nom_vernaculaire}"
                            )
                        )

                # Insérer le dernier lot
                if especes_batch:
                    self._insert_batch(especes_batch, stats)

                self.stdout.write()  # Nouvelle ligne après la progression

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'\nErreur lors de la lecture du fichier: {e}'))
            return stats

        return stats

    def _insert_batch(self, especes_batch: list, stats: dict):
        """Insère un lot d'espèces avec gestion des doublons."""
        try:
            # Utiliser ignore_conflicts pour éviter les erreurs de doublons
            Espece.objects.bulk_create(especes_batch, ignore_conflicts=True)
            stats['especes_created'] += len(especes_batch)
        except Exception:
            # Fallback: insertion une par une en cas d'erreur
            for espece in especes_batch:
                try:
                    espece.save()
                    stats['especes_created'] += 1
                except Exception:
                    stats['erreurs'] += 1

    def _display_report(self, stats: dict):
        """Affiche le rapport final d'import."""
        self.stdout.write(self.style.MIGRATE_HEADING('\n=== Rapport d\'import ===\n'))

        self.stdout.write(
            self.style.SUCCESS(
                f"Lignes traitées: {stats['total_lines']:,}\n"
                f"Oiseaux France trouvés: {stats['oiseaux_france']:,}\n"
                f"\nCréations:\n"
                f"   - Ordres: {stats['ordres_created']}\n"
                f"   - Familles: {stats['familles_created']}\n"
                f"   - Espèces: {stats['especes_created']}\n"
            )
        )

        if stats['erreurs'] > 0:
            self.stdout.write(self.style.WARNING(f"Erreurs: {stats['erreurs']}"))

        # Statistiques finales en base
        self.stdout.write(self.style.MIGRATE_HEADING('\n=== Base de données ===\n'))
        total_ordres = Ordre.objects.count()
        total_familles = Famille.objects.count()
        total_especes = Espece.objects.count()

        self.stdout.write(
            self.style.SUCCESS(
                f"Ordres: {total_ordres}\n"
                f"Familles: {total_familles}\n"
                f"Espèces: {total_especes}\n"
            )
        )

        # Exemples d'espèces
        self.stdout.write(self.style.MIGRATE_HEADING('Exemples d\'espèces importées:'))
        exemples = Espece.objects.select_related('famille', 'famille__ordre')[:5]
        for esp in exemples:
            famille_info = f" ({esp.famille.nom})" if esp.famille else ""
            self.stdout.write(f"  - {esp.nom}{famille_info} - {esp.nom_scientifique}")

        self.stdout.write(self.style.SUCCESS('\n[OK] Import termine avec succes!\n'))
