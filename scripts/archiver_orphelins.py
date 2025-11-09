#!/usr/bin/env python
"""
Script pour archiver les fichiers orphelins avant suppression.

Ce script :
- Archive les fichiers vraiment orphelins (sans exceptions)
- Préserve la structure des dossiers
- Génère un README.md avec détails
- Crée un script restore.sh pour restaurer si besoin
- Supprime les fichiers originaux
"""

import contextlib
import os
import shutil
from datetime import datetime
from pathlib import Path

# Configuration
BASE_DIR = Path(__file__).resolve().parent.parent
ARCHIVE_BASE_DIR = BASE_DIR / '.archived_orphans'


class OrphanArchiver:
    """Classe pour archiver les fichiers orphelins."""

    def __init__(self, orphan_files: list[str], dry_run: bool = False):
        """
        Initialise l'archiveur.

        Args:
            orphan_files: Liste des chemins de fichiers à archiver
            dry_run: Si True, simule sans supprimer
        """
        self.orphan_files = orphan_files
        self.dry_run = dry_run

        # Créer le nom du dossier d'archive avec timestamp
        timestamp = datetime.now().strftime('%Y-%m-%d_%Hh%M')
        self.archive_dir = ARCHIVE_BASE_DIR / timestamp

    def create_archive_structure(self):
        """Crée la structure du dossier d'archive."""
        print(f"\n[*] Creation de l'archive : {self.archive_dir}")

        if not self.dry_run:
            self.archive_dir.mkdir(parents=True, exist_ok=True)
            print("   [OK] Dossier d'archive cree")
        else:
            print("   [DRY-RUN] Dossier d'archive serait cree")

    def archive_file(self, filepath: str) -> bool:
        """
        Archive un fichier en préservant sa structure.

        Args:
            filepath: Chemin relatif du fichier à archiver

        Returns:
            True si succès, False sinon
        """
        source = BASE_DIR / filepath.replace('/', os.sep)
        destination = self.archive_dir / filepath.replace('/', os.sep)

        if not source.exists():
            print(f"   [WARN] Fichier introuvable : {filepath}")
            return False

        try:
            if not self.dry_run:
                # Créer les dossiers parents si nécessaire
                destination.parent.mkdir(parents=True, exist_ok=True)

                # Copier le fichier
                shutil.copy2(source, destination)

            print(f"   [OK] Archive : {filepath}")
            return True

        except Exception as e:
            print(f"   [ERROR] Erreur lors de l'archivage de {filepath}: {e}")
            return False

    def delete_file(self, filepath: str) -> bool:
        """
        Supprime le fichier original.

        Args:
            filepath: Chemin relatif du fichier à supprimer

        Returns:
            True si succès, False sinon
        """
        source = BASE_DIR / filepath.replace('/', os.sep)

        if not source.exists():
            return False

        try:
            if not self.dry_run:
                source.unlink()
                print(f"   [OK] Supprime : {filepath}")
            else:
                print(f"   [DRY-RUN] Serait supprime : {filepath}")
            return True

        except Exception as e:
            print(f"   [ERROR] Erreur lors de la suppression de {filepath}: {e}")
            return False

    def generate_readme(self, archived_files: list[str], deleted_files: list[str]):
        """Génère un README.md dans le dossier d'archive."""
        readme_path = self.archive_dir / 'README.md'

        content = f"""# Archive des Fichiers Orphelins

**Date d'archivage** : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 📋 Statistiques

- **Fichiers archivés** : {len(archived_files)}
- **Fichiers supprimés** : {len(deleted_files)}

## 📂 Fichiers Archivés

"""
        for filepath in sorted(archived_files):
            content += f"- `{filepath}`\n"

        content += f"""

## 🔄 Restauration

Pour restaurer ces fichiers, exécutez :

```bash
bash restore.sh
```

Ou manuellement, copiez les fichiers depuis ce dossier vers la racine du projet en respectant l'arborescence.

## ⚠️ Notes

- Ces fichiers ont été détectés comme orphelins (aucune référence trouvée dans le code)
- Vérifiez qu'ils ne sont vraiment plus nécessaires avant de supprimer définitivement cette archive
- Cette archive peut être conservée indéfiniment ou supprimée après vérification

## 🗑️ Suppression de cette archive

Si vous êtes certain que ces fichiers ne sont plus nécessaires :

```bash
# Depuis la racine du projet
rm -rf {self.archive_dir.relative_to(BASE_DIR)}
```
"""

        if not self.dry_run:
            with open(readme_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print("\n[OK] README.md genere")
        else:
            print("\n[DRY-RUN] README.md serait genere")

    def generate_restore_script(self, archived_files: list[str]):
        """Génère un script restore.sh pour restaurer les fichiers."""
        restore_path = self.archive_dir / 'restore.sh'

        content = """#!/bin/bash
# Script de restauration automatique
# Execute depuis la racine du projet

echo "Restauration des fichiers archives..."

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

"""

        for filepath in sorted(archived_files):
            # Convertir en chemins Unix pour le script bash
            unix_path = filepath.replace('\\', '/')
            content += f"""
# Restaurer {unix_path}
if [ -f "$SCRIPT_DIR/{unix_path}" ]; then
    mkdir -p "$PROJECT_ROOT/$(dirname "{unix_path}")"
    cp "$SCRIPT_DIR/{unix_path}" "$PROJECT_ROOT/{unix_path}"
    echo "[OK] Restaure : {unix_path}"
else
    echo "[WARN] Fichier introuvable : {unix_path}"
fi
"""

        content += """
echo ""
echo "Restauration terminee !"
echo "Verifiez que les fichiers ont ete correctement restaures."
"""

        if not self.dry_run:
            with open(restore_path, 'w', encoding='utf-8', newline='\n') as f:
                f.write(content)

            # Rendre le script exécutable (Unix)
            with contextlib.suppress(Exception):
                restore_path.chmod(0o755)

            print("[OK] Script restore.sh genere")
        else:
            print("[DRY-RUN] Script restore.sh serait genere")

    def run(self) -> tuple[int, int]:
        """
        Lance l'archivage complet.

        Returns:
            Tuple (nb_archived, nb_deleted)
        """
        if not self.orphan_files:
            print("[*] Aucun fichier a archiver.")
            return 0, 0

        print("\n" + "=" * 80)
        print("ARCHIVAGE DES FICHIERS ORPHELINS")
        if self.dry_run:
            print("MODE DRY-RUN (simulation uniquement)")
        print("=" * 80)

        # Créer la structure d'archive
        self.create_archive_structure()

        print(f"\n[*] Archivage de {len(self.orphan_files)} fichier(s)...\n")

        archived_files = []
        deleted_files = []

        # Archiver chaque fichier
        for filepath in self.orphan_files:
            if self.archive_file(filepath):
                archived_files.append(filepath)

        # Supprimer les fichiers originaux
        if not self.dry_run:
            print("\n[*] Suppression des fichiers originaux...\n")
            for filepath in archived_files:
                if self.delete_file(filepath):
                    deleted_files.append(filepath)

        # Générer README et script de restauration
        if archived_files:
            self.generate_readme(archived_files, deleted_files)
            self.generate_restore_script(archived_files)

        # Résumé
        print("\n" + "=" * 80)
        if not self.dry_run:
            print("ARCHIVAGE TERMINE")
            print(f"Fichiers archives : {len(archived_files)}")
            print(f"Fichiers supprimes : {len(deleted_files)}")
            print(f"Archive creee dans : {self.archive_dir.relative_to(BASE_DIR)}")
        else:
            print("DRY-RUN TERMINE")
            print(f"Fichiers qui seraient archives : {len(archived_files)}")
            print(f"Fichiers qui seraient supprimes : {len(archived_files)}")
        print("=" * 80 + "\n")

        return len(archived_files), len(deleted_files)


def archive_orphans(orphan_files: list[str], dry_run: bool = False) -> tuple[int, int]:
    """
    Fonction principale pour archiver des fichiers orphelins.

    Args:
        orphan_files: Liste des chemins de fichiers à archiver
        dry_run: Si True, simule sans supprimer

    Returns:
        Tuple (nb_archived, nb_deleted)
    """
    archiver = OrphanArchiver(orphan_files, dry_run=dry_run)
    return archiver.run()


if __name__ == '__main__':
    # Test avec des fichiers exemple
    import sys

    if len(sys.argv) > 1:
        test_files = sys.argv[1:]
        dry_run = '--dry-run' in test_files

        if dry_run:
            test_files.remove('--dry-run')

        print(f"[TEST] Archivage de {len(test_files)} fichier(s)")
        archive_orphans(test_files, dry_run=dry_run)
    else:
        print("Usage: python archiver_orphelins.py [--dry-run] <file1> <file2> ...")
        print("\nExemple:")
        print("  python archiver_orphelins.py --dry-run maintenance.html")
