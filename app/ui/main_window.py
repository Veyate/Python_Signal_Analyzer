"""
Fenêtre principale avec barre de menu moderne CustomTkinter, menu Source, persistance des panneaux et renommage sécurisé.
"""
import customtkinter as ctk
import tkinter as tk
import os
import config
from app.utils.i18n import _, i18n
from app.utils.settings_manager import settings
from app.ui.components.project_explorer import ProjectExplorerFrame
from app.ui.components.center_tabview import CenterTabView
from app.ui.components.properties_panel import PropertiesPanelFrame
from app.ui.components.status_bar import StatusBarFrame
from app.ui.dialogs.csv_import_dialog import CSVImportDialog

class MainWindow(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title(f"{_('app_title')} v{config.APP_VERSION}")
        self.geometry(f"{config.DEFAULT_WINDOW_WIDTH}x{config.DEFAULT_WINDOW_HEIGHT}")
        self.minsize(config.MIN_WINDOW_WIDTH, config.MIN_WINDOW_HEIGHT)

        self.imported_signals = {}
        self.display_objects = {}
        self.signal_counter = 0
        self.display_counter = 0

        self.grid_rowconfigure(0, weight=0)  # Barre de menu moderne
        self.grid_rowconfigure(1, weight=1)  # Séparateurs / Panneaux
        self.grid_rowconfigure(2, weight=0)  # Barre d'état
        self.grid_columnconfigure(0, weight=1)

        self._create_modern_top_toolbar()
        self._create_paned_center_layout()

        self.status_bar = StatusBarFrame(self)
        self.status_bar.grid(row=2, column=0, sticky="ew")
        self.status_bar.set_message(_("status_ready"))

    def _create_modern_top_toolbar(self):
        """Barre de navigation supérieure 100% CustomTkinter moderne."""
        self.top_bar = ctk.CTkFrame(self, height=42, corner_radius=0, fg_color="#1a1a1a")
        self.top_bar.grid(row=0, column=0, sticky="ew", padx=0, pady=0)

        # 1. Menu Fichier
        self.menu_file = ctk.CTkOptionMenu(
            self.top_bar,
            values=["📁 Fichier", "  📄 Nouveau Projet", "  📂 Ouvrir (.psa)", "  💾 Sauvegarder", "  ❌ Quitter"],
            width=110,
            command=self._on_menu_file_selected,
            fg_color="#2b2b2b", button_color="#1f1f1f", button_hover_color="#3b3b3b"
        )
        self.menu_file.pack(side="left", padx=(8, 4), pady=5)

        # 2. Menu Source (Consacré à l'importation de données)
        self.menu_source = ctk.CTkOptionMenu(
            self.top_bar,
            values=["📥 Source", "  📊 Importer CSV..."],
            width=110,
            command=self._on_menu_source_selected,
            fg_color="#2b2b2b", button_color="#1f1f1f", button_hover_color="#3b3b3b"
        )
        self.menu_source.pack(side="left", padx=4, pady=5)

        # 3. Menu Affichage (Thèmes)
        self.menu_view = ctk.CTkOptionMenu(
            self.top_bar,
            values=["🎨 Affichage", "  🌙 Mode Sombre", "  ☀️ Mode Clair", "  🖥️ Thème Système"],
            width=120,
            command=self._on_menu_view_selected,
            fg_color="#2b2b2b", button_color="#1f1f1f", button_hover_color="#3b3b3b"
        )
        self.menu_view.pack(side="left", padx=4, pady=5)

        # 4. Menu Analyse
        self.menu_analysis = ctk.CTkOptionMenu(
            self.top_bar,
            values=["📈 Analyse", "  📊 Affichage des données"],
            width=120,
            command=self._on_menu_analysis_selected,
            fg_color="#2d6a4f", button_color="#1b4332", button_hover_color="#40916c"
        )
        self.menu_analysis.pack(side="left", padx=4, pady=5)

        # 5. Menu Aide
        self.menu_help = ctk.CTkOptionMenu(
            self.top_bar,
            values=["❓ Aide", "  📖 Manuel Utilisateur"],
            width=100,
            command=self._on_menu_help_selected,
            fg_color="#2b2b2b", button_color="#1f1f1f", button_hover_color="#3b3b3b"
        )
        self.menu_help.pack(side="left", padx=4, pady=5)

        # Côté droit : Zoom IHM + Toggle thème rapide
        btn_quick_theme = ctk.CTkButton(
            self.top_bar, text="🌙 / ☀️", width=45, fg_color="gray25", hover_color="gray35",
            command=self._toggle_quick_theme
        )
        btn_quick_theme.pack(side="right", padx=(4, 8), pady=5)

        self.combo_scaling = ctk.CTkOptionMenu(
            self.top_bar, values=["80%", "100%", "125%", "150%"], width=75, command=self._on_change_scaling
        )
        self.combo_scaling.set(f"{int(settings.settings['ui_scaling'] * 100)}%")
        self.combo_scaling.pack(side="right", padx=4, pady=5)

        label_zoom = ctk.CTkLabel(self.top_bar, text="Zoom:", font=ctk.CTkFont(size=11))
        label_zoom.pack(side="right", padx=(8, 2))

    def _create_paned_center_layout(self):
        exp_w = settings.settings.get("panel_explorer_width", 180)
        prop_w = settings.settings.get("panel_properties_width", 230)

        self.paned = tk.PanedWindow(self, orient=tk.HORIZONTAL, bd=0, sashwidth=5, bg="#1f1f1f")
        self.paned.grid(row=1, column=0, sticky="nsew", padx=3, pady=3)

        self.project_explorer = ProjectExplorerFrame(
            self.paned, on_select_item=self._on_tree_item_selected, on_delete_item=self._on_tree_item_deleted
        )
        self.paned.add(self.project_explorer, minsize=100, width=exp_w, stretch="never")

        self.center_tabview = CenterTabView(self.paned)
        self.paned.add(self.center_tabview, minsize=200, stretch="always")

        self.properties_panel = PropertiesPanelFrame(self.paned, on_property_change=self._on_property_changed)
        self.paned.add(self.properties_panel, minsize=100, width=prop_w, stretch="never")

        self.paned.bind("<ButtonRelease-1>", self._on_paned_sash_dragged)
        self.after(50, self._apply_saved_sash_positions)
        self.after(300, self._apply_saved_sash_positions)

    def _apply_saved_sash_positions(self):
        try:
            self.update_idletasks()
            total_w = self.paned.winfo_width()
            if total_w > 300:
                exp_w = settings.settings.get("panel_explorer_width", 180)
                prop_w = settings.settings.get("panel_properties_width", 230)
                self.paned.sash_place(0, exp_w, 0)
                self.paned.sash_place(1, max(exp_w + 150, total_w - prop_w), 0)
        except Exception:
            pass

    def _on_paned_sash_dragged(self, event=None):
        try:
            total_w = self.paned.winfo_width()
            sash0_x = self.paned.sash_coord(0)[0]
            sash1_x = self.paned.sash_coord(1)[0]
            if sash0_x > 50:
                settings.settings["panel_explorer_width"] = sash0_x
            if total_w - sash1_x > 50:
                settings.settings["panel_properties_width"] = total_w - sash1_x
            settings.save_settings()
        except Exception:
            pass

    # --- Callbacks Menu Supérieur ---

    def _on_menu_file_selected(self, option):
        self.menu_file.set("📁 Fichier")
        if "Nouveau" in option: self._action_new_project()
        elif "Ouvrir" in option: self._action_open_project()
        elif "Sauvegarder" in option: self._action_save_project()
        elif "Quitter" in option: self.quit()

    def _on_menu_source_selected(self, option):
        self.menu_source.set("📥 Source")
        if "Importer CSV" in option: self._action_import_csv()

    def _on_menu_view_selected(self, option):
        self.menu_view.set("🎨 Affichage")
        if "Sombre" in option: self._set_theme("Dark")
        elif "Clair" in option: self._set_theme("Light")
        elif "Système" in option: self._set_theme("System")

    def _on_menu_analysis_selected(self, option):
        self.menu_analysis.set("📈 Analyse")
        if "Affichage des données" in option:
            self._add_data_display_object()

    def _on_menu_help_selected(self, option):
        self.menu_help.set("❓ Aide")
        if "Manuel" in option: self._action_open_help()

    def _toggle_quick_theme(self):
        curr = ctk.get_appearance_mode()
        new_theme = "Light" if curr == "Dark" else "Dark"
        self._set_theme(new_theme)

    def _set_theme(self, mode):
        ctk.set_appearance_mode(mode)
        settings.settings["appearance_mode"] = mode
        settings.save_settings()

    # --- Actions Métier & Événements ---

    def _action_import_csv(self):
        dialog = CSVImportDialog(self, on_import_callback=self._on_csv_imported)

    def _on_csv_imported(self, df, x_col, y_col, file_path):
        self.signal_counter += 1
        signal_id = f"sig_{self.signal_counter}"
        file_name = os.path.basename(file_path)

        self.imported_signals[signal_id] = {
            "name": file_name,
            "df": df,
            "x_col": x_col,
            "y_col": y_col
        }

        self.project_explorer.add_imported_signal(signal_id, file_name)
        self._on_tree_item_selected(signal_id, file_name, "signal")
        self.status_bar.set_message(f"Signal '{file_name}' importé ({len(df)} points).")

    def _add_data_display_object(self):
        self.display_counter += 1
        display_id = f"disp_{self.display_counter}"
        display_name = f"Affichage {self.display_counter}"

        initial_signals = set()
        if self.imported_signals:
            first_sig_id = list(self.imported_signals.keys())[0]
            initial_signals.add(first_sig_id)

        self.display_objects[display_id] = {
            "name": display_name,
            "title": display_name,
            "x_label": "Temps",
            "y_label": "Amplitude",
            "selected_signal_ids": initial_signals,
            "linewidth": 1.2,
            "linestyle": "-",
            "x_min": None,
            "x_max": None,
            "y_min": None,
            "y_max": None
        }

        self.project_explorer.add_display_item(display_id, display_name)
        self._on_tree_item_selected(display_id, display_name, "display")
        self.status_bar.set_message(f"Nouvel affichage '{display_name}' créé.")

    def _on_tree_item_selected(self, item_id, item_text, item_type):
        if item_type == "signal" and item_id in self.imported_signals:
            sig_data = self.imported_signals[item_id]
            self.center_tabview.open_or_select_data_tab(item_id, sig_data["name"], sig_data["df"])
            self.properties_panel.display_signal_properties(item_id, sig_data, on_rename_callback=self._on_signal_renamed)
            self.status_bar.set_message(f"Données du signal : {sig_data['name']}")

        elif item_type == "display" and item_id in self.display_objects:
            disp_config = self.display_objects[item_id]
            plot_widget = self.center_tabview.open_or_select_plot_tab(item_id, disp_config["name"])
            tab_title = f"📈 {disp_config['name']}"
            is_pinned = self.center_tabview.is_tab_pinned(tab_title)

            self.properties_panel.display_display_properties(
                item_id, disp_config, self.imported_signals,
                is_pinned=is_pinned,
                on_pin_toggle_callback=self.center_tabview.toggle_pin_tab,
                on_signals_toggle_callback=self._on_display_signals_toggled,
                on_prop_change_callback=self._on_display_property_changed
            )

            self._update_plot_display(item_id)
            self.status_bar.set_message(f"Graphique : {disp_config['name']}")

    def _on_signal_renamed(self, signal_id, new_name):
        if signal_id in self.imported_signals:
            old_name = self.imported_signals[signal_id]["name"]
            if old_name == new_name:
                return

            self.imported_signals[signal_id]["name"] = new_name
            self.project_explorer.update_item_name(signal_id, new_name)

            old_tab_title = f"📋 Données: {old_name}"
            new_tab_title = f"📋 Données: {new_name}"
            self.center_tabview.rename_tab(old_tab_title, new_tab_title, data_df=self.imported_signals[signal_id]["df"])

            for disp_id in list(self.display_objects.keys()):
                self._update_plot_display(disp_id)

            self.status_bar.set_message(f"Signal renommé en '{new_name}'")

    def _on_tree_item_deleted(self, item_id, item_type):
        if item_type == "signal" and item_id in self.imported_signals:
            sig_info = self.imported_signals.pop(item_id)
            tab_title = f"📋 Données: {sig_info['name']}"
            self.center_tabview.close_tab_by_title(tab_title)
            for disp in self.display_objects.values():
                disp["selected_signal_ids"].discard(item_id)
            self.status_bar.set_message(f"Signal '{sig_info['name']}' supprimé.")

        elif item_type == "display" and item_id in self.display_objects:
            disp_info = self.display_objects.pop(item_id)
            tab_title = f"📈 {disp_info['name']}"
            self.center_tabview.close_tab_by_title(tab_title)
            self.status_bar.set_message(f"Affichage '{disp_info['name']}' supprimé.")

        self.properties_panel.show_empty()

    def _on_display_signals_toggled(self, display_id, signal_id, is_checked):
        if display_id in self.display_objects:
            sel_set = self.display_objects[display_id]["selected_signal_ids"]
            if is_checked: sel_set.add(signal_id)
            else: sel_set.discard(signal_id)
            self._update_plot_display(display_id)

    def _on_display_property_changed(self, display_id, prop_name, prop_value):
        if display_id in self.display_objects:
            old_name = self.display_objects[display_id].get("name", "")
            self.display_objects[display_id][prop_name] = prop_value

            if prop_name in ("name", "title"):
                self.display_objects[display_id]["name"] = prop_value
                self.display_objects[display_id]["title"] = prop_value

                self.project_explorer.update_item_name(display_id, prop_value)

                old_tab_title = f"📈 {old_name}"
                new_tab_title = f"📈 {prop_value}"
                self.center_tabview.rename_tab(old_tab_title, new_tab_title, display_id=display_id)

            self._update_plot_display(display_id)

    def _update_plot_display(self, display_id):
        disp_config = self.display_objects.get(display_id)
        if not disp_config: return

        plot_widget = self.center_tabview.get_plot_widget(display_id)
        if not plot_widget: return

        signals_to_plot = []
        for sig_id in disp_config.get("selected_signal_ids", set()):
            if sig_id in self.imported_signals:
                s_info = self.imported_signals[sig_id]
                df = s_info["df"]
                signals_to_plot.append({
                    "name": s_info["name"],
                    "x_data": df[s_info["x_col"]].values,
                    "y_data": df[s_info["y_col"]].values
                })

        plot_widget.plot_multi_signals(
            signals_to_plot,
            title=disp_config.get("title", disp_config.get("name")),
            x_label=disp_config.get("x_label", "Temps"),
            y_label=disp_config.get("y_label", "Amplitude"),
            linewidth=disp_config.get("linewidth", 1.2),
            linestyle=disp_config.get("linestyle", "-"),
            x_min=disp_config.get("x_min"),
            x_max=disp_config.get("x_max"),
            y_min=disp_config.get("y_min"),
            y_max=disp_config.get("y_max")
        )

    def _on_change_scaling(self, choice_str):
        scale_val = float(choice_str.replace("%", "")) / 100.0
        settings.settings["ui_scaling"] = scale_val
        settings.save_settings()
        ctk.set_widget_scaling(scale_val)
        ctk.set_window_scaling(scale_val)

    def _on_property_changed(self, new_props): pass
    def _action_new_project(self): pass
    def _action_open_project(self): pass
    def _action_save_project(self): pass
    def _action_open_help(self): pass
