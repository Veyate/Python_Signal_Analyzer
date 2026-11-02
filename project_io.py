# project_io.py
import os
import json
import shutil
import tempfile
import zipfile
from datetime import datetime


class ProjectIOManager:
    """Gestionnaire de sauvegarde et chargement de projets auto-contenus (.psa / ZIP)."""

    FILE_FILTER = "Projet PySide Signal Analysis (*.psa);;Archives ZIP (*.zip);;Tous les fichiers (*)"

    @staticmethod
    def save_project(file_path: str, main_window) -> bool:
        """
        Exporte le projet courant vers une archive ZIP .psa.
        Les fichiers CSV importés sont copiés à l'intérieur de l'archive sous 'data/'
        pour garantir l'autonomie totale du projet.
        Enregistre également la liste des onglets actuellement ouverts.
        """
        temp_dir = tempfile.mkdtemp(prefix="psa_export_")
        data_dir = os.path.join(temp_dir, "data")
        os.makedirs(data_dir, exist_ok=True)

        if isinstance(main_window, list):
            nodes_registry = main_window
            mw_obj = None
        else:
            nodes_registry = getattr(main_window, "nodes_registry", [])
            mw_obj = main_window

        nodes_data = []
        node_id_map = {}

        for idx, node in enumerate(nodes_registry):
            node_id = f"node_{idx+1}"
            node_id_map[node] = node_id

            node_dict = {
                "id": node_id,
                "type": getattr(node, "node_type", "unknown"),
                "pos_x": float(node.pos().x()),
                "pos_y": float(node.pos().y()),
                "params": dict(node.params)
            }

            # Si c'est un nœud d'import CSV, copie le fichier dans data/ de l'archive
            if getattr(node, "node_type", "") == "csv_import":
                src_csv = node.params.get("file_path", "")
                if src_csv and os.path.exists(src_csv):
                    csv_filename = f"{node_id}_{os.path.basename(src_csv)}"
                    dest_csv = os.path.join(data_dir, csv_filename)
                    try:
                        shutil.copy2(src_csv, dest_csv)
                        node_dict["params"]["internal_csv_relpath"] = f"data/{csv_filename}"
                    except Exception as e:
                        print(f"Erreur lors de la copie du CSV {src_csv}: {e}")

            nodes_data.append(node_dict)

        # Sauvegarde des connexions
        connections_data = []
        for node in nodes_registry:
            if hasattr(node, "input_node_a") and node.input_node_a in node_id_map:
                connections_data.append({
                    "source_id": node_id_map[node.input_node_a],
                    "target_id": node_id_map[node],
                    "target_port": "a"
                })
            elif hasattr(node, "input_node") and node.input_node in node_id_map:
                connections_data.append({
                    "source_id": node_id_map[node.input_node],
                    "target_id": node_id_map[node],
                    "target_port": "a"
                })

            if hasattr(node, "input_node_b") and node.input_node_b in node_id_map:
                connections_data.append({
                    "source_id": node_id_map[node.input_node_b],
                    "target_id": node_id_map[node],
                    "target_port": "b"
                })

        # Sauvegarde des onglets ouverts dans l'interface
        open_tabs_data = []
        if mw_obj and hasattr(mw_obj, "center_tabs"):
            for i in range(mw_obj.center_tabs.count()):
                widget = mw_obj.center_tabs.widget(i)
                node = getattr(widget, "associated_node", None)
                if node and node in node_id_map:
                    tab_type = "graph" if widget.__class__.__name__ == "MplCanvasWidget" else "table"
                    tab_info = {
                        "node_id": node_id_map[node],
                        "type": tab_type
                    }
                    if tab_type == "graph" and hasattr(widget, "get_graph_config"):
                        tab_info["config"] = widget.get_graph_config()
                    open_tabs_data.append(tab_info)

        project_manifest = {
            "format_version": "1.0",
            "app_name": "PySide6 Signal Studio",
            "saved_at": datetime.now().isoformat(),
            "nodes": nodes_data,
            "connections": connections_data,
            "open_tabs": open_tabs_data
        }

        # Écriture du manifest project.json
        manifest_path = os.path.join(temp_dir, "project.json")
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(project_manifest, f, indent=4, ensure_ascii=False)

        # Compression dans l'archive .psa
        try:
            with zipfile.ZipFile(file_path, "w", zipfile.ZIP_DEFLATED) as zip_file:
                for root, dirs, files in os.walk(temp_dir):
                    for file in files:
                        full_path = os.path.join(root, file)
                        rel_path = os.path.relpath(full_path, temp_dir)
                        zip_file.write(full_path, rel_path)
            success = True
        except Exception as e:
            print(f"Erreur lors de la création de l'archive .psa: {e}")
            success = False
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

        return success

    @staticmethod
    def load_project(file_path: str, main_window) -> bool:
        """
        Extrait et restaure un projet .psa à partir de son archive ZIP.
        Les fichiers CSV internes sont extraits dans un dossier local temporaire.
        Restaure également les onglets graphiques et tableaux ouverts.
        """
        if not os.path.exists(file_path):
            return False

        temp_dir = tempfile.mkdtemp(prefix="psa_import_")
        try:
            with zipfile.ZipFile(file_path, "r") as zip_file:
                zip_file.extractall(temp_dir)

            manifest_path = os.path.join(temp_dir, "project.json")
            if not os.path.exists(manifest_path):
                print("Fichier project.json introuvable dans l'archive.")
                return False

            with open(manifest_path, "r", encoding="utf-8") as f:
                project_manifest = json.load(f)

            # Nettoyage de la scène courante
            canvas = main_window.node_editor
            nodes_to_delete = list(main_window.nodes_registry)
            for n in nodes_to_delete:
                main_window.delete_node(n)

            id_node_map = {}

            # Reconstruction des nœuds
            for n_data in project_manifest.get("nodes", []):
                node_type = n_data.get("type", "")
                pos_x = n_data.get("pos_x", 0.0)
                pos_y = n_data.get("pos_y", 0.0)
                params = n_data.get("params", {})
                node_id = n_data.get("id")

                if node_type == "generator":
                    node = canvas.add_generator_node(name=params.get("name", "Générateur"), x=pos_x, y=pos_y)
                    node.params.update(params)

                elif node_type == "csv_import":
                    rel_csv = params.get("internal_csv_relpath", "")
                    if rel_csv:
                        extracted_csv = os.path.join(temp_dir, rel_csv)
                        if os.path.exists(extracted_csv):
                            params["file_path"] = extracted_csv

                    node = canvas.add_csv_node(name=params.get("name", "Import CSV"), x=pos_x, y=pos_y)
                    node.params.update(params)

                elif node_type == "do160_double_exp":
                    node = canvas.add_do160_double_exp_node(name=params.get("name", "Impulsion DO-160"), x=pos_x, y=pos_y)
                    node.params.update(params)

                elif node_type == "do160_damped_sine":
                    node = canvas.add_do160_damped_sine_node(name=params.get("name", "Sinus Amorti WF3"), x=pos_x, y=pos_y)
                    node.params.update(params)

                elif node_type in ("filter", "lowpass_filter"):
                    node = canvas.add_lowpass_node(name=params.get("name", "Filtre Passe-Bas"), x=pos_x, y=pos_y)
                    node.params.update(params)

                elif node_type == "highpass_filter":
                    node = canvas.add_highpass_node(name=params.get("name", "Filtre Passe-Haut"), x=pos_x, y=pos_y)
                    node.params.update(params)

                elif node_type == "bandpass_filter":
                    node = canvas.add_bandpass_node(name=params.get("name", "Filtre Passe-Bande"), x=pos_x, y=pos_y)
                    node.params.update(params)

                elif node_type == "bandstop_filter":
                    node = canvas.add_bandstop_node(name=params.get("name", "Filtre Coupe-Bande"), x=pos_x, y=pos_y)
                    node.params.update(params)

                elif node_type == "derivative":
                    node = canvas.add_derivative_node(name=params.get("name", "Dérivateur"), x=pos_x, y=pos_y)
                    node.params.update(params)

                elif node_type == "integrator":
                    node = canvas.add_integrator_node(name=params.get("name", "Intégrateur"), x=pos_x, y=pos_y)
                    node.params.update(params)

                elif node_type == "gain":
                    node = canvas.add_gain_node(name=params.get("name", "Gain"), x=pos_x, y=pos_y)
                    node.params.update(params)

                elif node_type == "inversion":
                    node = canvas.add_inversion_node(name=params.get("name", "Inversion"), x=pos_x, y=pos_y)
                    node.params.update(params)

                elif node_type == "abs_val":
                    node = canvas.add_abs_node(name=params.get("name", "Absolue"), x=pos_x, y=pos_y)
                    node.params.update(params)

                elif node_type == "log_func":
                    node = canvas.add_log_node(name=params.get("name", "Logarithme"), x=pos_x, y=pos_y)
                    node.params.update(params)

                elif node_type == "exp_func":
                    node = canvas.add_exp_node(name=params.get("name", "Exponentielle"), x=pos_x, y=pos_y)
                    node.params.update(params)

                elif node_type == "power_func":
                    node = canvas.add_power_node(name=params.get("name", "Puissance"), x=pos_x, y=pos_y)
                    node.params.update(params)

                elif node_type == "addition":
                    node = canvas.add_addition_node(name=params.get("name", "Addition"), x=pos_x, y=pos_y)
                    node.params.update(params)

                elif node_type == "noise_generator":
                    node = canvas.add_noise_node(name=params.get("name", "Injecteur de Bruit"), x=pos_x, y=pos_y)
                    node.params.update(params)

                elif node_type == "resample":
                    node = canvas.add_resample_node(name=params.get("name", "Rééchantillonnage"), x=pos_x, y=pos_y)
                    node.params.update(params)

                elif node_type == "interpolation":
                    node = canvas.add_interpolation_node(name=params.get("name", "Interpolation"), x=pos_x, y=pos_y)
                    node.params.update(params)

                elif node_type == "dac_simulation":
                    node = canvas.add_dac_node(name=params.get("name", "Simulation DAC"), x=pos_x, y=pos_y)
                    node.params.update(params)

                elif node_type == "fixed_average":
                    node = canvas.add_fixed_average_node(name=params.get("name", "Moyenne Fixe"), x=pos_x, y=pos_y)
                    node.params.update(params)

                elif node_type == "moving_average":
                    node = canvas.add_moving_average_node(name=params.get("name", "Moyenne Glissante"), x=pos_x, y=pos_y)
                    node.params.update(params)

                elif node_type == "median_filter":
                    node = canvas.add_median_filter_node(name=params.get("name", "Filtre Médian"), x=pos_x, y=pos_y)
                    node.params.update(params)

                elif node_type in ("thd_analysis", "thd"):
                    node = canvas.add_thd_node(name=params.get("name", "Analyse THD"), x=pos_x, y=pos_y)
                    node.params.update(params)

                elif node_type in ("fft_analysis", "fft"):
                    node = canvas.add_fft_node(name=params.get("name", "Analyse FFT"), x=pos_x, y=pos_y)
                    node.params.update(params)

                else:
                    continue

                node.setPos(pos_x, pos_y)
                node.recalculate()
                id_node_map[node_id] = node
                main_window.nodes_registry.append(node)

            # Reconstruction des connexions
            for conn_data in project_manifest.get("connections", []):
                src_node = id_node_map.get(conn_data.get("source_id"))
                tgt_node = id_node_map.get(conn_data.get("target_id"))
                port = conn_data.get("target_port", "a")
                if src_node and tgt_node:
                    canvas.create_connection(src_node, tgt_node, target_port=port)

            # Recalcul global
            main_window.recalc_all_nodes()
            main_window.refresh_project_tree()

            # Restauration des onglets ouverts
            for tab_info in project_manifest.get("open_tabs", []):
                node_id = tab_info.get("node_id")
                tab_type = tab_info.get("type")
                graph_config = tab_info.get("config")
                target_node = id_node_map.get(node_id)
                if target_node:
                    if tab_type == "graph":
                        widget = main_window.open_graph_for_node(target_node)
                        if widget and graph_config and hasattr(widget, "apply_graph_config"):
                            widget.apply_graph_config(graph_config)
                    elif tab_type == "table":
                        main_window.open_table_for_node(target_node)

            return True

        except Exception as e:
            print(f"Erreur lors du chargement du projet .psa: {e}")
            return False
