#!/usr/bin/env python
"""
Script pour vérifier les fichiers orphelins détectés.

Ce script lit le rapport généré par find_orphan_files.py et effectue
des recherches approfondies pour déterminer si les fichiers sont vraiment orphelins.

Génère un rapport Markdown avec un tableau de vérification.
"""

import os
import re
import json
from pathlib import Path
from typing import List, Dict, Set, Optional
from dataclasses import dataclass

# Configuration
BASE_DIR = Path(__file__).resolve().parent.parent
REPORT_PATH = BASE_DIR / 'scripts' / 'rapport_fichiers_orphelins.md'
OUTPUT_PATH = BASE_DIR / 'scripts' / 'verification_orphelins.md'
EXCEPTIONS_PATH = BASE_DIR / 'scripts' / 'exceptions_orphelins.json'

IGNORE_DIRS = {
    '.git', '.venv', '__pycache__', '.pytest_cache', '.mypy_cache',
    'migrations', 'htmlcov', '.ruff_cache', 'staticfiles', 'media',
    '.idea', '.github', '.claude', 'node_modules', 'deployment'
}


@dataclass
class FileException:
    """Exception pour un fichier orphelin avec justification."""
    file: str
    reason: str
    category: str


@dataclass
class VerificationResult:
    """Résultat de vérification pour un fichier."""
    filename: str
    file_type: str
    found_in_global_py: bool
    found_in_global_html: bool
    found_in_urls: bool
    found_in_views: bool
    found_in_templates: bool
    references_found: List[str]  # Liste des endroits où le fichier est référencé
    score: int
    is_orphan: bool
    exception: Optional[FileException] = None  # Exception si connue


class OrphanVerifier:
    """Classe pour vérifier les fichiers orphelins."""

    def __init__(self):
        self.orphan_files: List[str] = []
        self.all_python_files: List[Path] = []
        self.all_html_files: List[Path] = []
        self.urls_files: List[Path] = []
        self.views_files: List[Path] = []
        self.verification_results: List[VerificationResult] = []
        self.exceptions: Dict[str, FileException] = {}  # key = filepath
        self.load_exceptions()

    def load_exceptions(self):
        """Charge le fichier JSON des exceptions."""
        if EXCEPTIONS_PATH.exists():
            try:
                with open(EXCEPTIONS_PATH, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for exc in data.get('exceptions', []):
                        file_exc = FileException(
                            file=exc['file'],
                            reason=exc['reason'],
                            category=exc['category']
                        )
                        self.exceptions[exc['file']] = file_exc
                print(f"[*] {len(self.exceptions)} exception(s) chargee(s) depuis {EXCEPTIONS_PATH.name}\n")
            except Exception as e:
                print(f"[WARN] Erreur lors du chargement des exceptions : {e}\n")
        else:
            print("[*] Aucun fichier d'exceptions trouve (premiere execution)\n")

    def save_exceptions(self):
        """Sauvegarde les exceptions dans le fichier JSON."""
        data = {
            "exceptions": [
                {
                    "file": exc.file,
                    "reason": exc.reason,
                    "category": exc.category
                }
                for exc in self.exceptions.values()
            ]
        }

        try:
            with open(EXCEPTIONS_PATH, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f"\n[OK] Exceptions sauvegardees dans {EXCEPTIONS_PATH}")
        except Exception as e:
            print(f"\n[ERROR] Erreur lors de la sauvegarde : {e}")

    def collect_project_files(self):
        """Collecte tous les fichiers du projet pour les recherches."""
        print("[*] Collecte des fichiers du projet...")

        for root, dirs, files in os.walk(BASE_DIR):
            # Ignorer certains dossiers
            dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]

            root_path = Path(root)

            for file in files:
                file_path = root_path / file

                if file.endswith('.py'):
                    self.all_python_files.append(file_path)
                    if file == 'urls.py':
                        self.urls_files.append(file_path)
                    if 'views' in file or 'views' in str(file_path):
                        self.views_files.append(file_path)
                elif file.endswith('.html'):
                    self.all_html_files.append(file_path)

        print(f"   [OK] {len(self.all_python_files)} fichiers Python collectes")
        print(f"   [OK] {len(self.urls_files)} fichiers urls.py")
        print(f"   [OK] {len(self.views_files)} fichiers views.py")
        print(f"   [OK] {len(self.all_html_files)} fichiers HTML")

    def parse_markdown_report(self) -> Dict[str, List[str]]:
        """Parse le rapport Markdown pour extraire les fichiers orphelins."""
        print("\n[*] Lecture du rapport Markdown...")

        if not REPORT_PATH.exists():
            print(f"[ERROR] Rapport non trouve : {REPORT_PATH}")
            print("Veuillez d'abord executer find_orphan_files.py")
            return {}

        with open(REPORT_PATH, 'r', encoding='utf-8') as f:
            content = f.read()

        orphans = {
            'python': [],
            'html': [],
            'css': [],
            'js': []
        }

        # Parser le Markdown pour extraire les fichiers
        current_section = None

        for line in content.split('\n'):
            # Détecter les sections
            if line.startswith('## PYTHON'):
                current_section = 'python'
            elif line.startswith('## HTML'):
                current_section = 'html'
            elif line.startswith('## CSS'):
                current_section = 'css'
            elif line.startswith('## JS'):
                current_section = 'js'
            elif line.startswith('##'):
                current_section = None

            # Extraire les fichiers (lignes commençant par "- `")
            if current_section and line.startswith('- `'):
                # Extraire le chemin entre backticks
                match = re.search(r'`([^`]+)`', line)
                if match:
                    filepath = match.group(1)
                    orphans[current_section].append(filepath)

        total = sum(len(files) for files in orphans.values())
        print(f"   [OK] {total} fichiers orphelins a verifier")

        return orphans

    def search_in_files(self, search_term: str, files: List[Path]) -> List[str]:
        """Recherche un terme dans une liste de fichiers."""
        references = []

        for file_path in files:
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()

                    if search_term in content:
                        # Compter les occurrences
                        count = content.count(search_term)
                        relative_path = file_path.relative_to(BASE_DIR)
                        references.append(f"{relative_path} ({count}x)")

            except Exception:
                pass

        return references

    def verify_file(self, filepath: str, file_type: str) -> VerificationResult:
        """Vérifie si un fichier est vraiment orphelin."""
        # Extraire le nom du fichier (sans extension pour certaines recherches)
        filename = Path(filepath).name
        filename_no_ext = Path(filepath).stem

        # Initialiser les résultats
        found_in_global_py = False
        found_in_global_html = False
        found_in_urls = False
        found_in_views = False
        found_in_templates = False
        all_references = []

        # 1. Recherche globale dans les fichiers Python
        py_refs = self.search_in_files(filename, self.all_python_files)
        if py_refs:
            found_in_global_py = True
            all_references.extend([f"Python: {ref}" for ref in py_refs[:3]])  # Max 3 refs

        # Recherche aussi par nom sans extension (pour imports Python)
        if file_type == 'python':
            py_refs_no_ext = self.search_in_files(filename_no_ext, self.all_python_files)
            if py_refs_no_ext and not found_in_global_py:
                found_in_global_py = True
                all_references.extend([f"Python: {ref}" for ref in py_refs_no_ext[:3]])

        # 2. Recherche globale dans les fichiers HTML
        html_refs = self.search_in_files(filename, self.all_html_files)
        if html_refs:
            found_in_global_html = True
            all_references.extend([f"HTML: {ref}" for ref in html_refs[:3]])

        # 3. Recherche spécifique dans urls.py
        urls_refs = self.search_in_files(filename_no_ext, self.urls_files)
        if urls_refs:
            found_in_urls = True
            all_references.extend([f"URLs: {ref}" for ref in urls_refs[:2]])

        # 4. Recherche spécifique dans views.py
        views_refs = self.search_in_files(filename, self.views_files)
        if views_refs:
            found_in_views = True
            all_references.extend([f"Views: {ref}" for ref in views_refs[:2]])

        # 5. Pour les templates HTML, recherche dans templates (include/extends)
        if file_type == 'html':
            template_refs = self.search_in_files(filename, self.all_html_files)
            if template_refs:
                found_in_templates = True
                # Déjà compté dans global_html, mais on marque quand même

        # Calculer le score
        score = sum([
            found_in_global_py,
            found_in_global_html,
            found_in_urls,
            found_in_views,
            found_in_templates
        ])

        # Déterminer si vraiment orphelin
        is_orphan = score == 0

        # Vérifier si c'est une exception connue
        exception = self.exceptions.get(filepath, None)

        return VerificationResult(
            filename=filepath,
            file_type=file_type,
            found_in_global_py=found_in_global_py,
            found_in_global_html=found_in_global_html,
            found_in_urls=found_in_urls,
            found_in_views=found_in_views,
            found_in_templates=found_in_templates,
            references_found=all_references,
            score=score,
            is_orphan=is_orphan,
            exception=exception
        )

    def get_file_dates(self, filepath: str) -> tuple[str, str]:
        """Récupère les dates de création et modification d'un fichier."""
        from datetime import datetime
        import os

        # Convertir le chemin relatif en absolu
        full_path = BASE_DIR / filepath.replace('/', os.sep)

        try:
            if full_path.exists():
                stat = full_path.stat()

                # Date de création (Windows: st_ctime, Unix: st_birthtime si disponible)
                created = datetime.fromtimestamp(stat.st_ctime)
                created_str = created.strftime('%Y-%m-%d')

                # Date de modification
                modified = datetime.fromtimestamp(stat.st_mtime)
                modified_str = modified.strftime('%Y-%m-%d')

                return created_str, modified_str
            else:
                return "N/A", "N/A"
        except Exception:
            return "N/A", "N/A"

    def verify_all_orphans(self, orphans: Dict[str, List[str]]):
        """Vérifie tous les fichiers orphelins détectés."""
        print("\n[*] Verification des fichiers orphelins...\n")

        total_files = sum(len(files) for files in orphans.values())
        current = 0

        for file_type, files in orphans.items():
            for filepath in files:
                current += 1
                print(f"   [{current}/{total_files}] Verification de {filepath}...")

                result = self.verify_file(filepath, file_type)

                # Afficher l'exception si elle existe
                if result.exception:
                    print(f"       [i] Exception connue : \"{result.exception.reason}\" ({result.exception.category})")
                elif result.is_orphan:
                    print(f"       [!] Aucune reference trouvee (Score {result.score}/5)")

                self.verification_results.append(result)

        print(f"\n[OK] Verification terminee !")

    def interactive_exceptions_update(self):
        """Mode interactif pour documenter/modifier les exceptions."""
        orphans_list = [r for r in self.verification_results if r.is_orphan]

        if not orphans_list:
            print("\n[*] Aucun fichier orphelin a documenter.")
            return

        exceptions_count = sum(1 for r in orphans_list if r.exception is not None)

        print("\n" + "="*80)
        if exceptions_count > 0:
            print(f"{len(orphans_list)} fichiers vraiment orphelins (dont {exceptions_count} exception(s) connue(s)).")
        else:
            print(f"{len(orphans_list)} fichiers vraiment orphelins detectes.")
        print("="*80)

        response = input("\nVoulez-vous mettre a jour les exceptions ? (o/n): ").strip().lower()

        if response != 'o':
            print("[*] Mise a jour des exceptions annulee.")
            return

        print("\n")
        updated = False
        files_to_delete = []  # Collecter les fichiers à supprimer

        for i, result in enumerate(orphans_list, 1):
            print(f"[{i}/{len(orphans_list)}] {result.filename}")

            if result.exception:
                # Exception existante
                print(f'  Exception actuelle : "{result.exception.reason}" ({result.exception.category})')
                choice = input("  [m]odifier / [s]upprimer exception / [d]etruire fichier / [c]onserver : ").strip().lower()

                if choice == 'm':
                    # Modifier
                    reason = input("  Nouvelle raison : ").strip()
                    if reason:
                        print("\n  Categories disponibles:")
                        print("    1. Infrastructure")
                        print("    2. Bibliotheque externe")
                        print("    3. Inclusion dynamique")
                        print("    4. Deploiement")
                        print("    5. Autre")
                        cat_choice = input("  Categorie (1-5) : ").strip()

                        categories = {
                            '1': 'Infrastructure',
                            '2': 'Bibliotheque externe',
                            '3': 'Inclusion dynamique',
                            '4': 'Deploiement',
                            '5': 'Autre'
                        }
                        category = categories.get(cat_choice, 'Autre')

                        self.exceptions[result.filename] = FileException(
                            file=result.filename,
                            reason=reason,
                            category=category
                        )
                        result.exception = self.exceptions[result.filename]
                        print(f"  [OK] Exception modifiee\n")
                        updated = True
                    else:
                        print("  [!] Raison vide, modification annulee\n")

                elif choice == 's':
                    # Supprimer l'exception (pas le fichier)
                    if result.filename in self.exceptions:
                        del self.exceptions[result.filename]
                        result.exception = None
                        print(f"  [OK] Exception supprimee\n")
                        updated = True

                elif choice == 'd':
                    # Marquer pour suppression/archivage
                    files_to_delete.append(result.filename)
                    # Retirer de la liste des exceptions si présent
                    if result.filename in self.exceptions:
                        del self.exceptions[result.filename]
                        result.exception = None
                        updated = True
                    print(f"  [OK] Marque pour suppression\n")

                elif choice == 'c':
                    # Conserver
                    print(f"  [OK] Exception conservee\n")

                else:
                    print(f"  [!] Choix invalide, exception conservee\n")

            else:
                # Pas d'exception
                print("  Exception actuelle : Aucune")
                choice = input("  Marquer comme exception ou supprimer ? (o/n/d): ").strip().lower()

                if choice == 'o':
                    # Marquer comme exception
                    reason = input("  Raison : ").strip()
                    if reason:
                        print("\n  Categories disponibles:")
                        print("    1. Infrastructure")
                        print("    2. Bibliotheque externe")
                        print("    3. Inclusion dynamique")
                        print("    4. Deploiement")
                        print("    5. Autre")
                        cat_choice = input("  Categorie (1-5) : ").strip()

                        categories = {
                            '1': 'Infrastructure',
                            '2': 'Bibliotheque externe',
                            '3': 'Inclusion dynamique',
                            '4': 'Deploiement',
                            '5': 'Autre'
                        }
                        category = categories.get(cat_choice, 'Autre')

                        self.exceptions[result.filename] = FileException(
                            file=result.filename,
                            reason=reason,
                            category=category
                        )
                        result.exception = self.exceptions[result.filename]
                        print(f"  [OK] Exception ajoutee\n")
                        updated = True
                    else:
                        print("  [!] Raison vide, ajout annule\n")

                elif choice == 'd':
                    # Marquer pour suppression/archivage
                    files_to_delete.append(result.filename)
                    print(f"  [OK] Marque pour suppression\n")

                else:
                    # Ignorer (n ou autre)
                    print(f"  [!] Ignore\n")

        # Sauvegarder les exceptions si modifiées
        if updated:
            self.save_exceptions()
        else:
            print("[*] Aucune modification des exceptions.")

        # Archiver et supprimer les fichiers marqués
        if files_to_delete:
            print(f"\n[!] {len(files_to_delete)} fichier(s) marque(s) pour suppression.")
            print("[!] Les fichiers seront archives dans .archived_orphans/")
            confirm = input("Confirmer l'archivage et la suppression ? (o/n): ").strip().lower()

            if confirm == 'o':
                try:
                    import sys
                    sys.path.insert(0, str(BASE_DIR / 'scripts'))
                    from archiver_orphelins import archive_orphans

                    archived, deleted = archive_orphans(files_to_delete, dry_run=False)
                    print(f"\n[OK] {archived} fichier(s) archive(s) et {deleted} supprime(s).")
                except Exception as e:
                    print(f"[ERROR] Erreur lors de l'archivage : {e}")
            else:
                print("[*] Archivage annule.")
        else:
            print("\n[*] Aucun fichier marque pour suppression.")

    def generate_markdown_report(self):
        """Génère le rapport Markdown avec tableau de vérification."""
        from datetime import datetime

        print("\n[*] Generation du rapport Markdown...")

        lines = []
        lines.append("# Vérification des Fichiers Orphelins\n")
        lines.append(f"**Date de génération** : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        lines.append("---\n\n")

        # Statistiques
        total = len(self.verification_results)
        vraiment_orphelins = sum(1 for r in self.verification_results if r.is_orphan)
        faux_positifs = total - vraiment_orphelins

        lines.append("## 📊 Résumé\n\n")
        lines.append(f"- **Total de fichiers vérifiés** : {total}\n")
        lines.append(f"- **Vraiment orphelins** : {vraiment_orphelins} ⚠️\n")
        lines.append(f"- **Faux positifs** : {faux_positifs} ✅\n\n")

        # Tableau de vérification
        lines.append("## 📋 Tableau de Vérification\n\n")
        lines.append("| Fichier | Type | Recherche Python | Recherche HTML | Dans URLs | Dans Views | Dans Templates | Score | Exception | Verdict |\n")
        lines.append("|---------|------|------------------|----------------|-----------|------------|----------------|-------|-----------|----------|\n")

        # Trier par score (orphelins d'abord)
        sorted_results = sorted(self.verification_results, key=lambda r: (r.is_orphan, -r.score), reverse=True)

        for result in sorted_results:
            # Raccourcir le nom du fichier si trop long
            filename = result.filename
            if len(filename) > 50:
                filename = "..." + filename[-47:]

            # Récupérer les dates de création et modification
            created_date, modified_date = self.get_file_dates(result.filename)

            # Emojis pour les booléens
            py_icon = "✅" if result.found_in_global_py else "❌"
            html_icon = "✅" if result.found_in_global_html else "❌"
            urls_icon = "✅" if result.found_in_urls else "❌"
            views_icon = "✅" if result.found_in_views else "❌"
            templates_icon = "✅" if result.found_in_templates else "❌"

            # Exception
            if result.exception:
                exception_cell = f"✅<br><small>{result.exception.category}</small>"
                verdict = "🟣 **Exception connue**"
            else:
                exception_cell = "❌"
                # Verdict normal
                if result.is_orphan:
                    verdict = "🔴 **ORPHELIN**"
                elif result.score >= 3:
                    verdict = "🟢 Faux positif"
                elif result.score >= 1:
                    verdict = "🟡 À vérifier"
                else:
                    verdict = "🔴 **ORPHELIN**"

            # Créer la ligne avec le nom du fichier et les dates sur deux lignes
            file_cell = f"`{filename}`<br><small>Créé: {created_date} - Modifié: {modified_date}</small>"

            lines.append(f"| {file_cell} | {result.file_type.upper()} | {py_icon} | {html_icon} | {urls_icon} | {views_icon} | {templates_icon} | {result.score}/5 | {exception_cell} | {verdict} |\n")

        # Section exceptions connues
        exceptions_list = [r for r in sorted_results if r.exception is not None]
        if exceptions_list:
            lines.append("\n---\n\n")
            lines.append("## 🟣 Exceptions Connues\n\n")
            lines.append("Ces fichiers sont marqués comme orphelins mais ont une justification :\n\n")

            # Grouper par catégorie
            by_category: Dict[str, List[VerificationResult]] = {}
            for result in exceptions_list:
                category = result.exception.category
                if category not in by_category:
                    by_category[category] = []
                by_category[category].append(result)

            for category, results in sorted(by_category.items()):
                lines.append(f"### {category}\n\n")
                for result in results:
                    lines.append(f"- `{result.filename}` : {result.exception.reason}\n")
                lines.append("\n")

        # Section détails pour les vraiment orphelins (sans exceptions)
        vraiment_orphelins_list = [r for r in sorted_results if r.is_orphan and r.exception is None]
        if vraiment_orphelins_list:
            lines.append("\n---\n\n")
            lines.append("## 🔴 Fichiers Vraiment Orphelins\n\n")
            lines.append("Ces fichiers n'ont **aucune référence** dans le projet et **aucune justification** :\n\n")

            for result in vraiment_orphelins_list:
                lines.append(f"- `{result.filename}` ({result.file_type.upper()})\n")

        # Section détails avec références
        lines.append("\n---\n\n")
        lines.append("## 🔍 Détails des Références\n\n")
        lines.append("Fichiers avec au moins une référence :\n\n")

        for result in sorted_results:
            if not result.is_orphan and result.references_found:
                lines.append(f"### `{result.filename}`\n\n")
                for ref in result.references_found[:5]:  # Max 5 références
                    lines.append(f"- {ref}\n")
                lines.append("\n")

        # Notes
        lines.append("\n---\n\n")
        lines.append("## 📝 Légende\n\n")
        lines.append("- **Recherche Python** : Fichier mentionné dans du code Python\n")
        lines.append("- **Recherche HTML** : Fichier mentionné dans des templates HTML\n")
        lines.append("- **Dans URLs** : Fichier référencé dans urls.py\n")
        lines.append("- **Dans Views** : Fichier référencé dans views.py\n")
        lines.append("- **Dans Templates** : Template inclus/étendu par d'autres templates\n")
        lines.append("- **Score** : Nombre de types de références trouvées (sur 5)\n\n")
        lines.append("- **Exception** : Fichier marqué comme exception connue avec justification\n\n")
        lines.append("### Verdicts\n\n")
        lines.append("- 🔴 **ORPHELIN** : Aucune référence trouvée (score = 0)\n")
        lines.append("- 🟡 **À vérifier** : Peu de références (score 1-2)\n")
        lines.append("- 🟢 **Faux positif** : Plusieurs références (score ≥ 3)\n")
        lines.append("- 🟣 **Exception connue** : Fichier justifié comme nécessaire malgré l'absence de références\n")

        content = ''.join(lines)

        # Écrire le fichier
        try:
            with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"[OK] Rapport genere : {OUTPUT_PATH}\n")
        except Exception as e:
            print(f"[ERROR] Erreur lors de la generation : {e}\n")

    def run(self):
        """Lance la vérification complète."""
        print("\n" + "="*80)
        print("VERIFICATION DES FICHIERS ORPHELINS")
        print("="*80 + "\n")

        # Collecter les fichiers du projet
        self.collect_project_files()

        # Parser le rapport
        orphans = self.parse_markdown_report()

        if not orphans or sum(len(files) for files in orphans.values()) == 0:
            print("[ERROR] Aucun fichier orphelin a verifier.")
            return

        # Vérifier tous les orphelins
        self.verify_all_orphans(orphans)

        # Mode interactif pour documenter les exceptions
        self.interactive_exceptions_update()

        # Générer le rapport
        self.generate_markdown_report()

        # Afficher résumé
        total = len(self.verification_results)
        vraiment_orphelins = sum(1 for r in self.verification_results if r.is_orphan)

        print("="*80)
        print(f"TOTAL: {total} fichiers verifies")
        print(f"Vraiment orphelins: {vraiment_orphelins}")
        print(f"Faux positifs: {total - vraiment_orphelins}")
        print("="*80 + "\n")


if __name__ == '__main__':
    import os
    verifier = OrphanVerifier()
    verifier.run()
