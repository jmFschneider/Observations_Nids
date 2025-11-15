"""
Script de vérification et import des communes déléguées depuis l'API geo.api.gouv.fr

Ce script :
1. Récupère toutes les communes déléguées de France via l'API
2. Vérifie si elles sont présentes dans la base de données
3. Ajoute les communes manquantes avec toutes les informations disponibles
"""

import requests
import sys
from django.core.management.base import BaseCommand
from django.db import transaction
from geo.models import AncienneCommune, CommuneFrance


class Command(BaseCommand):
    help = "Vérifie et importe les communes déléguées manquantes depuis l'API geo.api.gouv.fr"

    API_BASE_URL = "https://geo.api.gouv.fr"

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Mode simulation : affiche ce qui serait fait sans modifier la base',
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Affiche plus de détails',
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=0,
            help='Limite le nombre de communes à traiter (0 = illimité)',
        )

    def handle(self, *args, **options):
        self.dry_run = options['dry_run']
        self.verbose = options['verbose']
        self.limit = options['limit']

        if self.dry_run:
            self.stdout.write(self.style.WARNING("=== MODE SIMULATION (dry-run) ===\n"))

        # Statistiques
        self.stats = {
            'total_api': 0,
            'deja_presentes': 0,
            'ajoutees': 0,
            'communes_nouvelles_creees': 0,
            'communes_nouvelles_manquantes': 0,
            'erreurs': 0,
        }

        # Cache pour les communes nouvelles
        self.cache_communes_nouvelles = {}

        # Étape 1 : Récupérer les communes déléguées depuis l'API
        self.stdout.write("Récupération des communes déléguées depuis l'API geo.api.gouv.fr...")
        communes_deleguees = self.recuperer_communes_deleguees()

        if not communes_deleguees:
            self.stdout.write(self.style.ERROR("Impossible de récupérer les données de l'API"))
            return

        self.stats['total_api'] = len(communes_deleguees)
        self.stdout.write(f"Trouvé {len(communes_deleguees)} communes déléguées dans l'API\n")

        # Étape 2 : Vérifier lesquelles sont absentes de la BDD
        self.stdout.write("Vérification des communes manquantes...")
        codes_insee_existants = set(
            AncienneCommune.objects.values_list('code_insee', flat=True)
        )
        self.stdout.write(f"Actuellement {len(codes_insee_existants)} anciennes communes en BDD\n")

        # Étape 3 : Traiter les communes manquantes
        communes_a_traiter = [
            c for c in communes_deleguees
            if c.get('code') not in codes_insee_existants
        ]

        if self.limit > 0:
            communes_a_traiter = communes_a_traiter[:self.limit]

        self.stdout.write(f"Communes déléguées à ajouter : {len(communes_a_traiter)}\n")

        if not communes_a_traiter:
            self.stdout.write(self.style.SUCCESS("Base de données à jour ! Aucune commune à ajouter."))
            self.afficher_statistiques()
            return

        # Traitement avec transaction
        if not self.dry_run:
            with transaction.atomic():
                self.traiter_communes(communes_a_traiter)
        else:
            self.traiter_communes(communes_a_traiter)

        self.afficher_statistiques()

    def recuperer_communes_deleguees(self):
        """Récupère toutes les communes déléguées depuis l'API"""
        try:
            params = {
                'fields': 'nom,code,chefLieu,centre,codesPostaux'
            }
            response = requests.get(
                f"{self.API_BASE_URL}/communes_associees_deleguees",
                params=params,
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            self.stdout.write(self.style.ERROR(f"Erreur API: {e}"))
            return None

    def recuperer_info_commune_nouvelle(self, code_insee):
        """Récupère les informations complètes d'une commune nouvelle"""
        if code_insee in self.cache_communes_nouvelles:
            return self.cache_communes_nouvelles[code_insee]

        try:
            params = {
                'fields': 'nom,code,codesPostaux,departement,region,population,surface,centre'
            }
            response = requests.get(
                f"{self.API_BASE_URL}/communes/{code_insee}",
                params=params,
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            self.cache_communes_nouvelles[code_insee] = data
            return data
        except requests.exceptions.RequestException as e:
            if self.verbose:
                self.stdout.write(
                    self.style.WARNING(f"  Impossible de récupérer commune {code_insee}: {e}")
                )
            return None

    def traiter_communes(self, communes):
        """Traite la liste des communes déléguées à ajouter"""
        for i, commune_deleguee in enumerate(communes, 1):
            if i % 100 == 0:
                self.stdout.write(f"Progression : {i}/{len(communes)}")

            self.traiter_une_commune(commune_deleguee)

    def traiter_une_commune(self, commune_deleguee):
        """Traite une commune déléguée"""
        code_insee_deleguee = commune_deleguee.get('code')
        nom_deleguee = commune_deleguee.get('nom', 'Inconnu')
        code_chef_lieu = commune_deleguee.get('chefLieu')

        if not code_chef_lieu:
            if self.verbose:
                self.stdout.write(
                    self.style.WARNING(f"  Pas de chef-lieu pour {nom_deleguee}")
                )
            self.stats['erreurs'] += 1
            return

        # Vérifier si la commune nouvelle existe dans CommuneFrance
        try:
            commune_actuelle = CommuneFrance.objects.get(code_insee=code_chef_lieu)
        except CommuneFrance.DoesNotExist:
            # La commune nouvelle n'existe pas, essayer de la créer
            commune_actuelle = self.creer_commune_nouvelle(code_chef_lieu)
            if not commune_actuelle:
                self.stats['communes_nouvelles_manquantes'] += 1
                if self.verbose:
                    self.stdout.write(
                        self.style.WARNING(
                            f"  Commune nouvelle {code_chef_lieu} introuvable pour {nom_deleguee}"
                        )
                    )
                return

        # Extraire les coordonnées GPS
        latitude = None
        longitude = None
        if 'centre' in commune_deleguee and 'coordinates' in commune_deleguee['centre']:
            # L'API renvoie [longitude, latitude]
            coords = commune_deleguee['centre']['coordinates']
            longitude = coords[0]
            latitude = coords[1]

        # Extraire le code postal
        code_postal = ''
        if 'codesPostaux' in commune_deleguee and commune_deleguee['codesPostaux']:
            code_postal = commune_deleguee['codesPostaux'][0]

        # Créer l'ancienne commune
        if not self.dry_run:
            try:
                AncienneCommune.objects.create(
                    nom=nom_deleguee,
                    code_insee=code_insee_deleguee,
                    code_postal=code_postal,
                    departement=commune_actuelle.departement,
                    code_departement=commune_actuelle.code_departement,
                    latitude=latitude,
                    longitude=longitude,
                    altitude=None,  # Non disponible via l'API
                    commune_actuelle=commune_actuelle,
                    date_fusion=None,  # Non disponible via cette API
                    commentaire=f"Importé depuis API geo.api.gouv.fr (commune déléguée de {commune_actuelle.nom})",
                )
                self.stats['ajoutees'] += 1

                if self.verbose:
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"  + {nom_deleguee} ({code_insee_deleguee}) -> {commune_actuelle.nom}"
                        )
                    )
            except Exception as e:
                self.stats['erreurs'] += 1
                self.stdout.write(
                    self.style.ERROR(f"  Erreur création {nom_deleguee}: {e}")
                )
        else:
            self.stats['ajoutees'] += 1
            if self.verbose:
                coords_str = f"({latitude}, {longitude})" if latitude else "(pas de coords)"
                self.stdout.write(
                    f"  [SIMULATION] + {nom_deleguee} ({code_insee_deleguee}) "
                    f"-> {commune_actuelle.nom} {coords_str}"
                )

    def creer_commune_nouvelle(self, code_insee):
        """Crée une commune nouvelle dans CommuneFrance si nécessaire"""
        info = self.recuperer_info_commune_nouvelle(code_insee)
        if not info:
            return None

        if self.dry_run:
            if self.verbose:
                self.stdout.write(
                    f"  [SIMULATION] Création commune nouvelle : {info.get('nom')} ({code_insee})"
                )
            self.stats['communes_nouvelles_creees'] += 1
            # Retourner un objet factice pour continuer la simulation
            return CommuneFrance(
                code_insee=code_insee,
                nom=info.get('nom', 'Inconnu'),
                departement=info.get('departement', {}).get('nom', 'Inconnu'),
                code_departement=info.get('departement', {}).get('code', '00'),
            )

        # Extraire les données
        try:
            nom = info.get('nom', 'Inconnu')
            departement_info = info.get('departement', {})
            region_info = info.get('region', {})

            # Coordonnées
            latitude = 0.0
            longitude = 0.0
            if 'centre' in info and 'coordinates' in info['centre']:
                longitude = info['centre']['coordinates'][0]
                latitude = info['centre']['coordinates'][1]

            # Code postal (premier de la liste)
            code_postal = '00000'
            if 'codesPostaux' in info and info['codesPostaux']:
                code_postal = info['codesPostaux'][0]

            # Créer la commune
            commune = CommuneFrance.objects.create(
                nom=nom,
                code_insee=code_insee,
                code_postal=code_postal,
                departement=departement_info.get('nom', 'Inconnu'),
                code_departement=departement_info.get('code', '00'),
                region=region_info.get('nom', ''),
                latitude=latitude,
                longitude=longitude,
                altitude=None,
                population=info.get('population'),
                superficie=info.get('surface', 0) / 100 if info.get('surface') else None,  # hectares -> km²
                source_ajout='api_geo',
                commentaire="Créée automatiquement lors de l'import des communes déléguées",
            )

            self.stats['communes_nouvelles_creees'] += 1
            if self.verbose:
                self.stdout.write(
                    self.style.SUCCESS(f"  ++ Commune nouvelle créée : {nom} ({code_insee})")
                )

            return commune

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"  Erreur création commune nouvelle {code_insee}: {e}")
            )
            return None

    def afficher_statistiques(self):
        """Affiche les statistiques finales"""
        self.stdout.write(
            self.style.SUCCESS(
                f"\n{'='*60}\n"
                f"RÉSULTATS\n"
                f"{'='*60}\n"
                f"Communes déléguées dans l'API    : {self.stats['total_api']}\n"
                f"Anciennes communes ajoutées      : {self.stats['ajoutees']}\n"
                f"Communes nouvelles créées        : {self.stats['communes_nouvelles_creees']}\n"
                f"Communes nouvelles introuvables  : {self.stats['communes_nouvelles_manquantes']}\n"
                f"Erreurs                          : {self.stats['erreurs']}\n"
                f"{'='*60}"
            )
        )

        if self.dry_run:
            self.stdout.write(
                self.style.WARNING("\nMODE SIMULATION - Aucune modification effectuée")
            )
            self.stdout.write("Relancez sans --dry-run pour appliquer les changements")
