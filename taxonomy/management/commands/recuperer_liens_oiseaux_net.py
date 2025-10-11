"""
Commande Django pour récupérer automatiquement les liens oiseaux.net pour chaque espèce.

Usage:
    python manage.py recuperer_liens_oiseaux_net
    python manage.py recuperer_liens_oiseaux_net --force  # Mettre à jour même celles qui ont déjà un lien
    python manage.py recuperer_liens_oiseaux_net --limit 10  # Tester sur 10 espèces
    python manage.py recuperer_liens_oiseaux_net --dry-run  # Simuler sans modifier la base
    python manage.py recuperer_liens_oiseaux_net --delay 1.5
    
    
    
[ECHECS] Especes non trouvees:
============================================================
  - Oie de taïga (Anser fabalis)
  - Oie de toundra (Anser serrirostris Gould, 1852)
  - Engoulevent d’Amérique (Chordeiles minor)
  - Gallinule poule-d'eau (Gallinula chloropus)
  - Guignard d'Eurasie (Eudromias morinellus)
  - Gravelot asiatique (Anarhynchus asiaticus)
  - Gravelot tibétain (Anarhynchus atrifrons)
  - Chevalier culblanc (Tringa ochropus Linnaeus, 1758)
  - Albatros à bec jaune (Thalassarche chlororhynchos)
  - Puffin cendré (Calonectris borealis)
  - Héron garde-bœufs (Ardea ibis Linnaeus, 1758)
  - Vautour percnoptère (Neophron percnopterus)
  - Circaète Jean-le-blanc (Circaetus gallicus)
  - Busard Saint-Martin (Circus cyaneus)
  - Petit-duc scops (Otus scops)
  - Hibou moyen-duc (Asio otus)
  - Grand-duc d'Europe (Bubo bubo)
  - Martin-pêcheur d'Europe (Alcedo atthis)
  - Pie-grièche grise (Lanius excubitor Linnaeus, 1758)
  - Pie-grièche méridionale (Lanius meridionalis Temminck, 1820)
  - Pie-grièche masquée (Lanius nubicus Lichtenstein, MHK, 1823)
  - Pie-grièche à poitrine rose (Lanius minor Gmelin, JF, 1788)
  - Pie-grièche à tête rousse (Lanius senator Linnaeus, 1758)
  - Pie-grièche isabelle (Lanius isabellinus Hemprich & Ehrenberg, 1833)
  - Pie-grièche écorcheur (Lanius collurio Linnaeus, 1758)
  - Pie-grièche du Turkestan (Lanius phoenicuroides)
  - Pie-grièche brune (Lanius cristatus Linnaeus, 1758)
  - Pouillot à pattes sombres (Phylloscopus plumbeitarsus Swinhoe, 1861)
  - Roitelet à triple bandeau (Regulus ignicapilla)
  - Gobemouche à demi-collier (Ficedula semitorquata)
  - Bergeronnette orientale (Motacilla tschutschensis Gmelin, JF, 1789)
  - Pinson africain (Fringilla spodiogenys)
  - Grosbec casse-noyaux (Coccothraustes coccothraustes)
  - Bec-croisé perroquet (Loxia pytyopsittacus Borkhausen, 1793)
  - Bec-croisé des sapins (Loxia curvirostra Linnaeus, 1758)
  - Bec-croisé bifascié (Loxia leucoptera Gmelin, JF, 1789)
  - Oriole de Baltimore (Icterus galbula)
"""

import re
import time
import unicodedata
from urllib.parse import quote_plus

import requests
from bs4 import BeautifulSoup
from django.core.management.base import BaseCommand

from taxonomy.models import Espece


class Command(BaseCommand):
    help = "Récupère automatiquement les liens oiseaux.net pour toutes les espèces"

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Mettre à jour même les espèces qui ont déjà un lien',
        )
        parser.add_argument(
            '--limit',
            type=int,
            help='Limiter à N espèces (pour tests)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Simuler sans modifier la base de données',
        )
        parser.add_argument(
            '--delay',
            type=float,
            default=1.0,
            help='Délai en secondes entre chaque requête (défaut: 1.0)',
        )

    def handle(self, *args, **options):
        force = options['force']
        limit = options['limit']
        dry_run = options['dry_run']
        delay = options['delay']

        # Filtrer les espèces (toujours exclure celles sans nom scientifique)
        especes_base = Espece.objects.exclude(nom_scientifique='').exclude(nom_scientifique__isnull=True)

        if force:
            especes = especes_base
            self.stdout.write(self.style.WARNING(
                "[Mode FORCE] Mise a jour de toutes les especes, meme celles avec lien existant"
            ))
        else:
            especes = especes_base.filter(lien_oiseau_net__isnull=True) | especes_base.filter(lien_oiseau_net='')
            self.stdout.write(self.style.SUCCESS(
                "Mise a jour uniquement des especes sans lien"
            ))

        if limit:
            especes = especes[:limit]
            self.stdout.write(self.style.WARNING(f"[Mode TEST] Limité à {limit} espèces"))

        total = especes.count()

        if total == 0:
            self.stdout.write(self.style.SUCCESS(
                "\nAucune espèce à traiter. Toutes les espèces ont déjà un lien !"
            ))
            return

        if dry_run:
            self.stdout.write(self.style.WARNING("[Mode DRY-RUN] Simulation, aucune modification"))

        self.stdout.write(self.style.SUCCESS(f"\nTraitement de {total} espèce(s)...\n"))

        stats = {
            'success_direct': 0,
            'success_google': 0,
            'failed': 0,
            'skipped': 0,
        }

        failed_species = []

        for i, espece in enumerate(especes, start=1):
            # Barre de progression
            progress = f"[{i}/{total}]"
            self.stdout.write(f"\n{progress} {espece.nom} ({espece.nom_scientifique})")

            # Si pas de nom scientifique, skip
            if not espece.nom_scientifique:
                self.stdout.write(self.style.WARNING("  [!] Pas de nom scientifique, ignore"))
                stats['skipped'] += 1
                continue

            # Méthode 1 : Construction depuis le nom français (PRIORITAIRE)
            url_nom_francais = self.construire_url_depuis_nom_francais(espece.nom)
            self.stdout.write(f"  -> Test URL nom francais: {url_nom_francais}")

            if self.verifier_url_existe(url_nom_francais):
                self.stdout.write(self.style.SUCCESS("  [OK] URL nom francais valide !"))
                if not dry_run:
                    espece.lien_oiseau_net = url_nom_francais
                    espece.save()
                stats['success_direct'] += 1
            else:
                self.stdout.write(self.style.WARNING("  [X] URL nom francais invalide"))

                # Méthode 2 : Construction depuis le nom scientifique (fallback)
                url_nom_sci = self.construire_url_depuis_nom_scientifique(espece.nom_scientifique)
                self.stdout.write(f"  -> Test URL nom scientifique: {url_nom_sci}")

                if self.verifier_url_existe(url_nom_sci):
                    self.stdout.write(self.style.SUCCESS("  [OK] URL nom scientifique valide !"))
                    if not dry_run:
                        espece.lien_oiseau_net = url_nom_sci
                        espece.save()
                    stats['success_direct'] += 1
                else:
                    self.stdout.write(self.style.WARNING("  [X] URL nom scientifique invalide"))

                    # Méthode 3 : Recherche Google (dernier recours)
                    self.stdout.write("  -> Recherche Google...")
                    url_google = self.chercher_via_google(espece.nom_scientifique, espece.nom)

                    if url_google:
                        self.stdout.write(self.style.SUCCESS(f"  [OK] Trouve via Google: {url_google}"))
                        if not dry_run:
                            espece.lien_oiseau_net = url_google
                            espece.save()
                        stats['success_google'] += 1
                    else:
                        self.stdout.write(self.style.ERROR("  [X] Echec Google"))
                        stats['failed'] += 1
                        failed_species.append(f"{espece.nom} ({espece.nom_scientifique})")

            # Délai entre requêtes pour ne pas surcharger les serveurs
            if i < total:
                time.sleep(delay)

        # Résumé final
        self.stdout.write("\n" + "="*60)
        self.stdout.write(self.style.SUCCESS("\n[RESUME]"))
        self.stdout.write("="*60)
        self.stdout.write(f"Total traite      : {total}")
        self.stdout.write(self.style.SUCCESS(f"[OK] Succes direct   : {stats['success_direct']}"))
        self.stdout.write(self.style.SUCCESS(f"[OK] Succes Google   : {stats['success_google']}"))
        self.stdout.write(self.style.WARNING(f"[!] Ignores         : {stats['skipped']}"))
        self.stdout.write(self.style.ERROR(f"[X] Echecs          : {stats['failed']}"))

        total_success = stats['success_direct'] + stats['success_google']
        if total > 0:
            taux_reussite = (total_success / total) * 100
            self.stdout.write(f"\nTaux de réussite : {taux_reussite:.1f}%")

        if failed_species:
            self.stdout.write("\n" + "="*60)
            self.stdout.write(self.style.ERROR("\n[ECHECS] Especes non trouvees:"))
            self.stdout.write("="*60)
            for species in failed_species:
                self.stdout.write(f"  - {species}")
            self.stdout.write("\n[CONSEIL] Verifiez manuellement ces especes sur oiseaux.net")

        if dry_run:
            self.stdout.write("\n" + "="*60)
            self.stdout.write(self.style.WARNING(
                "Mode DRY-RUN : Aucune modification n'a été enregistrée"
            ))
            self.stdout.write(self.style.WARNING(
                "Relancez sans --dry-run pour appliquer les modifications"
            ))

        self.stdout.write("\n" + "="*60)
        self.stdout.write(self.style.SUCCESS("\n[OK] Traitement termine !\n"))

    def construire_url_depuis_nom_francais(self, nom_francais):
        """
        Construit l'URL oiseaux.net depuis le nom français.
        Exemple: "Bernache cravant" → "https://www.oiseaux.net/oiseaux/bernache.cravant.html"

        Oiseaux.net utilise le nom vernaculaire français en minuscules avec points.
        """
        # Nettoyer le nom français
        nom_clean = nom_francais.strip().lower()

        # Normaliser les caractères accentués
        nom_clean = unicodedata.normalize('NFD', nom_clean)
        nom_clean = ''.join(c for c in nom_clean if unicodedata.category(c) != 'Mn')

        # Remplacer les espaces et apostrophes par des points
        nom_url = nom_clean.replace(' ', '.').replace("'", '.')

        # Supprimer les caractères spéciaux (garder seulement lettres, chiffres et points)
        nom_url = re.sub(r'[^\w\.]', '', nom_url)

        # Supprimer les points multiples consécutifs
        nom_url = re.sub(r'\.+', '.', nom_url)

        # Supprimer les points en début/fin
        nom_url = nom_url.strip('.')

        return f"https://www.oiseaux.net/oiseaux/{nom_url}.html"

    def construire_url_depuis_nom_scientifique(self, nom_scientifique):
        """
        Construit l'URL oiseaux.net depuis le nom scientifique (fallback).
        Exemple: "Passer domesticus" → "https://www.oiseaux.net/oiseaux/passer.domesticus.html"
        """
        # Nettoyer le nom scientifique
        nom_clean = nom_scientifique.strip().lower()

        # Remplacer les espaces par des points
        nom_url = nom_clean.replace(' ', '.')

        # Supprimer les caractères spéciaux
        nom_url = re.sub(r'[^\w\.]', '', nom_url)

        return f"https://www.oiseaux.net/oiseaux/{nom_url}.html"

    def verifier_url_existe(self, url):
        """
        Vérifie qu'une URL existe et retourne un contenu valide.
        """
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.head(url, headers=headers, timeout=10, allow_redirects=True)

            # Accepter 200 (OK) et 301/302 (redirections)
            return response.status_code in [200, 301, 302]
        except requests.RequestException:
            return False

    def chercher_via_google(self, nom_scientifique, nom_francais):
        """
        Recherche l'URL oiseaux.net via Google.
        """
        try:
            # Construction de la requête Google
            query = f"{nom_scientifique} {nom_francais} site:oiseaux.net"
            url_google = f"https://www.google.com/search?q={quote_plus(query)}"

            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }

            response = requests.get(url_google, headers=headers, timeout=10)
            response.raise_for_status()

            # Parser le HTML de la page de résultats
            soup = BeautifulSoup(response.text, 'html.parser')

            # Chercher les liens dans les résultats Google
            for link in soup.find_all('a'):
                href = link.get('href', '')

                # Extraire l'URL réelle depuis le lien Google
                if '/url?q=' in href:
                    # Format Google: /url?q=https://www.oiseaux.net/...&sa=...
                    match = re.search(r'/url\?q=(https://www\.oiseaux\.net[^&]+)', href)
                    if match:
                        url_candidate = match.group(1)

                        # Vérifier que cette URL existe
                        if self.verifier_url_existe(url_candidate):
                            return url_candidate

            # Méthode alternative : chercher directement les liens oiseaux.net
            for link in soup.find_all('a', href=re.compile(r'oiseaux\.net')):
                href = link.get('href', '')
                if 'oiseaux.net/oiseaux/' in href:
                    # Nettoyer l'URL
                    url_clean = href.split('&')[0].replace('/url?q=', '')
                    if self.verifier_url_existe(url_clean):
                        return url_clean

            return None

        except requests.RequestException:
            return None

    def normaliser_nom_scientifique(self, nom):
        """
        Normalise le nom scientifique pour la recherche.
        - Supprime les sous-espèces (garde seulement genre + espèce)
        - Exemple: "Passer domesticus domesticus" → "Passer domesticus"
        """
        parts = nom.strip().split()
        if len(parts) >= 2:
            return f"{parts[0]} {parts[1]}"
        return nom
