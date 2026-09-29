"""
Fenêtre principale avec barre de menu moderne CustomTkinter, menu Source, persistance fixe des panneaux,
analyses FFT multi-signaux et sauvegarde/chargement de projets .psa.
"""
import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox
import os
import config
import numpy as np
from app.utils.i18n import _, i18n
from app.utils.settings_manager import settings
from app.ui.components.project_explorer import ProjectExplorerFrame
from app.ui.components.center_tabview import CenterTabView
from app.ui.components.properties_panel import PropertiesPanelFrame
from app.ui.components.status_bar import StatusBarFrame
from app.ui.dialogs.csv_import_dialog import CSVImportDialog
from app.controllers.project_manager import ProjectManager
from app.controllers.fft_analyzer import FFTAnalyzer

class MainWindow(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title(f"{_('app_title')} v{config.APP_VERSION}")
        self.geometry(f"{config.DEFAULT_WINDOW_WIDTH}x{config.DEFAULT_WINDOW_HEIGHT}")
        self.minsize(config.MIN_WINDOW_WIDTH, config.MIN_WINDOW_HEIGHT)

        self.imported_signals = {}
        self.display_objects = {}
        self.fft_objects = {}
        self.signal_counter = 0
        self.display_counter = 0
        self.fft_counter = 0

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
            values=[_("menu_file"), _("menu_file_new"), _("menu_file_open"), _("menu_file_save"), _("menu_file_quit")],
            width=110,
            command=self._on_menu_file_selected,
            fg_color="#2b2b2b", button_color="#1f1f1f", button_hover_color="#3b3b3b"
        )
        self.menu_file.pack(side="left", padx=(8, 4), pady=5)

        # 2. Menu Source
        self.menu_source = ctk.CTkOptionMenu(
            self.top_bar,
            values=[_("menu_source"), _("menu_source_import")],
            width=110,
            command=self._on_menu_source_selected,
            fg_color="#2b2b2b", button_color="#1f1f1f", button_hover_color="#3b3b3b"
        )
        self.menu_source.pack(side="left", padx=4, pady=5)

        # 3. Menu Affichage (Thèmes)
        self.menu_view = ctk.CTkOptionMenu(
            self.top_bar,
            values=[_("menu_view"), _("menu_view_dark"), _("menu_view_light"), _("menu_view_system")],
            width=120,
            command=self._on_menu_view_selected,
            fg_color="#2b2b2b", button_color="#1f1f1f", button_hover_color="#3b3b3b"
        )
        self.menu_view.pack(side="left", padx=4, pady=5)

        # 4. Menu Analyse (Affichage + FFT)
        self.menu_analysis = ctk.CTkOptionMenu(
            self.top_bar,
            values=[_("menu_analysis"), _("menu_analysis_display"), _("menu_analysis_fft")],
            width=150,
            command=self._on_menu_analysis_selected,
            fg_color="#2d6a4f", button_color="#1b4332", button_hover_color="#40916c"
        )
        self.menu_analysis.pack(side="left", padx=4, pady=5)

        # 5. Menu Aide
        self.menu_help = ctk.CTkOptionMenu(
            self.top_bar,
            values=[_("menu_help"), _("menu_help_manual")],
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

        label_zoom = ctk.CTkLabel(self.top_bar, text=_("zoom"), font=ctk.CTkFont(size=11))
        label_zoom.pack(side="right", padx=(8, 2))

    def _create_paned_center_layout(self):
        exp_w = max(100, min(settings.settings.get("panel_explorer_width", 180), 350))
        prop_w = max(140, min(settings.settings.get("panel_properties_width", 230), 380))

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
        self.after(100, self._apply_saved_sash_positions)

    def _apply_saved_sash_positions(self):
        try:
            self.update_idletasks()
            total_w = self.paned.winfo_width()
            if total_w > 300:
                exp_w = max(100, min(settings.settings.get("panel_explorer_width", 180), 350))
                prop_w = max(140, min(settings.settings.get("panel_properties_width", 230), 380))
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
                settings.settings["panel_explorer_width"] = max(100, min(sash0_x, 350))
            if total_w - sash1_x > 50:
                settings.settings["panel_properties_width"] = max(140, min(total_w - sash1_x, 380))
            settings.save_settings()
        except Exception:
            pass

    # --- Callbacks Menu Supérieur ---

    def _on_menu_file_selected(self, option):
        self.menu_file.set(_("menu_file"))
        if _("menu_file_new").strip() in option or "Nouveau" in option or "New" in option:
            self._action_new_project()
        elif _("menu_file_open").strip() in option or "Ouvrir" in option or "Open" in option:
            self._action_open_project()
        elif _("menu_file_save").strip() in option or "Sauvegarder" in option or "Save" in option:
            self._action_save_project()
        elif _("menu_file_quit").strip() in option or "Quitter" in option or "Quit" in option:
            self.quit()

    def _on_menu_source_selected(self, option):
        self.menu_source.set(_("menu_source"))
        if _("menu_source_import").strip() in option or "Importer" in option or "Import" in option:
            self._action_import_csv()

    def _on_menu_view_selected(self, option):
        self.menu_view.set(_("menu_view"))
        if "Sombre" in option or "Dark" in option: self._set_theme("Dark")
        elif "Clair" in option or "Light" in option: self._set_theme("Light")
        elif "Système" in option or "System" in option: self._set_theme("System")

    def _on_menu_analysis_selected(self, option):
        self.menu_analysis.set(_("menu_analysis"))
        if _("menu_analysis_display").strip() in option or "Affichage des données" in option or "Data Display" in option:
            self._add_data_display_object()
        elif _("menu_analysis_fft").strip() in option or "Fourier" in option or "FFT" in option:
            self._add_fft_object()

    def _on_menu_help_selected(self, option):
        self.menu_help.set(_("menu_help"))
        if "Manuel" in option or "Manual" in option: self._action_open_help()

    def _toggle_quick_theme(self):
        curr = ctk.get_appearance_mode()
        new_theme = "Light" if curr == "Dark" else "Dark"
        self._set_theme(new_theme)

    def _set_theme(self, mode):
        ctk.set_appearance_mode(mode)
        settings.settings["appearance_mode"] = mode
        settings.save_settings()

    # --- Actions Projet (Nouveau, Ouvrir, Sauvegarder) ---

    def _action_new_project(self):
        if self.imported_signals or self.display_objects or self.fft_objects:
            if not messagebox.askyesno(_("warning_title"), _("confirm_new_project")):
                return

        self.imported_signals.clear()
        self.display_objects.clear()
        self.fft_objects.clear()
        self.signal_counter = 0
        self.display_counter = 0
        self.fft_counter = 0

        self.project_explorer.clear_tree()
        self.center_tabview.close_all_tabs()
        self.properties_panel.show_empty()
        self.status_bar.set_message(_("status_project_new"))

    def _action_save_project(self):
        path = filedialog.asksaveasfilename(
            title=_("save_project_title"),
            filetypes=[(_("psa_file_type"), "*.psa"), (_("all_files"), "*.*")],
            defaultextension=".psa"
        )
        if path:
            success, msg = ProjectManager.save_project(
                path, self.imported_signals, self.display_objects, self.fft_objects,
                self.signal_counter, self.display_counter, self.fft_counter
            )
            if success:
                self.status_bar.set_message(_("status_project_saved", os.path.basename(path)))
            else:
                messagebox.showerror(_("warning_title"), msg)
                self.status_bar.set_message(_("status_project_error"), msg)

    def _action_open_project(self):
        if self.imported_signals or self.display_objects or self.fft_objects:
            if not messagebox.askyesno(_("warning_title"), _("confirm_open_project")):
                return

        path = filedialog.askopenfilename(
            title=_("open_project_title"),
            filetypes=[(_("psa_file_type"), "*.psa"), (_("all_files"), "*.*")]
        )
        if path:
            success, msg, data = ProjectManager.load_project(path)
            if success:
                self.imported_signals = data["imported_signals"]
                self.display_objects = data["display_objects"]
                self.fft_objects = data.get("fft_objects", {})
                self.signal_counter = data["signal_counter"]
                self.display_counter = data["display_counter"]
                self.fft_counter = data.get("fft_counter", 0)

                self.project_explorer.clear_tree()
                self.center_tabview.close_all_tabs()

                for sig_id, sig_info in self.imported_signals.items():
                    self.project_explorer.add_imported_signal(sig_id, sig_info["name"])

                for disp_id, disp_info in self.display_objects.items():
                    self.project_explorer.add_display_item(disp_id, disp_info["name"])

                for fft_id, fft_info in self.fft_objects.items():
                    self.project_explorer.add_fft_item(fft_id, fft_info["name"])

                self.status_bar.set_message(_("status_project_loaded", os.path.basename(path)))
            else:
                messagebox.showerror(_("warning_title"), msg)
                self.status_bar.set_message(_("status_project_error"), msg)

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
        self.status_bar.set_message(_("status_signal_imported", file_name, len(df)))

    def _add_data_display_object(self):
        self.display_counter += 1
        display_id = f"disp_{self.display_counter}"
        display_name = f"Affichage {self.display_counter}"

        initial_signals = set()
        c1_target_id = None
        c2_target_id = None
        if self.imported_signals:
            first_sig_id = list(self.imported_signals.keys())[0]
            initial_signals.add(first_sig_id)
            c1_target_id = first_sig_id
            c2_target_id = first_sig_id

        self.display_objects[display_id] = {
            "name": display_name,
            "title": display_name,
            "x_label": "Temps",
            "y_label": "Amplitude",
            "selected_signal_ids": initial_signals,
            "cursor1_target_id": c1_target_id,
            "cursor2_target_id": c2_target_id,
            "linewidth": 1.2,
            "linestyle": "-",
            "x_min": None,
            "x_max": None,
            "y_min": None,
            "y_max": None,
            "cursors_enabled": False,
            "cursor1_x": None,
            "cursor2_x": None,
            "ref_freq": 50.0,
            "show_cursor_overlay": True
        }

        self.project_explorer.add_display_item(display_id, display_name)
        self._on_tree_item_selected(display_id, display_name, "display")
        self.status_bar.set_message(_("status_display_created", display_name))

    def _add_fft_object(self):
        self.fft_counter += 1
        fft_id = f"fft_{self.fft_counter}"
        fft_name = f"FFT {self.fft_counter}"

        initial_signals = set()
        c1_target_id = None
        c2_target_id = None
        if self.imported_signals:
            first_sig_id = list(self.imported_signals.keys())[0]
            initial_signals.add(first_sig_id)
            c1_target_id = first_sig_id
            c2_target_id = first_sig_id

        self.fft_objects[fft_id] = {
            "name": fft_name,
            "title": fft_name,
            "selected_signal_ids": initial_signals,
            "cursor1_target_id": c1_target_id,
            "cursor2_target_id": c2_target_id,
            "window_type": "Hann",
            "n_points": "Auto",
            "f_min": None,
            "f_max": None,
            "x_label": "Fréquence (Hz)",
            "y_label": "Amplitude",
            "linewidth": 1.2,
            "linestyle": "-",
            "x_min": None,
            "x_max": None,
            "y_min": None,
            "y_max": None,
            "cursors_enabled": False,
            "cursor1_x": None,
            "cursor2_x": None,
            "ref_freq": 50.0,
            "show_cursor_overlay": True,
            "peak_search_enabled": False,
            "num_peaks": 5,
            "detected_peaks": []
        }

        self.project_explorer.add_fft_item(fft_id, fft_name)
        self._on_tree_item_selected(fft_id, fft_name, "fft")
        self.status_bar.set_message(_("status_fft_created", fft_name))

    def _on_tree_item_selected(self, item_id, item_text, item_type):
        if item_type == "signal" and item_id in self.imported_signals:
            sig_data = self.imported_signals[item_id]
            self.center_tabview.open_or_select_data_tab(item_id, sig_data["name"], sig_data["df"])
            self.properties_panel.display_signal_properties(item_id, sig_data, on_rename_callback=self._on_signal_renamed)
            self.status_bar.set_message(_("status_signal_data", sig_data['name']))

        elif item_type == "display" and item_id in self.display_objects:
            disp_config = self.display_objects[item_id]
            plot_widget = self.center_tabview.open_or_select_plot_tab(item_id, disp_config["name"])
            tab_title = _("tab_plot_prefix", disp_config['name'])
            is_pinned = self.center_tabview.is_tab_pinned(tab_title)

            self.properties_panel.display_display_properties(
                item_id, disp_config, self.imported_signals,
                is_pinned=is_pinned,
                on_pin_toggle_callback=self.center_tabview.toggle_pin_tab,
                on_signals_toggle_callback=self._on_display_signals_toggled,
                on_prop_change_callback=self._on_display_property_changed
            )

            self._update_plot_display(item_id)
            self.status_bar.set_message(_("status_plot", disp_config['name']))

        elif item_type == "fft" and item_id in self.fft_objects:
            fft_config = self.fft_objects[item_id]
            plot_widget = self.center_tabview.open_or_select_fft_tab(item_id, fft_config["name"])
            tab_title = _("tab_fft_prefix", fft_config['name'])
            is_pinned = self.center_tabview.is_tab_pinned(tab_title)

            self._update_fft_display(item_id)

            self.properties_panel.display_fft_properties(
                item_id, fft_config, self.imported_signals,
                is_pinned=is_pinned,
                on_pin_toggle_callback=self.center_tabview.toggle_pin_tab,
                on_signals_toggle_callback=self._on_fft_signals_toggled,
                on_prop_change_callback=self._on_fft_property_changed
            )

            self.status_bar.set_message(_("status_fft_data", fft_config['name']))

    def _on_signal_renamed(self, signal_id, new_name):
        if signal_id in self.imported_signals:
            old_name = self.imported_signals[signal_id]["name"]
            if old_name == new_name:
                return

            self.imported_signals[signal_id]["name"] = new_name
            self.project_explorer.update_item_name(signal_id, new_name)

            old_tab_title = _("tab_data_prefix", old_name)
            new_tab_title = _("tab_data_prefix", new_name)
            self.center_tabview.rename_tab(old_tab_title, new_tab_title, data_df=self.imported_signals[signal_id]["df"])

            for disp_id in list(self.display_objects.keys()):
                self._update_plot_display(disp_id)

            for fft_id in list(self.fft_objects.keys()):
                self._update_fft_display(fft_id)

            self.status_bar.set_message(_("status_signal_renamed", new_name))

    def _on_tree_item_deleted(self, item_id, item_type):
        if item_type == "signal" and item_id in self.imported_signals:
            sig_info = self.imported_signals.pop(item_id)
            tab_title = _("tab_data_prefix", sig_info['name'])
            self.center_tabview.close_tab_by_title(tab_title)

            for disp in self.display_objects.values():
                disp["selected_signal_ids"].discard(item_id)
                if disp.get("cursor1_target_id") == item_id: disp["cursor1_target_id"] = None
                if disp.get("cursor2_target_id") == item_id: disp["cursor2_target_id"] = None

            for fft_info in self.fft_objects.values():
                if "selected_signal_ids" in fft_info and isinstance(fft_info["selected_signal_ids"], set):
                    fft_info["selected_signal_ids"].discard(item_id)
                if fft_info.get("cursor1_target_id") == item_id: fft_info["cursor1_target_id"] = None
                if fft_info.get("cursor2_target_id") == item_id: fft_info["cursor2_target_id"] = None

            self.status_bar.set_message(_("status_signal_deleted", sig_info['name']))

        elif item_type == "display" and item_id in self.display_objects:
            disp_info = self.display_objects.pop(item_id)
            tab_title = _("tab_plot_prefix", disp_info['name'])
            self.center_tabview.close_tab_by_title(tab_title)
            self.status_bar.set_message(_("status_display_deleted", disp_info['name']))

        elif item_type == "fft" and item_id in self.fft_objects:
            fft_info = self.fft_objects.pop(item_id)
            tab_title = _("tab_fft_prefix", fft_info['name'])
            self.center_tabview.close_tab_by_title(tab_title)
            self.status_bar.set_message(_("status_fft_deleted", fft_info['name']))

        self.properties_panel.show_empty()

    def _on_display_signals_toggled(self, display_id, signal_id, is_checked):
        if display_id in self.display_objects:
            sel_set = self.display_objects[display_id]["selected_signal_ids"]
            if is_checked:
                sel_set.add(signal_id)
                if not self.display_objects[display_id].get("cursor1_target_id"):
                    self.display_objects[display_id]["cursor1_target_id"] = signal_id
                if not self.display_objects[display_id].get("cursor2_target_id"):
                    self.display_objects[display_id]["cursor2_target_id"] = signal_id
            else:
                sel_set.discard(signal_id)
                remaining = list(sel_set)
                fallback = remaining[0] if remaining else None
                if self.display_objects[display_id].get("cursor1_target_id") == signal_id:
                    self.display_objects[display_id]["cursor1_target_id"] = fallback
                if self.display_objects[display_id].get("cursor2_target_id") == signal_id:
                    self.display_objects[display_id]["cursor2_target_id"] = fallback

            self._update_plot_display(display_id)

    def _on_fft_signals_toggled(self, fft_id, signal_id, is_checked):
        if fft_id in self.fft_objects:
            sel_set = self.fft_objects[fft_id].get("selected_signal_ids", set())
            if not isinstance(sel_set, set):
                sel_set = set(sel_set)
                self.fft_objects[fft_id]["selected_signal_ids"] = sel_set

            if is_checked:
                sel_set.add(signal_id)
                if not self.fft_objects[fft_id].get("cursor1_target_id"):
                    self.fft_objects[fft_id]["cursor1_target_id"] = signal_id
                if not self.fft_objects[fft_id].get("cursor2_target_id"):
                    self.fft_objects[fft_id]["cursor2_target_id"] = signal_id
            else:
                sel_set.discard(signal_id)
                remaining = list(sel_set)
                fallback = remaining[0] if remaining else None
                if self.fft_objects[fft_id].get("cursor1_target_id") == signal_id:
                    self.fft_objects[fft_id]["cursor1_target_id"] = fallback
                if self.fft_objects[fft_id].get("cursor2_target_id") == signal_id:
                    self.fft_objects[fft_id]["cursor2_target_id"] = fallback

            self._update_fft_display(fft_id)

    def _on_display_property_changed(self, display_id, prop_name, prop_value):
        if display_id in self.display_objects:
            old_name = self.display_objects[display_id].get("name", "")
            self.display_objects[display_id][prop_name] = prop_value

            if prop_name in ("name", "title"):
                self.display_objects[display_id]["name"] = prop_value
                self.display_objects[display_id]["title"] = prop_value

                self.project_explorer.update_item_name(display_id, prop_value)

                old_tab_title = _("tab_plot_prefix", old_name)
                new_tab_title = _("tab_plot_prefix", prop_value)
                self.center_tabview.rename_tab(old_tab_title, new_tab_title, display_id=display_id)

            self._update_plot_display(display_id)

            if prop_name in ("cursors_enabled", "cursor1_target_id", "cursor2_target_id"):
                disp_config = self.display_objects[display_id]
                tab_title = _("tab_plot_prefix", disp_config['name'])
                is_pinned = self.center_tabview.is_tab_pinned(tab_title)
                self.properties_panel.display_display_properties(
                    display_id, disp_config, self.imported_signals,
                    is_pinned=is_pinned,
                    on_pin_toggle_callback=self.center_tabview.toggle_pin_tab,
                    on_signals_toggle_callback=self._on_display_signals_toggled,
                    on_prop_change_callback=self._on_display_property_changed
                )

    def _on_fft_property_changed(self, fft_id, prop_name, prop_value):
        if fft_id in self.fft_objects:
            old_name = self.fft_objects[fft_id].get("name", "")
            self.fft_objects[fft_id][prop_name] = prop_value

            if prop_name in ("name", "title"):
                self.fft_objects[fft_id]["name"] = prop_value
                self.fft_objects[fft_id]["title"] = prop_value

                self.project_explorer.update_item_name(fft_id, prop_value)

                old_tab_title = _("tab_fft_prefix", old_name)
                new_tab_title = _("tab_fft_prefix", prop_value)
                self.center_tabview.rename_tab(old_tab_title, new_tab_title, fft_id=fft_id)

            self._update_fft_display(fft_id)

            if prop_name in ("cursors_enabled", "cursor1_target_id", "cursor2_target_id", "window_type", "n_points", "f_min", "f_max", "peak_search_enabled", "num_peaks"):
                fft_config = self.fft_objects[fft_id]
                tab_title = _("tab_fft_prefix", fft_config['name'])
                is_pinned = self.center_tabview.is_tab_pinned(tab_title)
                self.properties_panel.display_fft_properties(
                    fft_id, fft_config, self.imported_signals,
                    is_pinned=is_pinned,
                    on_pin_toggle_callback=self.center_tabview.toggle_pin_tab,
                    on_signals_toggle_callback=self._on_fft_signals_toggled,
                    on_prop_change_callback=self._on_fft_property_changed
                )

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
                    "id": sig_id,
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
            y_max=disp_config.get("y_max"),
            cursors_enabled=disp_config.get("cursors_enabled", False),
            cursor1_x=disp_config.get("cursor1_x"),
            cursor1_target_id=disp_config.get("cursor1_target_id"),
            cursor2_x=disp_config.get("cursor2_x"),
            cursor2_target_id=disp_config.get("cursor2_target_id"),
            ref_freq=disp_config.get("ref_freq", 50.0),
            show_cursor_overlay=disp_config.get("show_cursor_overlay", True)
        )

    def _update_fft_display(self, fft_id):
        fft_config = self.fft_objects.get(fft_id)
        if not fft_config: return

        plot_widget = self.center_tabview.get_plot_widget(fft_id)
        if not plot_widget: return

        selected_sig_ids = fft_config.get("selected_signal_ids", set())
        if not isinstance(selected_sig_ids, set):
            selected_sig_ids = set(selected_sig_ids)

        if not selected_sig_ids and fft_config.get("source_signal_id"):
            selected_sig_ids = {fft_config["source_signal_id"]}
            fft_config["selected_signal_ids"] = selected_sig_ids

        signals_to_plot = []
        computed_spectrums = {}
        first_freqs = None
        first_amp = None

        default_colors = ["#00f5d4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd", "#1f77b4", "#bcbd22"]

        for idx, sig_id in enumerate(selected_sig_ids):
            if sig_id in self.imported_signals:
                s_info = self.imported_signals[sig_id]
                df = s_info["df"]
                xv = df[s_info["x_col"]].values
                yv = df[s_info["y_col"]].values

                freqs, amplitude, _ = FFTAnalyzer.compute_fft(
                    xv, yv,
                    window_type=fft_config.get("window_type", "Hann"),
                    n_points=fft_config.get("n_points", "Auto"),
                    f_min=fft_config.get("f_min"),
                    f_max=fft_config.get("f_max")
                )

                computed_spectrums[sig_id] = {"freqs": freqs, "amplitude": amplitude, "name": s_info["name"]}

                if first_freqs is None and len(freqs) > 0:
                    first_freqs = freqs
                    first_amp = amplitude

                signals_to_plot.append({
                    "id": sig_id,
                    "name": f"FFT({s_info['name']})",
                    "x_data": freqs,
                    "y_data": amplitude,
                    "color": default_colors[idx % len(default_colors)]
                })

        fft_config["computed_spectrums"] = computed_spectrums
        if first_freqs is not None:
            fft_config["computed_freqs"] = first_freqs
            fft_config["computed_amplitude"] = first_amp

        # Detect peaks if enabled (on target or first signal)
        peaks = []
        if fft_config.get("peak_search_enabled") and first_freqs is not None and len(first_freqs) > 0:
            num_p = fft_config.get("num_peaks", 5)
            peaks = FFTAnalyzer.detect_peaks(first_freqs, first_amp, num_peaks=num_p)
            fft_config["detected_peaks"] = peaks
        else:
            fft_config["detected_peaks"] = []

        # Cursor target fallback
        c1_target = fft_config.get("cursor1_target_id")
        c2_target = fft_config.get("cursor2_target_id")
        avail_sig_list = list(selected_sig_ids)

        if not c1_target or c1_target not in selected_sig_ids:
            c1_target = avail_sig_list[0] if avail_sig_list else None
            fft_config["cursor1_target_id"] = c1_target

        if not c2_target or c2_target not in selected_sig_ids:
            c2_target = avail_sig_list[0] if avail_sig_list else None
            fft_config["cursor2_target_id"] = c2_target

        # Default cursor positions if enabled but cursor1_x is None
        if fft_config.get("cursors_enabled") and fft_config.get("cursor1_x") is None and first_freqs is not None and len(first_freqs) > 0:
            f_min_val = float(np.min(first_freqs))
            f_max_val = float(np.max(first_freqs))
            fft_config["cursor1_x"] = round(f_min_val + 0.25 * (f_max_val - f_min_val), 5)
            fft_config["cursor2_x"] = round(f_min_val + 0.75 * (f_max_val - f_min_val), 5)

        plot_widget.plot_multi_signals(
            signals_to_plot,
            title=fft_config.get("title", fft_config.get("name")),
            x_label=fft_config.get("x_label", "Fréquence (Hz)"),
            y_label=fft_config.get("y_label", "Amplitude"),
            linewidth=fft_config.get("linewidth", 1.2),
            linestyle=fft_config.get("linestyle", "-"),
            x_min=fft_config.get("x_min"),
            x_max=fft_config.get("x_max"),
            y_min=fft_config.get("y_min"),
            y_max=fft_config.get("y_max"),
            cursors_enabled=fft_config.get("cursors_enabled", False),
            cursor1_x=fft_config.get("cursor1_x"),
            cursor1_target_id=fft_config.get("cursor1_target_id"),
            cursor2_x=fft_config.get("cursor2_x"),
            cursor2_target_id=fft_config.get("cursor2_target_id"),
            ref_freq=fft_config.get("ref_freq", 50.0),
            show_cursor_overlay=fft_config.get("show_cursor_overlay", True),
            peaks=peaks if fft_config.get("peak_search_enabled") else None
        )

    def _on_change_scaling(self, choice_str):
        scale_val = float(choice_str.replace("%", "")) / 100.0
        settings.settings["ui_scaling"] = scale_val
        settings.save_settings()
        ctk.set_widget_scaling(scale_val)
        ctk.set_window_scaling(scale_val)

    def _on_property_changed(self, new_props): pass
    def _action_open_help(self): pass
