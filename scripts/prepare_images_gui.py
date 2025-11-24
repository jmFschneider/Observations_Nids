#!/usr/bin/env python
"""
Interface graphique pour la préparation d'images OCR.

Ce script fournit une interface Tkinter pour prépare_images_local.py
avec sauvegarde automatique des préférences utilisateur.

Usage:
    python scripts/prepare_images_gui.py
"""

import json
import subprocess
import sys
import threading
from pathlib import Path
from tkinter import *
from tkinter import filedialog, messagebox, scrolledtext, ttk

# Configuration
PREFERENCES_FILE = Path.home() / ".observations_nids_preferences.json"


class PreparationImagesGUI:
    """Interface graphique pour la préparation d'images."""

    def __init__(self, root):
        self.root = root
        self.root.title("Préparation d'Images pour OCR")
        self.root.geometry("700x650")
        self.root.resizable(True, True)

        # Variables
        self.input_dir = StringVar()
        self.output_dir = StringVar()
        self.crop_percent = StringVar(value="100")
        self.operateur = StringVar(value="Utilisateur")
        self.skip_deskew = BooleanVar(value=False)
        self.skip_optimize = BooleanVar(value=False)
        self.preview_mode = BooleanVar(value=False)
        self.verbose = BooleanVar(value=False)

        # État du traitement
        self.processing = False
        self.process = None

        # Charger les préférences
        self.load_preferences()

        # Créer l'interface
        self.create_widgets()

    def create_widgets(self):
        """Crée les widgets de l'interface."""

        # === SECTION 1 : Chemins ===
        frame_paths = LabelFrame(self.root, text="📁 Chemins", padx=10, pady=10)
        frame_paths.pack(fill="x", padx=10, pady=5)

        # Input directory
        Label(frame_paths, text="Dossier d'entrée (scans bruts) :").grid(
            row=0, column=0, sticky="w", pady=5
        )
        Entry(frame_paths, textvariable=self.input_dir, width=50).grid(
            row=0, column=1, pady=5
        )
        Button(
            frame_paths, text="Parcourir...", command=self.browse_input, width=12
        ).grid(row=0, column=2, padx=5, pady=5)

        # Output directory
        Label(frame_paths, text="Dossier de sortie (préparé) :").grid(
            row=1, column=0, sticky="w", pady=5
        )
        Entry(frame_paths, textvariable=self.output_dir, width=50).grid(
            row=1, column=1, pady=5
        )
        Button(
            frame_paths, text="Parcourir...", command=self.browse_output, width=12
        ).grid(row=1, column=2, padx=5, pady=5)

        # === SECTION 2 : Options ===
        frame_options = LabelFrame(self.root, text="⚙️ Options", padx=10, pady=10)
        frame_options.pack(fill="x", padx=10, pady=5)

        # Opérateur
        Label(frame_options, text="Nom de l'opérateur :").grid(
            row=0, column=0, sticky="w", pady=5
        )
        Entry(frame_options, textvariable=self.operateur, width=30).grid(
            row=0, column=1, sticky="w", pady=5
        )

        # Crop verso
        Label(frame_options, text="Recadrage verso :").grid(
            row=1, column=0, sticky="w", pady=5
        )
        frame_crop = Frame(frame_options)
        frame_crop.grid(row=1, column=1, sticky="w", pady=5)

        Radiobutton(
            frame_crop,
            text="100% (complet)",
            variable=self.crop_percent,
            value="100",
        ).pack(side=LEFT, padx=5)
        Radiobutton(
            frame_crop,
            text="55% (partie gauche)",
            variable=self.crop_percent,
            value="55",
        ).pack(side=LEFT, padx=5)

        # === SECTION 3 : Traitement ===
        frame_processing = LabelFrame(
            self.root, text="🔧 Traitement", padx=10, pady=10
        )
        frame_processing.pack(fill="x", padx=10, pady=5)

        Checkbutton(
            frame_processing,
            text="Désactiver le redressement automatique (deskew)",
            variable=self.skip_deskew,
        ).grid(row=0, column=0, sticky="w", pady=2)

        Checkbutton(
            frame_processing,
            text="Désactiver les optimisations OCR (CLAHE, débruitage, etc.)",
            variable=self.skip_optimize,
        ).grid(row=1, column=0, sticky="w", pady=2)

        # === SECTION 4 : Mode ===
        frame_mode = LabelFrame(self.root, text="🎯 Mode", padx=10, pady=10)
        frame_mode.pack(fill="x", padx=10, pady=5)

        Checkbutton(
            frame_mode,
            text="Mode aperçu (ne pas enregistrer les fichiers)",
            variable=self.preview_mode,
        ).grid(row=0, column=0, sticky="w", pady=2)

        Checkbutton(
            frame_mode, text="Logs détaillés (verbose)", variable=self.verbose
        ).grid(row=1, column=0, sticky="w", pady=2)

        # === SECTION 5 : Actions ===
        frame_actions = Frame(self.root, padx=10, pady=10)
        frame_actions.pack(fill="x")

        self.btn_run = Button(
            frame_actions,
            text="▶ Lancer le traitement",
            command=self.run_processing,
            bg="#4CAF50",
            fg="white",
            font=("Arial", 12, "bold"),
            height=2,
            width=25,
        )
        self.btn_run.pack(side=LEFT, padx=5)

        self.btn_stop = Button(
            frame_actions,
            text="⏹ Arrêter",
            command=self.stop_processing,
            bg="#f44336",
            fg="white",
            font=("Arial", 12, "bold"),
            height=2,
            width=15,
            state=DISABLED,
        )
        self.btn_stop.pack(side=LEFT, padx=5)

        # === SECTION 6 : Logs ===
        frame_logs = LabelFrame(self.root, text="📋 Logs", padx=10, pady=10)
        frame_logs.pack(fill="both", expand=True, padx=10, pady=5)

        self.log_text = scrolledtext.ScrolledText(
            frame_logs, height=10, wrap=WORD, state=DISABLED
        )
        self.log_text.pack(fill="both", expand=True)

        # === SECTION 7 : Barre de progression ===
        self.progress = ttk.Progressbar(
            self.root, orient=HORIZONTAL, mode='indeterminate'
        )
        self.progress.pack(fill="x", padx=10, pady=5)

    def browse_input(self):
        """Ouvre le dialogue de sélection de dossier d'entrée."""
        directory = filedialog.askdirectory(
            title="Sélectionner le dossier de scans bruts",
            initialdir=self.input_dir.get() or str(Path.home()),
        )
        if directory:
            self.input_dir.set(directory)

    def browse_output(self):
        """Ouvre le dialogue de sélection de dossier de sortie."""
        directory = filedialog.askdirectory(
            title="Sélectionner le dossier de sortie",
            initialdir=self.output_dir.get() or str(Path.home()),
        )
        if directory:
            self.output_dir.set(directory)

    def validate_inputs(self):
        """Valide les entrées utilisateur."""
        if not self.input_dir.get():
            messagebox.showerror(
                "Erreur", "Veuillez sélectionner un dossier d'entrée."
            )
            return False

        if not Path(self.input_dir.get()).exists():
            messagebox.showerror("Erreur", "Le dossier d'entrée n'existe pas.")
            return False

        if not self.output_dir.get():
            messagebox.showerror(
                "Erreur", "Veuillez sélectionner un dossier de sortie."
            )
            return False

        return True

    def build_command(self):
        """Construit la commande à exécuter."""
        script_path = Path(__file__).parent / "prepare_images_local.py"

        cmd = [
            sys.executable,
            str(script_path),
            "--input",
            self.input_dir.get(),
            "--output",
            self.output_dir.get(),
            "--crop",
            self.crop_percent.get(),
            "--operateur",
            self.operateur.get(),
        ]

        if self.skip_deskew.get():
            cmd.append("--skip-deskew")

        if self.skip_optimize.get():
            cmd.append("--skip-optimize")

        if self.preview_mode.get():
            cmd.append("--preview")

        if self.verbose.get():
            cmd.append("--verbose")

        return cmd

    def log(self, message):
        """Ajoute un message dans les logs."""
        self.log_text.config(state=NORMAL)
        self.log_text.insert(END, message + "\n")
        self.log_text.see(END)
        self.log_text.config(state=DISABLED)

    def run_processing(self):
        """Lance le traitement en arrière-plan."""
        if not self.validate_inputs():
            return

        # Sauvegarder les préférences
        self.save_preferences()

        # État UI
        self.processing = True
        self.btn_run.config(state=DISABLED)
        self.btn_stop.config(state=NORMAL)
        self.progress.start()

        # Effacer les logs précédents
        self.log_text.config(state=NORMAL)
        self.log_text.delete(1.0, END)
        self.log_text.config(state=DISABLED)

        # Construire la commande
        cmd = self.build_command()
        self.log(f"🚀 Commande : {' '.join(cmd)}\n")
        self.log("=" * 60)

        # Lancer dans un thread séparé
        thread = threading.Thread(target=self.execute_processing, args=(cmd,))
        thread.daemon = True
        thread.start()

    def execute_processing(self, cmd):
        """Exécute le processus de traitement."""
        try:
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True,
            )

            # Lire la sortie en temps réel
            for line in self.process.stdout:
                if not self.processing:
                    break
                self.root.after(0, self.log, line.rstrip())

            self.process.wait()

            # Traitement terminé
            if self.processing:
                if self.process.returncode == 0:
                    self.root.after(
                        0,
                        messagebox.showinfo,
                        "Succès",
                        "✓ Traitement terminé avec succès !",
                    )
                else:
                    self.root.after(
                        0,
                        messagebox.showerror,
                        "Erreur",
                        f"✗ Le traitement a échoué (code {self.process.returncode})",
                    )

        except Exception as e:
            self.root.after(
                0, messagebox.showerror, "Erreur", f"Erreur lors du traitement : {e}"
            )

        finally:
            # Réinitialiser l'état UI
            self.root.after(0, self.reset_ui)

    def stop_processing(self):
        """Arrête le traitement en cours."""
        if self.process and self.process.poll() is None:
            self.process.terminate()
            self.log("\n⏹ Traitement arrêté par l'utilisateur.")

        self.processing = False
        self.reset_ui()

    def reset_ui(self):
        """Réinitialise l'interface après traitement."""
        self.btn_run.config(state=NORMAL)
        self.btn_stop.config(state=DISABLED)
        self.progress.stop()
        self.processing = False

    def load_preferences(self):
        """Charge les préférences utilisateur depuis le fichier JSON."""
        if PREFERENCES_FILE.exists():
            try:
                with open(PREFERENCES_FILE, 'r', encoding='utf-8') as f:
                    prefs = json.load(f)

                self.input_dir.set(prefs.get('input_dir', ''))
                self.output_dir.set(prefs.get('output_dir', ''))
                self.crop_percent.set(prefs.get('crop_percent', '100'))
                self.operateur.set(prefs.get('operateur', 'Utilisateur'))
                self.skip_deskew.set(prefs.get('skip_deskew', False))
                self.skip_optimize.set(prefs.get('skip_optimize', False))
                self.preview_mode.set(prefs.get('preview_mode', False))
                self.verbose.set(prefs.get('verbose', False))

                self.log(f"✓ Préférences chargées depuis : {PREFERENCES_FILE}")
            except Exception as e:
                self.log(f"⚠ Erreur lors du chargement des préférences : {e}")

    def save_preferences(self):
        """Sauvegarde les préférences utilisateur dans le fichier JSON."""
        prefs = {
            'input_dir': self.input_dir.get(),
            'output_dir': self.output_dir.get(),
            'crop_percent': self.crop_percent.get(),
            'operateur': self.operateur.get(),
            'skip_deskew': self.skip_deskew.get(),
            'skip_optimize': self.skip_optimize.get(),
            'preview_mode': self.preview_mode.get(),
            'verbose': self.verbose.get(),
        }

        try:
            with open(PREFERENCES_FILE, 'w', encoding='utf-8') as f:
                json.dump(prefs, f, indent=2, ensure_ascii=False)
            self.log(f"✓ Préférences sauvegardées dans : {PREFERENCES_FILE}")
        except Exception as e:
            self.log(f"⚠ Erreur lors de la sauvegarde des préférences : {e}")


def main():
    """Point d'entrée de l'application GUI."""
    root = Tk()
    app = PreparationImagesGUI(root)
    root.mainloop()


if __name__ == '__main__':
    main()
