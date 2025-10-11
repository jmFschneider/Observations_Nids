#!/usr/bin/env python3

"""
Génère un index.md avec un sommaire détaillé vers les fichiers Markdown d'un répertoire.

Fonctionnalités:
- Liens vers les fichiers .md (hors index.md par défaut)
- Sous-sections cliquables (##, ###, ... jusqu'à une profondeur configurable)
- Slugification "GitHub/Obsidian-like" (accents, ponctuation, espaces)
- Gestion des doublons d'ancres (ajout de suffixes -1, -2, ...)
- 📊 Statistiques sur les documents (nombre de mots, taille fichiers, totaux)
- Emojis contextuels selon le type de document
- Date de génération automatique

Utilisation:
    python build_index.py                              # Simple
    python build_index.py --no-stats                   # Sans statistiques
    python build_index.py --max-depth 3                # Profondeur limitée
    python build_index.py --root ./docs --out index.md # Autre répertoire
"""

from __future__ import annotations

import argparse
import re
import sys
import unicodedata
from datetime import datetime
from pathlib import Path
from urllib.parse import quote

HEADING_RE = re.compile(r'^(#{1,6})\s+(.*?)(\s+#+\s*)?$')  # # Titre ####  (fin optionnelle)

def natural_key(s: str):
    """Tri naturel: '10_file' après '2_file'."""
    return [int(text) if text.isdigit() else text.lower()
            for text in re.findall(r'\d+|\D+', s)]

def strip_markdown_formatting(text: str) -> str:
    """Enlève les décorations Markdown simples pour slugifier plus proprement."""
    # code inline
    text = re.sub(r'`([^`]*)`', r'\1', text)
    # liens [texte](url)
    text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)
    # emphases ** */_ _
    text = re.sub(r'[*_]{1,3}([^*_]+)[*_]{1,3}', r'\1', text)
    # images ![alt](src)
    text = re.sub(r'!\[([^\]]*)\]\([^)]+\)', r'\1', text)
    # HTML inline <tag>…</tag>
    text = re.sub(r'<[^>]+>', ' ', text)
    return text.strip()

def slugify_gfm(heading: str, used: dict[str, int]) -> str:
    """
    Slug "GitHub Flavored Markdown"-like:
    - lower, strip
    - enlever diacritiques
    - supprimer ponctuation, garder espaces et '-'
    - remplacer espaces par '-'
    - compresser les '-'
    - gérer doublons avec suffixes '-1', '-2', ...
    """
    text = strip_markdown_formatting(heading)
    text = text.strip().lower()
    # décomposer unicode et enlever diacritiques
    text = ''.join(
        ch for ch in unicodedata.normalize('NFD', text)
        if unicodedata.category(ch) != 'Mn'
    )
    # supprimer tout sauf lettres, chiffres, espaces et '-'
    text = re.sub(r'[^a-z0-9\- ]+', '', text)
    # remplacer espaces par '-'
    text = re.sub(r'\s+', '-', text)
    # compresser multiples '-'
    text = re.sub(r'-{2,}', '-', text).strip('-')

    base = text or 'section'
    count = used.get(base, 0)
    if count == 0:
        used[base] = 1
        return base
    else:
        used[base] = count + 1
        return f"{base}-{count}"

def parse_headings(md_path: Path, max_depth: int) -> tuple[str, list[tuple[int, str, str]], int]:
    """
    Retourne:
      - title: titre H1 (ou nom de fichier)
      - sections: liste de (level, text, anchor_slug) pour niveaux 2..max_depth
      - word_count: nombre approximatif de mots dans le document
    """
    title = md_path.stem
    sections: list[tuple[int, str, str]] = []
    used: dict[str, int] = {}
    word_count = 0

    try:
        text = md_path.read_text(encoding='utf-8')
    except UnicodeDecodeError:
        # fallback Windows-1252 si nécessaire
        try:
            text = md_path.read_text(encoding='cp1252')
        except Exception as e:
            print(f"⚠️  Impossible de lire {md_path.name}: {e}", file=sys.stderr)
            return title, sections, 0

    # Compter approximativement les mots (hors code blocks)
    text_without_code = re.sub(r'```.*?```', '', text, flags=re.DOTALL)
    words = re.findall(r'\b\w+\b', text_without_code)
    word_count = len(words)

    for line in text.splitlines():
        m = HEADING_RE.match(line.rstrip())
        if not m:
            continue
        level = len(m.group(1))
        heading_text = m.group(2).strip()
        if level == 1:
            title = strip_markdown_formatting(heading_text) or title
        elif 2 <= level <= max_depth:
            slug = slugify_gfm(heading_text, used)
            sections.append((level, strip_markdown_formatting(heading_text), slug))

    return title, sections, word_count

def format_file_size(size_or_path) -> str:
    """Retourne la taille du fichier de manière lisible."""
    size = size_or_path.stat().st_size if isinstance(size_or_path, Path) else size_or_path

    if size < 1024:
        return f"{size} B"
    elif size < 1024 * 1024:
        return f"{size / 1024:.1f} KB"
    else:
        return f"{size / (1024 * 1024):.1f} MB"

def get_file_emoji(filename: str) -> str:
    """Retourne un emoji approprié selon le type de fichier."""
    filename_lower = filename.lower()
    emoji_map = {
        '📘': ['0', 'readme'],
        '🚀': ['quick', 'start'],
        '🏗️': ['architecture'],
        '🔄': ['workflow', 'git'],
        '📖': ['guide'],
        '⚡': ['optimisation', 'performance'],
        '🗄️': ['reset', 'database'],
        '🌍': ['geocod', 'altitude'],
        '🏘️': ['commune'],
    }
    for emoji, keywords in emoji_map.items():
        if any(keyword in filename_lower for keyword in keywords):
            return emoji
    return '📄'

def build_index(root: Path, out_file: Path, max_depth: int, excludes: list[str], show_stats: bool = True) -> str:
    """Génère l'index avec statistiques optionnelles."""
    files = [p for p in root.glob('*.md') if p.name.lower() not in {e.lower() for e in excludes}]

    if not files:
        print("⚠️  Aucun fichier Markdown trouvé", file=sys.stderr)
        return ""

    files.sort(key=lambda p: natural_key(p.name))

    lines: list[str] = []
    lines.append("# 📘 Documentation – Index")
    lines.append("")
    lines.append("Bienvenue dans la documentation du projet **Observations Nids**.")
    lines.append("")
    lines.append("Utilisez les liens ci-dessous pour accéder rapidement aux guides et à leurs sections.")
    lines.append("")

    if show_stats:
        total_words = 0
        total_size = 0
        lines.append("## 📊 Statistiques")
        lines.append("")
        lines.append(f"- **Nombre de documents** : {len(files)}")

    lines.append("")
    lines.append("---")
    lines.append("")

    for md in files:
        title, sections, word_count = parse_headings(md, max_depth=max_depth)
        rel = md.name  # même dossier
        rel_url = quote(rel)  # encode espaces etc.
        emoji = get_file_emoji(md.name)

        lines.append(f"### {emoji} [{rel}]({rel_url})")
        lines.append(f"**{title}**")

        if show_stats:
            file_size = format_file_size(md)
            lines.append(f"  \n*≈ {word_count} mots • {file_size}*")
            total_words += word_count
            total_size += md.stat().st_size

        if sections:
            lines.append("")
            # Indentation cohérente selon le niveau
            base_level = min(level for (level, _, _) in sections) if sections else 2
            for level, text, slug in sections:
                indent = "  " * (level - base_level)
                lines.append(f"{indent}- [{text}]({rel_url}#{slug})")
        lines.append("")
        lines.append("---")
        lines.append("")

    if show_stats:
        lines.insert(6, f"- **Total de mots** : ≈ {total_words:,}")
        lines.insert(7, f"- **Taille totale** : {format_file_size(total_size)}")
        lines.insert(8, "")

    # Ajout du footer avec date de génération
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append(f"*Index généré automatiquement le {datetime.now().strftime('%d/%m/%Y à %H:%M')}*")
    lines.append("")

    content = "\n".join(lines).rstrip() + "\n"
    out_file.write_text(content, encoding='utf-8')
    return content

def safe_print(text: str):
    """Affiche du texte en gérant les erreurs d'encodage Windows."""
    try:
        print(text)
    except UnicodeEncodeError:
        # Fallback : enlever les emojis pour Windows
        text_no_emoji = re.sub(r'[^\x00-\x7F]+', '', text)
        print(text_no_emoji)

def main():
    parser = argparse.ArgumentParser(
        description="Génère un index.md avec sommaires détaillés pour les fichiers Markdown.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples d'utilisation:
  python build_index.py
  python build_index.py --root ./docs --out sommaire.md
  python build_index.py --max-depth 3 --no-stats
  python build_index.py --exclude "index.md,README.md,DRAFT.md"
        """
    )
    parser.add_argument("--root", default=".", help="Répertoire racine des .md (défaut: .)")
    parser.add_argument("--out", default="index.md", help="Nom du fichier de sortie (défaut: index.md)")
    parser.add_argument("--max-depth", type=int, default=4, help="Profondeur max des titres (défaut: 4 → jusqu'à ####)")
    parser.add_argument("--exclude", default="index.md,README.md",
                        help="Fichiers à exclure (liste séparée par des virgules)")
    parser.add_argument("--no-stats", action="store_true", help="Ne pas afficher les statistiques")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    out_file = (root / args.out).resolve()
    excludes = [e.strip() for e in args.exclude.split(",") if e.strip()]

    if not root.exists():
        safe_print(f"[ERREUR] Répertoire introuvable: {root}")
        sys.exit(1)

    if not root.is_dir():
        safe_print(f"[ERREUR] Le chemin spécifié n'est pas un répertoire: {root}")
        sys.exit(1)

    safe_print(f"Analyse du répertoire: {root}")
    safe_print(f"Fichiers exclus: {', '.join(excludes)}")
    safe_print("")

    content = build_index(root, out_file, args.max_depth, excludes, show_stats=not args.no_stats)

    if content:
        safe_print(f"[OK] Fichier généré: {out_file}")
        safe_print("Aperçu (premières lignes):\n")
        safe_print('\n'.join(content.splitlines()[:15]))
        safe_print("...")
    else:
        safe_print("[ERREUR] Aucun contenu généré")
        sys.exit(1)

if __name__ == "__main__":
    main()
