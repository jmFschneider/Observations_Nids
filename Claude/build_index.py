#!/usr/bin/env python3

"""
Génère un index.md avec un sommaire détaillé vers les fichiers Markdown d'un répertoire.
- Liens vers les fichiers .md (hors index.md par défaut)
- Sous-sections cliquables (##, ###, ... jusqu'à une profondeur configurable)
- Slugification "GitHub/Obsidian-like" (accents, ponctuation, espaces)
- Gestion des doublons d'ancres (ajout de suffixes -1, -2, ...)
"""

from __future__ import annotations

import argparse
import re
import sys
import unicodedata
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

def parse_headings(md_path: Path, max_depth: int) -> tuple[str, list[tuple[int, str, str]]]:
    """
    Retourne:
      - title: titre H1 (ou nom de fichier)
      - sections: liste de (level, text, anchor_slug) pour niveaux 2..max_depth
    """
    title = md_path.stem
    sections: list[tuple[int, str, str]] = []
    used: dict[str, int] = {}

    try:
        text = md_path.read_text(encoding='utf-8')
    except UnicodeDecodeError:
        # fallback Windows-1252 si nécessaire
        text = md_path.read_text(encoding='cp1252')

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

    return title, sections

def build_index(root: Path, out_file: Path, max_depth: int, excludes: list[str]) -> str:
    files = [p for p in root.glob('*.md') if p.name.lower() not in {e.lower() for e in excludes}]
    files.sort(key=lambda p: natural_key(p.name))

    lines: list[str] = []
    lines.append("# 📘 Documentation – Index")
    lines.append("")
    lines.append("Bienvenue dans la documentation. Utilisez les liens ci-dessous pour accéder rapidement aux guides et à leurs sections.")
    lines.append("")
    lines.append("---")
    lines.append("")

    for md in files:
        title, sections = parse_headings(md, max_depth=max_depth)
        rel = md.name  # même dossier
        rel_url = quote(rel)  # encode espaces etc.
        lines.append(f"### [{rel}]({rel_url})")
        lines.append(f"**{title}**")
        if sections:
            lines.append("")
            # Indentation cohérente selon le niveau
            base_level = min(l for (l, _, _) in sections) if sections else 2
            for level, text, slug in sections:
                indent = "  " * (level - base_level)
                lines.append(f"{indent}- [{text}]({rel_url}#{slug})")
        lines.append("")
        lines.append("---")
        lines.append("")

    content = "\n".join(lines).rstrip() + "\n"
    out_file.write_text(content, encoding='utf-8')
    return content

def main():
    parser = argparse.ArgumentParser(
        description="Génère un index.md avec sommaires détaillés pour les fichiers Markdown."
    )
    parser.add_argument("--root", default=".", help="Répertoire racine des .md (défaut: .)")
    parser.add_argument("--out", default="index.md", help="Nom du fichier de sortie (défaut: index.md)")
    parser.add_argument("--max-depth", type=int, default=4, help="Profondeur max des titres (défaut: 4 → jusqu'à ####)")
    parser.add_argument("--exclude", default="index.md,README.md",
                        help="Fichiers à exclure (liste séparée par des virgules)")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    out_file = (root / args.out).resolve()
    excludes = [e.strip() for e in args.exclude.split(",") if e.strip()]

    if not root.exists():
        print(f"❌ Répertoire introuvable: {root}", file=sys.stderr)
        sys.exit(1)

    content = build_index(root, out_file, args.max_depth, excludes)
    print(f"✅ Fichier généré: {out_file}")
    print(f"📄 Aperçu (premières lignes):\n{'\n'.join(content.splitlines()[:10])}")

if __name__ == "__main__":
    main()
