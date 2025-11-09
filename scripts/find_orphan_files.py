#!/usr/bin/env python
"""
Script pour détecter les fichiers orphelins dans le projet Django.

Ce script analyse :
- Les imports Python
- Les templates référencés dans les vues
- Les fichiers statiques référencés dans les templates
- Les URLs

Et identifie les fichiers qui ne sont jamais référencés.
"""

import ast
import os
import re
from datetime import datetime
from pathlib import Path

# Configuration du projet
BASE_DIR = Path(__file__).resolve().parent.parent
APPS = [
    'accounts',
    'audit',
    'core',
    'geo',
    'ingest',
    'observations',
    'observations_nids',
    'review',
    'taxonomy',
]

# Fichiers et dossiers à ignorer
IGNORE_DIRS = {
    '.git',
    '.venv',
    '__pycache__',
    '.pytest_cache',
    '.mypy_cache',
    'migrations',
    'htmlcov',
    '.ruff_cache',
    'staticfiles',
    'media',
    '.idea',
    '.github',
    '.claude',
    'node_modules',
    'deployment',
    'goaccess',
    'IA_directives',
    'docs',
}

IGNORE_FILES = {
    '__init__.py',  # Toujours nécessaires
    'apps.py',  # Config Django
    'admin.py',  # Interface admin Django
    'tests.py',  # Tests
    'conftest.py',  # Config pytest
    'manage.py',  # Point d'entrée Django
    'wsgi.py',  # Déploiement
    'asgi.py',  # Déploiement
    'settings.py',  # Configuration
    'celery.py',  # Configuration Celery
    'config.py',  # Configuration
}


class OrphanFileFinder:
    """Classe pour trouver les fichiers orphelins dans le projet."""

    def __init__(self):
        self.all_python_files: set[Path] = set()
        self.all_html_files: set[Path] = set()
        self.all_css_files: set[Path] = set()
        self.all_js_files: set[Path] = set()

        self.referenced_python_files: set[Path] = set()
        self.referenced_html_files: set[Path] = set()
        self.referenced_css_files: set[Path] = set()
        self.referenced_js_files: set[Path] = set()

        self.python_imports: dict[Path, set[str]] = {}
        self.template_references: dict[Path, set[str]] = {}
        self.static_references: dict[Path, set[str]] = {}

    def should_ignore(self, path: Path) -> bool:
        """Vérifie si un chemin doit être ignoré."""
        # Ignorer les dossiers dans IGNORE_DIRS
        if any(part in IGNORE_DIRS for part in path.parts):
            return True

        # Ignorer certains fichiers spécifiques
        if path.name in IGNORE_FILES:
            return True

        # Ignorer les fichiers de test
        if path.name.startswith('test_') or path.name.endswith('_test.py'):
            return True

        # Ignorer les management commands, scripts, urls.py et models.py
        return (
            ('management' in path.parts and 'commands' in path.parts)
            or ('scripts' in path.parts and path.suffix == '.py')
            or path.name in ('urls.py', 'models.py')
        )

    def collect_all_files(self):
        """Collecte tous les fichiers du projet."""
        print("[*] Collecte de tous les fichiers...")

        for root, dirs, files in os.walk(BASE_DIR):
            # Modifier dirs en place pour ignorer certains dossiers
            dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]

            root_path = Path(root)

            for file in files:
                file_path = root_path / file

                if self.should_ignore(file_path):
                    continue

                if file.endswith('.py'):
                    self.all_python_files.add(file_path)
                elif file.endswith('.html'):
                    self.all_html_files.add(file_path)
                elif file.endswith('.css'):
                    self.all_css_files.add(file_path)
                elif file.endswith('.js'):
                    self.all_js_files.add(file_path)

        print(f"   [OK] {len(self.all_python_files)} fichiers Python")
        print(f"   [OK] {len(self.all_html_files)} fichiers HTML")
        print(f"   [OK] {len(self.all_css_files)} fichiers CSS")
        print(f"   [OK] {len(self.all_js_files)} fichiers JS")

    def parse_python_imports(self):
        """Parse les imports dans les fichiers Python."""
        print("\n[*] Analyse des imports Python...")

        for py_file in self.all_python_files:
            try:
                with open(py_file, encoding='utf-8') as f:
                    content = f.read()

                tree = ast.parse(content, filename=str(py_file))
                imports = set()

                for node in ast.walk(tree):
                    # Import simple: import module
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            imports.add(alias.name)

                    # Import from: from module import name
                    elif isinstance(node, ast.ImportFrom) and node.module:
                        imports.add(node.module)

                self.python_imports[py_file] = imports

                # Marquer les fichiers Python référencés
                for imp in imports:
                    # Convertir le module en chemin de fichier
                    parts = imp.split('.')

                    # Essayer de trouver le fichier correspondant
                    for py_candidate in self.all_python_files:
                        # Vérifier si le chemin correspond au module
                        relative_path = py_candidate.relative_to(BASE_DIR)
                        path_parts = list(relative_path.parts[:-1]) + [relative_path.stem]

                        if path_parts == parts or path_parts[-len(parts) :] == parts:
                            self.referenced_python_files.add(py_candidate)

            except Exception as e:
                print(f"   [WARN] Erreur lors du parsing de {py_file.name}: {e}")

        print(f"   [OK] {len(self.referenced_python_files)} fichiers Python référencés")

    def parse_urls_py(self):
        """Parse les fichiers urls.py pour détecter les vues utilisées."""
        print("\n[*] Analyse des urls.py...")

        # Trouver tous les fichiers urls.py
        urls_files = [f for f in self.all_python_files if f.name == 'urls.py']

        for urls_file in urls_files:
            try:
                with open(urls_file, encoding='utf-8') as f:
                    content = f.read()

                # Parser le fichier Python
                tree = ast.parse(content, filename=str(urls_file))

                # Chercher les imports de vues
                for node in ast.walk(tree):
                    # Import from: from app.views import view
                    if isinstance(node, ast.ImportFrom):
                        if node.module and 'views' in node.module:
                            module_parts = node.module.split('.')

                            # Essayer de trouver le fichier views.py correspondant
                            for py_file in self.all_python_files:
                                relative_path = py_file.relative_to(BASE_DIR)
                                path_parts = list(relative_path.parts[:-1]) + [relative_path.stem]

                                # Vérifier si le chemin correspond
                                if (
                                    'views' in str(py_file)
                                    and path_parts[-len(module_parts) :] == module_parts
                                ):
                                    self.referenced_python_files.add(py_file)

                    # Import simple: import app.views
                    elif isinstance(node, ast.Import):
                        for alias in node.names:
                            if 'views' in alias.name:
                                # Marquer comme référencé
                                for py_file in self.all_python_files:
                                    if 'views' in str(py_file) and alias.name.split('.')[0] in str(
                                        py_file
                                    ):
                                        self.referenced_python_files.add(py_file)

            except Exception as e:
                print(f"   [WARN] Erreur lors de l'analyse de {urls_file.name}: {e}")

        print("   [OK] Analyse des URLs terminee")

    def parse_settings_py(self):
        """Parse settings.py pour détecter middleware et autres fichiers référencés."""
        print("\n[*] Analyse de settings.py...")

        settings_file = BASE_DIR / 'observations_nids' / 'settings.py'

        if settings_file.exists():
            try:
                with open(settings_file, encoding='utf-8') as f:
                    content = f.read()

                # Chercher les middleware
                middleware_pattern = r"['\"]([^'\"]+\.middleware\.[^'\"]+)['\"]"
                middlewares = re.findall(middleware_pattern, content)

                for middleware in middlewares:
                    # Convertir en chemin de fichier
                    parts = middleware.split('.')

                    for py_file in self.all_python_files:
                        relative_path = py_file.relative_to(BASE_DIR)
                        path_parts = list(relative_path.parts[:-1]) + [relative_path.stem]

                        if 'middleware' in path_parts and parts[0] in str(py_file):
                            self.referenced_python_files.add(py_file)

            except Exception as e:
                print(f"   [WARN] Erreur lors de l'analyse de settings.py: {e}")

        print("   [OK] Analyse de settings.py terminee")

    def parse_template_references(self):
        """Parse les références de templates dans les vues Python."""
        print("\n[*] Analyse des references de templates...")

        # Patterns pour trouver les templates
        patterns = [
            r"render\([^,]+,\s*['\"]([^'\"]+\.html)['\"]",  # render(request, 'template.html')
            r"render_to_response\(['\"]([^'\"]+\.html)['\"]",  # render_to_response('template.html')
            r"template_name\s*=\s*['\"]([^'\"]+\.html)['\"]",  # template_name = 'template.html'
            r"TemplateResponse\([^,]+,\s*['\"]([^'\"]+\.html)['\"]",  # TemplateResponse(request, 'template.html')
            r"get_template\(['\"]([^'\"]+\.html)['\"]",  # get_template('template.html')
        ]

        for py_file in self.all_python_files:
            try:
                with open(py_file, encoding='utf-8') as f:
                    content = f.read()

                templates = set()
                for pattern in patterns:
                    matches = re.findall(pattern, content)
                    templates.update(matches)

                if templates:
                    self.template_references[py_file] = templates

                # Marquer les templates référencés
                for template_name in templates:
                    # Django cherche les templates dans plusieurs endroits
                    # 1. BASE_DIR/templates/
                    # 2. app/templates/

                    for html_file in self.all_html_files:
                        relative_path = html_file.relative_to(BASE_DIR)

                        # Vérifier si le chemin se termine par le nom du template
                        if str(relative_path).endswith(template_name):
                            self.referenced_html_files.add(html_file)

            except Exception as e:
                print(f"   [WARN] Erreur lors de l'analyse de {py_file.name}: {e}")

        print(f"   [OK] {len(self.referenced_html_files)} templates references")

    def parse_template_includes(self):
        """Parse les templates pour détecter les {% include %} et {% extends %}."""
        print("\n[*] Analyse des includes/extends dans les templates...")

        # Patterns pour trouver les templates inclus/étendus
        patterns = [
            r"{%\s*include\s+['\"]([^'\"]+\.html)['\"]",  # {% include 'template.html' %}
            r"{%\s*extends\s+['\"]([^'\"]+\.html)['\"]",  # {% extends 'base.html' %}
        ]

        for html_file in self.all_html_files:
            try:
                with open(html_file, encoding='utf-8') as f:
                    content = f.read()

                templates = set()
                for pattern in patterns:
                    matches = re.findall(pattern, content)
                    templates.update(matches)

                # Marquer les templates référencés
                for template_name in templates:
                    for other_html in self.all_html_files:
                        relative_path = other_html.relative_to(BASE_DIR)

                        # Vérifier si le chemin se termine par le nom du template
                        if str(relative_path).endswith(template_name):
                            self.referenced_html_files.add(other_html)

            except Exception as e:
                print(f"   [WARN] Erreur lors de l'analyse de {html_file.name}: {e}")

        print("   [OK] Templates inclus/etendus detectes")

    def parse_static_references(self):
        """Parse les références de fichiers statiques dans les templates."""
        print("\n[*] Analyse des fichiers statiques dans les templates...")

        # Patterns pour trouver les fichiers statiques
        patterns = [
            r"{%\s*static\s+['\"]([^'\"]+\.css)['\"]",  # {% static 'file.css' %}
            r"{%\s*static\s+['\"]([^'\"]+\.js)['\"]",  # {% static 'file.js' %}
            r'<link[^>]+href=[\'"]([^>\'"]+\.css)[\'"]',  # <link href="file.css">
            r'<script[^>]+src=[\'"]([^>\'"]+\.js)[\'"]',  # <script src="file.js">
            r'href=[\'"]([^>\'"]+\.css)[\'"]',  # href="file.css"
            r'src=[\'"]([^>\'"]+\.js)[\'"]',  # src="file.js"
        ]

        for html_file in self.all_html_files:
            try:
                with open(html_file, encoding='utf-8') as f:
                    content = f.read()

                static_files = set()
                for pattern in patterns:
                    matches = re.findall(pattern, content)
                    static_files.update(matches)

                if static_files:
                    self.static_references[html_file] = static_files

                # Marquer les fichiers statiques référencés
                for static_name in static_files:
                    # Nettoyer le nom (enlever /static/ au début si présent)
                    cleaned_static_name = static_name.lstrip('/').replace('static/', '')

                    # Normaliser le chemin (remplacer \ par /)
                    static_name_normalized = cleaned_static_name.replace('\\', '/')

                    for css_file in self.all_css_files:
                        css_normalized = str(css_file).replace('\\', '/')
                        # Chercher par nom de fichier simple ou par chemin complet
                        if css_normalized.endswith(
                            static_name_normalized
                        ) or css_normalized.endswith('/' + static_name_normalized.split('/')[-1]):
                            self.referenced_css_files.add(css_file)

                    for js_file in self.all_js_files:
                        js_normalized = str(js_file).replace('\\', '/')
                        # Chercher par nom de fichier simple ou par chemin complet
                        if js_normalized.endswith(static_name_normalized) or js_normalized.endswith(
                            '/' + static_name_normalized.split('/')[-1]
                        ):
                            self.referenced_js_files.add(js_file)

            except Exception as e:
                print(f"   [WARN] Erreur lors de l'analyse de {html_file.name}: {e}")

        print(f"   [OK] {len(self.referenced_css_files)} fichiers CSS references")
        print(f"   [OK] {len(self.referenced_js_files)} fichiers JS references")

    def find_orphans(self) -> dict[str, list[Path]]:
        """Identifie les fichiers orphelins."""
        print("\n[*] Identification des fichiers orphelins...")

        orphans = {
            'python': sorted(self.all_python_files - self.referenced_python_files),
            'html': sorted(self.all_html_files - self.referenced_html_files),
            'css': sorted(self.all_css_files - self.referenced_css_files),
            'js': sorted(self.all_js_files - self.referenced_js_files),
        }

        return orphans

    def generate_markdown_report(self, orphans: dict[str, list[Path]]) -> str:
        """Génère le contenu du rapport au format Markdown."""
        lines = []
        lines.append("# Rapport des Fichiers Orphelins\n")
        lines.append(f"**Date de génération** : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        lines.append("---\n")

        total_orphans = sum(len(files) for files in orphans.values())

        if total_orphans == 0:
            lines.append("\n✅ **Aucun fichier orphelin détecté !**\n")
            return '\n'.join(lines)

        lines.append(f"\n⚠️ **{total_orphans} fichiers orphelins détectés**\n")

        # Statistiques
        lines.append("\n## 📊 Statistiques\n")
        for file_type, files in orphans.items():
            if files:
                lines.append(f"- **{file_type.upper()}** : {len(files)} fichier(s)\n")

        # Détails par type de fichier
        for file_type, files in orphans.items():
            if not files:
                continue

            lines.append(f"\n## {file_type.upper()} ({len(files)} fichiers)\n")

            for file_path in files:
                relative_path = file_path.relative_to(BASE_DIR)
                # Convertir les backslashes en forward slashes pour Markdown
                relative_path_str = str(relative_path).replace('\\', '/')
                lines.append(f"- `{relative_path_str}`\n")

        # Notes
        lines.append("\n---\n")
        lines.append("\n## 📝 Notes importantes\n")
        lines.append("\nCe rapport peut contenir des **faux positifs** :\n")
        lines.append("- Fichiers importés dynamiquement\n")
        lines.append("- Templates/static utilisés via des variables\n")
        lines.append("- Fichiers utilisés par des bibliothèques externes\n")
        lines.append("- Fichiers nécessaires pour le déploiement\n")
        lines.append("\n⚠️ **Vérifiez manuellement avant de supprimer un fichier !**\n")

        return ''.join(lines)

    def generate_report(self, orphans: dict[str, list[Path]]):
        """Génère un rapport des fichiers orphelins (console + fichier Markdown)."""
        # Affichage console
        print("\n" + "=" * 80)
        print("RAPPORT DES FICHIERS ORPHELINS")
        print("=" * 80)

        total_orphans = sum(len(files) for files in orphans.values())

        if total_orphans == 0:
            print("\n[OK] Aucun fichier orphelin detecte !")
        else:
            print(f"\n[!] {total_orphans} fichiers orphelins detectes\n")

            for file_type, files in orphans.items():
                if not files:
                    continue

                print(f"\n{'=' * 80}")
                print(f"{file_type.upper()} - {len(files)} fichiers orphelins")
                print(f"{'=' * 80}\n")

                for file_path in files:
                    relative_path = file_path.relative_to(BASE_DIR)
                    print(f"  - {relative_path}")

            print(f"\n{'=' * 80}")
            print("NOTES")
            print(f"{'=' * 80}\n")
            print("Ce rapport peut contenir des faux positifs :")
            print("  - Fichiers importes dynamiquement")
            print("  - Templates/static utilises via des variables")
            print("  - Fichiers utilises par des bibliotheques externes")
            print("  - Fichiers necessaires pour le deploiement")
            print("\n[!] Verifiez manuellement avant de supprimer un fichier !")
            print(f"\n{'=' * 80}\n")

        # Génération du fichier Markdown
        markdown_content = self.generate_markdown_report(orphans)
        report_path = BASE_DIR / 'scripts' / 'rapport_fichiers_orphelins.md'

        try:
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write(markdown_content)
            print(f"[OK] Rapport Markdown genere : {report_path}\n")
        except Exception as e:
            print(f"[WARN] Erreur lors de la generation du fichier Markdown : {e}\n")

    def run(self):
        """Lance l'analyse complète."""
        print("\n[*] Demarrage de l'analyse des fichiers orphelins...\n")

        self.collect_all_files()
        self.parse_python_imports()
        self.parse_urls_py()
        self.parse_settings_py()
        self.parse_template_references()
        self.parse_template_includes()
        self.parse_static_references()

        orphans = self.find_orphans()
        self.generate_report(orphans)

        print("[OK] Analyse terminee !\n")


if __name__ == '__main__':
    finder = OrphanFileFinder()
    finder.run()
