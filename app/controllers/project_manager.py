"""
Gestionnaire d'importation et d'exportation de projets (.psa).
Le format .psa est une archive ZIP contenant :
- manifest.json : Métadonnées du projet, structure d'arborescence, configurations des graphiques et analyses FFT.
- signals/ : Fichiers CSV des données brutes de chaque signal.
"""
import os
import json
import zipfile
import shutil
import pandas as pd
import io

class ProjectManager:
    @staticmethod
    def save_project(file_path, imported_signals, display_objects, fft_objects, signal_counter, display_counter, fft_counter):
        try:
            temp_dir = os.path.join(os.path.dirname(file_path), "_temp_psa_build")
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
            os.makedirs(os.path.join(temp_dir, "signals"), exist_ok=True)

            signals_meta = {}
            for sig_id, sig_info in imported_signals.items():
                df = sig_info["df"]
                csv_filename = f"{sig_id}.csv"
                csv_path = os.path.join(temp_dir, "signals", csv_filename)
                df.to_csv(csv_path, sep=";", index=False)

                signals_meta[sig_id] = {
                    "name": sig_info["name"],
                    "x_col": sig_info["x_col"],
                    "y_col": sig_info["y_col"],
                    "file_rel_path": f"signals/{csv_filename}"
                }

            displays_meta = {}
            for disp_id, disp_info in display_objects.items():
                d_copy = disp_info.copy()
                if isinstance(d_copy.get("selected_signal_ids"), set):
                    d_copy["selected_signal_ids"] = list(d_copy["selected_signal_ids"])
                displays_meta[disp_id] = d_copy

            ffts_meta = {}
            for fft_id, fft_info in fft_objects.items():
                f_copy = fft_info.copy()
                if isinstance(f_copy.get("selected_signal_ids"), set):
                    f_copy["selected_signal_ids"] = list(f_copy["selected_signal_ids"])
                f_copy.pop("computed_freqs", None)
                f_copy.pop("computed_amplitude", None)
                f_copy.pop("computed_spectrums", None)
                ffts_meta[fft_id] = f_copy

            manifest = {
                "version": "1.1",
                "signal_counter": signal_counter,
                "display_counter": display_counter,
                "fft_counter": fft_counter,
                "signals": signals_meta,
                "displays": displays_meta,
                "ffts": ffts_meta
            }

            with open(os.path.join(temp_dir, "manifest.json"), "w", encoding="utf-8") as f:
                json.dump(manifest, f, indent=4, ensure_ascii=False)

            with zipfile.ZipFile(file_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root, _, files in os.walk(temp_dir):
                    for file in files:
                        full_p = os.path.join(root, file)
                        rel_p = os.path.relpath(full_p, temp_dir)
                        zipf.write(full_p, rel_p)

            shutil.rmtree(temp_dir)
            return True, "Projet sauvegardé avec succès."
        except Exception as e:
            return False, f"Erreur lors de la sauvegarde : {str(e)}"

    @staticmethod
    def load_project(file_path):
        try:
            if not zipfile.is_zipfile(file_path):
                return False, "Le fichier sélectionné n'est pas un projet .psa valide.", None

            imported_signals = {}
            display_objects = {}
            fft_objects = {}

            with zipfile.ZipFile(file_path, 'r') as zipf:
                if "manifest.json" not in zipf.namelist():
                    return False, "Le fichier .psa est corrompu (manifest.json manquant).", None

                with zipf.open("manifest.json") as f:
                    manifest = json.load(f)

                sig_counter = manifest.get("signal_counter", 0)
                disp_counter = manifest.get("display_counter", 0)
                fft_counter = manifest.get("fft_counter", 0)

                for sig_id, sig_info in manifest.get("signals", {}).items():
                    rel_p = sig_info["file_rel_path"]
                    if rel_p in zipf.namelist():
                        csv_bytes = zipf.read(rel_p)
                        df = pd.read_csv(io.BytesIO(csv_bytes), sep=";")
                        imported_signals[sig_id] = {
                            "name": sig_info["name"],
                            "df": df,
                            "x_col": sig_info["x_col"],
                            "y_col": sig_info["y_col"]
                        }

                for disp_id, disp_info in manifest.get("displays", {}).items():
                    if "selected_signal_ids" in disp_info:
                        disp_info["selected_signal_ids"] = set(disp_info["selected_signal_ids"])
                    display_objects[disp_id] = disp_info

                for fft_id, fft_info in manifest.get("ffts", {}).items():
                    if "selected_signal_ids" in fft_info:
                        fft_info["selected_signal_ids"] = set(fft_info["selected_signal_ids"])
                    fft_objects[fft_id] = fft_info

            return True, "Projet chargé avec succès.", {
                "imported_signals": imported_signals,
                "display_objects": display_objects,
                "fft_objects": fft_objects,
                "signal_counter": sig_counter,
                "display_counter": disp_counter,
                "fft_counter": fft_counter
            }
        except Exception as e:
            return False, f"Erreur lors du chargement : {str(e)}", None
