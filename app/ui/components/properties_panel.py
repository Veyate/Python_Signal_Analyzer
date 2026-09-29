"""
Panneau de propriétés dynamique adaptatif selon le type d'élément sélectionné :
- Signal brut (métadonnées + renommage)
- Affichage graphique (Général, Style, Curseurs)
- Analyse FFT (Général FFT multi-signaux, Style, Curseurs & Peak Search)
"""
import customtkinter as ctk
import numpy as np
from app.utils.i18n import _
from app.controllers.fft_analyzer import FFTAnalyzer

class PropertiesPanelFrame(ctk.CTkFrame):
    def __init__(self, parent, on_property_change=None, **kwargs):
        super().__init__(parent, **kwargs)
        self.on_property_change = on_property_change

        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.title_lbl = ctk.CTkLabel(self, text=_("properties_title"), font=ctk.CTkFont(size=12, weight="bold"))
        self.title_lbl.grid(row=0, column=0, padx=6, pady=3, sticky="w")

        self.container = ctk.CTkFrame(self, fg_color="transparent")
        self.container.grid(row=1, column=0, sticky="nsew", padx=2, pady=2)
        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)

        self.current_item_id = None
        self.current_item_type = None
        self.active_tab_name = None
        self.current_tabview = None
        self.show_empty()

    def show_empty(self):
        for widget in self.container.winfo_children():
            widget.destroy()
        lbl = ctk.CTkLabel(self.container, text=_("empty_selection"), text_color="gray", font=ctk.CTkFont(size=10))
        lbl.pack(pady=15, padx=4)

    # --- 1. PROPRIÉTÉS POUR SIGNAL BRUT ---
    def display_signal_properties(self, signal_id, signal_data, on_rename_callback=None):
        for widget in self.container.winfo_children():
            widget.destroy()

        self.current_item_id = signal_id
        self.current_item_type = "signal"
        self.current_tabview = None

        scroll_frame = ctk.CTkScrollableFrame(self.container)
        scroll_frame.pack(fill="both", expand=True, padx=2, pady=2)

        ctk.CTkLabel(scroll_frame, text=_("imported_signal_header"), font=ctk.CTkFont(size=11, weight="bold")).pack(anchor="w", pady=(2, 6))

        ctk.CTkLabel(scroll_frame, text=_("signal_name"), font=ctk.CTkFont(size=10)).pack(anchor="w", pady=(2, 1))
        entry_sig_name = ctk.CTkEntry(scroll_frame, font=ctk.CTkFont(size=10))
        entry_sig_name.insert(0, signal_data.get("name", ""))
        entry_sig_name.pack(fill="x", pady=(0, 6))

        if on_rename_callback:
            def _apply_rename(event=None):
                new_val = entry_sig_name.get().strip()
                if new_val:
                    on_rename_callback(signal_id, new_val)

            entry_sig_name.bind("<Return>", _apply_rename)
            entry_sig_name.bind("<FocusOut>", _apply_rename)

        points_cnt = len(signal_data["df"]) if "df" in signal_data and signal_data["df"] is not None else 0
        ctk.CTkLabel(scroll_frame, text=_("points_count"), font=ctk.CTkFont(size=10)).pack(anchor="w")
        lbl_pts = ctk.CTkLabel(scroll_frame, text=str(points_cnt), fg_color="#1f1f1f", corner_radius=3, font=ctk.CTkFont(size=10))
        lbl_pts.pack(fill="x", pady=(0, 5))

        ctk.CTkLabel(scroll_frame, text=_("axis_x"), font=ctk.CTkFont(size=10)).pack(anchor="w")
        lbl_x = ctk.CTkLabel(scroll_frame, text=signal_data.get("x_col", "-"), fg_color="#1f1f1f", corner_radius=3, font=ctk.CTkFont(size=10))
        lbl_x.pack(fill="x", pady=(0, 5))

        ctk.CTkLabel(scroll_frame, text=_("axis_y"), font=ctk.CTkFont(size=10)).pack(anchor="w")
        lbl_y = ctk.CTkLabel(scroll_frame, text=signal_data.get("y_col", "-"), fg_color="#1f1f1f", corner_radius=3, font=ctk.CTkFont(size=10))
        lbl_y.pack(fill="x", pady=(0, 5))

    # --- 2. PROPRIÉTÉS POUR AFFICHEUR GRAPHIQUE ---
    def display_display_properties(self, display_id, display_config, available_signals,
                                   is_pinned, on_pin_toggle_callback,
                                   on_signals_toggle_callback, on_prop_change_callback):
        if self.current_tabview is not None:
            try:
                curr = self.current_tabview.get()
                if curr: self.active_tab_name = curr
            except Exception: pass

        for widget in self.container.winfo_children():
            widget.destroy()

        self.current_item_id = display_id
        self.current_item_type = "display"

        def _on_tab_changed(selected_tab):
            self.active_tab_name = selected_tab

        tabview = ctk.CTkTabview(self.container, width=80, command=_on_tab_changed)
        tabview.pack(fill="both", expand=True)
        self.current_tabview = tabview

        tab_gen_name = _("tab_gen")
        tab_custom_name = _("tab_style")
        tab_cursor_name = _("tab_cursors")

        tabview.add(tab_gen_name)
        tabview.add(tab_custom_name)
        tabview.add(tab_cursor_name)

        if self.active_tab_name in [tab_gen_name, tab_custom_name, tab_cursor_name]:
            tabview.set(self.active_tab_name)

        # --- ONGLET 1 : GÉNÉRAL ---
        tab_gen = tabview.tab(tab_gen_name)
        scroll_gen = ctk.CTkScrollableFrame(tab_gen)
        scroll_gen.pack(fill="both", expand=True)

        chk_pin_var = ctk.BooleanVar(value=is_pinned)
        chk_pin = ctk.CTkCheckBox(
            scroll_gen, text=_("pin_tab"), variable=chk_pin_var, font=ctk.CTkFont(size=10, weight="bold"),
            command=lambda: on_pin_toggle_callback(_("tab_plot_prefix", display_config.get('name')), chk_pin_var.get())
        )
        chk_pin.pack(anchor="w", pady=(2, 10))

        ctk.CTkLabel(scroll_gen, text=_("curves_to_display"), font=ctk.CTkFont(size=10, weight="bold")).pack(anchor="w", pady=(4, 2))

        selected_signal_ids = display_config.get("selected_signal_ids", set())
        if not isinstance(selected_signal_ids, set):
            selected_signal_ids = set(selected_signal_ids)

        if not available_signals:
            ctk.CTkLabel(scroll_gen, text=_("no_signal_imported"), text_color="gray", font=ctk.CTkFont(size=10)).pack(anchor="w")
        else:
            for sig_id, sig_info in available_signals.items():
                var = ctk.BooleanVar(value=(sig_id in selected_signal_ids))
                chk_sig = ctk.CTkCheckBox(
                    scroll_gen, text=sig_info["name"], variable=var, font=ctk.CTkFont(size=10),
                    command=lambda sid=sig_id, v=var: on_signals_toggle_callback(display_id, sid, v.get())
                )
                chk_sig.pack(anchor="w", pady=3)

        # --- ONGLET 2 : STYLE & LIMITES DES AXES ---
        tab_cust = tabview.tab(tab_custom_name)
        scroll_cust = ctk.CTkScrollableFrame(tab_cust)
        scroll_cust.pack(fill="both", expand=True)

        # Titre
        ctk.CTkLabel(scroll_cust, text=_("graph_title"), font=ctk.CTkFont(size=10)).pack(anchor="w", pady=(2, 1))
        entry_title = ctk.CTkEntry(scroll_cust, font=ctk.CTkFont(size=10))
        entry_title.insert(0, display_config.get("title", display_config.get("name", "Graphique")))
        entry_title.pack(fill="x", pady=(0, 6))

        def _apply_title_change(event=None):
            new_title = entry_title.get().strip()
            if new_title: on_prop_change_callback(display_id, "name", new_title)

        entry_title.bind("<Return>", _apply_title_change)
        entry_title.bind("<FocusOut>", _apply_title_change)

        # Axe X Libellé
        ctk.CTkLabel(scroll_cust, text=_("label_axis_x"), font=ctk.CTkFont(size=10)).pack(anchor="w", pady=(2, 1))
        entry_x = ctk.CTkEntry(scroll_cust, font=ctk.CTkFont(size=10))
        entry_x.insert(0, display_config.get("x_label", "Temps"))
        entry_x.pack(fill="x", pady=(0, 6))

        def _apply_x_label(e=None): on_prop_change_callback(display_id, "x_label", entry_x.get())
        entry_x.bind("<Return>", _apply_x_label)
        entry_x.bind("<FocusOut>", _apply_x_label)

        # Axe Y Libellé
        ctk.CTkLabel(scroll_cust, text=_("label_axis_y"), font=ctk.CTkFont(size=10)).pack(anchor="w", pady=(2, 1))
        entry_y = ctk.CTkEntry(scroll_cust, font=ctk.CTkFont(size=10))
        entry_y.insert(0, display_config.get("y_label", "Amplitude"))
        entry_y.pack(fill="x", pady=(0, 6))

        def _apply_y_label(e=None): on_prop_change_callback(display_id, "y_label", entry_y.get())
        entry_y.bind("<Return>", _apply_y_label)
        entry_y.bind("<FocusOut>", _apply_y_label)

        # LIMITES DES AXES (ZOOM PERMANENT)
        ctk.CTkLabel(scroll_cust, text=_("zoom_limits"), font=ctk.CTkFont(size=10, weight="bold")).pack(anchor="w", pady=(6, 2))

        lim_grid = ctk.CTkFrame(scroll_cust, fg_color="transparent")
        lim_grid.pack(fill="x", pady=(0, 4))

        ctk.CTkLabel(lim_grid, text="X min:", font=ctk.CTkFont(size=10)).grid(row=0, column=0, sticky="w", padx=(0, 1))
        entry_xmin = ctk.CTkEntry(lim_grid, font=ctk.CTkFont(size=10), width=42)
        entry_xmin.grid(row=0, column=1, padx=(0, 3), pady=2)
        if display_config.get("x_min") is not None: entry_xmin.insert(0, str(display_config["x_min"]))

        ctk.CTkLabel(lim_grid, text="X max:", font=ctk.CTkFont(size=10)).grid(row=0, column=2, sticky="w", padx=(0, 1))
        entry_xmax = ctk.CTkEntry(lim_grid, font=ctk.CTkFont(size=10), width=42)
        entry_xmax.grid(row=0, column=3, pady=2)
        if display_config.get("x_max") is not None: entry_xmax.insert(0, str(display_config["x_max"]))

        ctk.CTkLabel(lim_grid, text="Y min:", font=ctk.CTkFont(size=10)).grid(row=1, column=0, sticky="w", padx=(0, 1))
        entry_ymin = ctk.CTkEntry(lim_grid, font=ctk.CTkFont(size=10), width=42)
        entry_ymin.grid(row=1, column=1, padx=(0, 3), pady=2)
        if display_config.get("y_min") is not None: entry_ymin.insert(0, str(display_config["y_min"]))

        ctk.CTkLabel(lim_grid, text="Y max:", font=ctk.CTkFont(size=10)).grid(row=1, column=2, sticky="w", padx=(0, 1))
        entry_ymax = ctk.CTkEntry(lim_grid, font=ctk.CTkFont(size=10), width=42)
        entry_ymax.grid(row=1, column=3, pady=2)
        if display_config.get("y_max") is not None: entry_ymax.insert(0, str(display_config["y_max"]))

        def _apply_limits():
            def _parse_val(val_str):
                try:
                    s = val_str.strip()
                    return float(s) if s else None
                except Exception: return None
            on_prop_change_callback(display_id, "x_min", _parse_val(entry_xmin.get()))
            on_prop_change_callback(display_id, "x_max", _parse_val(entry_xmax.get()))
            on_prop_change_callback(display_id, "y_min", _parse_val(entry_ymin.get()))
            on_prop_change_callback(display_id, "y_max", _parse_val(entry_ymax.get()))

        for ent in [entry_xmin, entry_xmax, entry_ymin, entry_ymax]:
            ent.bind("<Return>", lambda e: _apply_limits())
            ent.bind("<FocusOut>", lambda e: _apply_limits())

        btn_apply_lim = ctk.CTkButton(
            scroll_cust, text=_("apply_limits"), font=ctk.CTkFont(size=10), height=22, fg_color="#2b5b84",
            command=_apply_limits
        )
        btn_apply_lim.pack(fill="x", pady=(2, 4))

        def _reset_limits():
            entry_xmin.delete(0, "end"); entry_xmax.delete(0, "end")
            entry_ymin.delete(0, "end"); entry_ymax.delete(0, "end")
            on_prop_change_callback(display_id, "x_min", None); on_prop_change_callback(display_id, "x_max", None)
            on_prop_change_callback(display_id, "y_min", None); on_prop_change_callback(display_id, "y_max", None)

        btn_reset_lim = ctk.CTkButton(
            scroll_cust, text=_("reset_axes"), font=ctk.CTkFont(size=10), height=22, fg_color="gray30", hover_color="gray40",
            command=_reset_limits
        )
        btn_reset_lim.pack(fill="x", pady=(0, 8))

        # Épaisseur
        ctk.CTkLabel(scroll_cust, text=_("line_width"), font=ctk.CTkFont(size=10)).pack(anchor="w", pady=(2, 1))
        lbl_width_val = ctk.CTkLabel(scroll_cust, text=f"{display_config.get('linewidth', 1.2):.1f} px", font=ctk.CTkFont(size=10))
        lbl_width_val.pack(anchor="e")

        def _on_slider_width(val):
            lbl_width_val.configure(text=f"{val:.1f} px")
            on_prop_change_callback(display_id, "linewidth", round(val, 1))

        slider_width = ctk.CTkSlider(scroll_cust, from_=0.5, to=5.0, number_of_steps=45, command=_on_slider_width)
        slider_width.set(display_config.get("linewidth", 1.2))
        slider_width.pack(fill="x", pady=(0, 8))

        # Style de ligne
        ctk.CTkLabel(scroll_cust, text=_("line_style"), font=ctk.CTkFont(size=10)).pack(anchor="w", pady=(2, 1))
        style_map = {"Continu (-)": "-", "Pointillé (--)": "--", "Points (..)": ":", "Tiret-Point (-.)": "-."}
        combo_style = ctk.CTkOptionMenu(
            scroll_cust, values=list(style_map.keys()), font=ctk.CTkFont(size=10),
            command=lambda chosen: on_prop_change_callback(display_id, "linestyle", style_map.get(chosen, "-"))
        )
        current_st = display_config.get("linestyle", "-")
        for k, v in style_map.items():
            if v == current_st: combo_style.set(k); break
        combo_style.pack(fill="x", pady=(0, 8))

        # --- ONGLET 3 : CURSEURS & MESURES ---
        self._build_cursors_tab_content(tabview.tab(tab_cursor_name), display_id, display_config, available_signals, selected_signal_ids, on_prop_change_callback, is_fft=False)

    # --- 3. PROPRIÉTÉS POUR ANALYSE FFT ---
    def display_fft_properties(self, fft_id, fft_config, available_signals,
                               is_pinned, on_pin_toggle_callback, on_signals_toggle_callback, on_prop_change_callback):
        if self.current_tabview is not None:
            try:
                curr = self.current_tabview.get()
                if curr: self.active_tab_name = curr
            except Exception: pass

        for widget in self.container.winfo_children():
            widget.destroy()

        self.current_item_id = fft_id
        self.current_item_type = "fft"

        def _on_tab_changed(selected_tab):
            self.active_tab_name = selected_tab

        tabview = ctk.CTkTabview(self.container, width=80, command=_on_tab_changed)
        tabview.pack(fill="both", expand=True)
        self.current_tabview = tabview

        tab_gen_name = _("tab_gen")
        tab_custom_name = _("tab_style")
        tab_cursor_name = _("tab_cursors")

        tabview.add(tab_gen_name)
        tabview.add(tab_custom_name)
        tabview.add(tab_cursor_name)

        if self.active_tab_name in [tab_gen_name, tab_custom_name, tab_cursor_name]:
            tabview.set(self.active_tab_name)

        # --- ONGLET 1 : GÉNÉRAL FFT ---
        tab_gen = tabview.tab(tab_gen_name)
        scroll_gen = ctk.CTkScrollableFrame(tab_gen)
        scroll_gen.pack(fill="both", expand=True)

        chk_pin_var = ctk.BooleanVar(value=is_pinned)
        chk_pin = ctk.CTkCheckBox(
            scroll_gen, text=_("pin_tab"), variable=chk_pin_var, font=ctk.CTkFont(size=10, weight="bold"),
            command=lambda: on_pin_toggle_callback(_("tab_fft_prefix", fft_config.get('name')), chk_pin_var.get())
        )
        chk_pin.pack(anchor="w", pady=(2, 10))

        # Signaux Sources pour la FFT (Multisélection pour comparaison)
        ctk.CTkLabel(scroll_gen, text=_("curves_to_display"), font=ctk.CTkFont(size=10, weight="bold")).pack(anchor="w", pady=(4, 2))

        selected_signal_ids = fft_config.get("selected_signal_ids", set())
        if not isinstance(selected_signal_ids, set):
            selected_signal_ids = set(selected_signal_ids)

        if not available_signals:
            ctk.CTkLabel(scroll_gen, text=_("no_signal_imported"), text_color="gray", font=ctk.CTkFont(size=10)).pack(anchor="w")
        else:
            for sig_id, sig_info in available_signals.items():
                var = ctk.BooleanVar(value=(sig_id in selected_signal_ids))
                chk_sig = ctk.CTkCheckBox(
                    scroll_gen, text=sig_info["name"], variable=var, font=ctk.CTkFont(size=10),
                    command=lambda sid=sig_id, v=var: on_signals_toggle_callback(fft_id, sid, v.get())
                )
                chk_sig.pack(anchor="w", pady=3)

        # Fenêtrage
        ctk.CTkLabel(scroll_gen, text=_("fft_window_type"), font=ctk.CTkFont(size=10, weight="bold")).pack(anchor="w", pady=(8, 1))
        combo_win = ctk.CTkOptionMenu(
            scroll_gen, values=FFTAnalyzer.WINDOW_TYPES, font=ctk.CTkFont(size=10),
            command=lambda w: on_prop_change_callback(fft_id, "window_type", w)
        )
        combo_win.set(fft_config.get("window_type", "Hann"))
        combo_win.pack(fill="x", pady=(0, 8))

        # Nombre de points N
        ctk.CTkLabel(scroll_gen, text=_("fft_n_points"), font=ctk.CTkFont(size=10, weight="bold")).pack(anchor="w", pady=(2, 1))
        combo_n = ctk.CTkOptionMenu(
            scroll_gen, values=FFTAnalyzer.N_POINTS_OPTIONS, font=ctk.CTkFont(size=10),
            command=lambda n: on_prop_change_callback(fft_id, "n_points", n)
        )
        combo_n.set(str(fft_config.get("n_points", "Auto")))
        combo_n.pack(fill="x", pady=(0, 8))

        # Plage fréquentielle f_min / f_max
        ctk.CTkLabel(scroll_gen, text=_("fft_freq_range"), font=ctk.CTkFont(size=10, weight="bold")).pack(anchor="w", pady=(4, 1))

        # Calcul limite théorique fs/2
        fs_th = 1000.0
        if selected_signal_ids:
            first_sid = list(selected_signal_ids)[0]
            if first_sid in available_signals:
                df_s = available_signals[first_sid]["df"]
                x_c = available_signals[first_sid]["x_col"]
                xv = df_s[x_c].values
                if len(xv) > 1:
                    dt = float(np.mean(np.diff(xv)))
                    if dt > 0: fs_th = 1.0 / dt

        lbl_th = ctk.CTkLabel(scroll_gen, text=_("fft_theoretical_bounds", fs_th / 2.0), font=ctk.CTkFont(size=9), text_color="gray70")
        lbl_th.pack(anchor="w", pady=(0, 4))

        f_grid = ctk.CTkFrame(scroll_gen, fg_color="transparent")
        f_grid.pack(fill="x", pady=(0, 4))

        ctk.CTkLabel(f_grid, text=_("fft_fmin"), font=ctk.CTkFont(size=10)).grid(row=0, column=0, sticky="w")
        entry_fmin = ctk.CTkEntry(f_grid, font=ctk.CTkFont(size=10), width=55)
        entry_fmin.grid(row=0, column=1, padx=(4, 8))
        if fft_config.get("f_min") is not None: entry_fmin.insert(0, str(fft_config["f_min"]))

        ctk.CTkLabel(f_grid, text=_("fft_fmax"), font=ctk.CTkFont(size=10)).grid(row=0, column=2, sticky="w")
        entry_fmax = ctk.CTkEntry(f_grid, font=ctk.CTkFont(size=10), width=55)
        entry_fmax.grid(row=0, column=3, padx=(4, 0))
        if fft_config.get("f_max") is not None: entry_fmax.insert(0, str(fft_config["f_max"]))

        def _apply_freq_range():
            def _p(s):
                try: return float(s.strip()) if s.strip() else None
                except Exception: return None
            on_prop_change_callback(fft_id, "f_min", _p(entry_fmin.get()))
            on_prop_change_callback(fft_id, "f_max", _p(entry_fmax.get()))

        entry_fmin.bind("<Return>", lambda e: _apply_freq_range())
        entry_fmin.bind("<FocusOut>", lambda e: _apply_freq_range())
        entry_fmax.bind("<Return>", lambda e: _apply_freq_range())
        entry_fmax.bind("<FocusOut>", lambda e: _apply_freq_range())

        btn_app_f = ctk.CTkButton(scroll_gen, text=_("apply_limits"), font=ctk.CTkFont(size=10), height=22, fg_color="#2b5b84", command=_apply_freq_range)
        btn_app_f.pack(fill="x", pady=(2, 4))

        # --- ONGLET 2 : STYLE FFT ---
        tab_cust = tabview.tab(tab_custom_name)
        scroll_cust = ctk.CTkScrollableFrame(tab_cust)
        scroll_cust.pack(fill="both", expand=True)

        ctk.CTkLabel(scroll_cust, text=_("fft_name_title"), font=ctk.CTkFont(size=10)).pack(anchor="w", pady=(2, 1))
        entry_title = ctk.CTkEntry(scroll_cust, font=ctk.CTkFont(size=10))
        entry_title.insert(0, fft_config.get("title", fft_config.get("name", "FFT")))
        entry_title.pack(fill="x", pady=(0, 6))

        def _apply_fft_title_change(event=None):
            new_t = entry_title.get().strip()
            if new_t: on_prop_change_callback(fft_id, "name", new_t)

        entry_title.bind("<Return>", _apply_fft_title_change)
        entry_title.bind("<FocusOut>", _apply_fft_title_change)

        # Axis Labels
        ctk.CTkLabel(scroll_cust, text=_("label_axis_x"), font=ctk.CTkFont(size=10)).pack(anchor="w", pady=(2, 1))
        entry_x = ctk.CTkEntry(scroll_cust, font=ctk.CTkFont(size=10))
        entry_x.insert(0, fft_config.get("x_label", "Fréquence (Hz)"))
        entry_x.pack(fill="x", pady=(0, 6))

        def _apply_fft_x_label(e=None): on_prop_change_callback(fft_id, "x_label", entry_x.get())
        entry_x.bind("<Return>", _apply_fft_x_label)
        entry_x.bind("<FocusOut>", _apply_fft_x_label)

        ctk.CTkLabel(scroll_cust, text=_("label_axis_y"), font=ctk.CTkFont(size=10)).pack(anchor="w", pady=(2, 1))
        entry_y = ctk.CTkEntry(scroll_cust, font=ctk.CTkFont(size=10))
        entry_y.insert(0, fft_config.get("y_label", "Amplitude"))
        entry_y.pack(fill="x", pady=(0, 6))

        def _apply_fft_y_label(e=None): on_prop_change_callback(fft_id, "y_label", entry_y.get())
        entry_y.bind("<Return>", _apply_fft_y_label)
        entry_y.bind("<FocusOut>", _apply_fft_y_label)

        # Zoom limits
        ctk.CTkLabel(scroll_cust, text=_("zoom_limits"), font=ctk.CTkFont(size=10, weight="bold")).pack(anchor="w", pady=(6, 2))
        lim_grid = ctk.CTkFrame(scroll_cust, fg_color="transparent")
        lim_grid.pack(fill="x", pady=(0, 4))

        ctk.CTkLabel(lim_grid, text="X min:", font=ctk.CTkFont(size=10)).grid(row=0, column=0, sticky="w", padx=(0, 1))
        entry_xmin = ctk.CTkEntry(lim_grid, font=ctk.CTkFont(size=10), width=42)
        entry_xmin.grid(row=0, column=1, padx=(0, 3), pady=2)
        if fft_config.get("x_min") is not None: entry_xmin.insert(0, str(fft_config["x_min"]))

        ctk.CTkLabel(lim_grid, text="X max:", font=ctk.CTkFont(size=10)).grid(row=0, column=2, sticky="w", padx=(0, 1))
        entry_xmax = ctk.CTkEntry(lim_grid, font=ctk.CTkFont(size=10), width=42)
        entry_xmax.grid(row=0, column=3, pady=2)
        if fft_config.get("x_max") is not None: entry_xmax.insert(0, str(fft_config["x_max"]))

        ctk.CTkLabel(lim_grid, text="Y min:", font=ctk.CTkFont(size=10)).grid(row=1, column=0, sticky="w", padx=(0, 1))
        entry_ymin = ctk.CTkEntry(lim_grid, font=ctk.CTkFont(size=10), width=42)
        entry_ymin.grid(row=1, column=1, padx=(0, 3), pady=2)
        if fft_config.get("y_min") is not None: entry_ymin.insert(0, str(fft_config["y_min"]))

        ctk.CTkLabel(lim_grid, text="Y max:", font=ctk.CTkFont(size=10)).grid(row=1, column=2, sticky="w", padx=(0, 1))
        entry_ymax = ctk.CTkEntry(lim_grid, font=ctk.CTkFont(size=10), width=42)
        entry_ymax.grid(row=1, column=3, pady=2)
        if fft_config.get("y_max") is not None: entry_ymax.insert(0, str(fft_config["y_max"]))

        def _apply_fft_zoom_limits():
            def _p(s):
                try: return float(s.strip()) if s.strip() else None
                except Exception: return None
            on_prop_change_callback(fft_id, "x_min", _p(entry_xmin.get()))
            on_prop_change_callback(fft_id, "x_max", _p(entry_xmax.get()))
            on_prop_change_callback(fft_id, "y_min", _p(entry_ymin.get()))
            on_prop_change_callback(fft_id, "y_max", _p(entry_ymax.get()))

        for ent in [entry_xmin, entry_xmax, entry_ymin, entry_ymax]:
            ent.bind("<Return>", lambda e: _apply_fft_zoom_limits())
            ent.bind("<FocusOut>", lambda e: _apply_fft_zoom_limits())

        btn_app_z = ctk.CTkButton(scroll_cust, text=_("apply_limits"), font=ctk.CTkFont(size=10), height=22, fg_color="#2b5b84", command=_apply_fft_zoom_limits)
        btn_app_z.pack(fill="x", pady=(2, 4))

        def _reset_fft_limits():
            entry_xmin.delete(0, "end"); entry_xmax.delete(0, "end")
            entry_ymin.delete(0, "end"); entry_ymax.delete(0, "end")
            on_prop_change_callback(fft_id, "x_min", None); on_prop_change_callback(fft_id, "x_max", None)
            on_prop_change_callback(fft_id, "y_min", None); on_prop_change_callback(fft_id, "y_max", None)

        btn_reset_lim = ctk.CTkButton(
            scroll_cust, text=_("reset_axes"), font=ctk.CTkFont(size=10), height=22, fg_color="gray30", hover_color="gray40",
            command=_reset_fft_limits
        )
        btn_reset_lim.pack(fill="x", pady=(0, 8))

        # Épaisseur & Style
        ctk.CTkLabel(scroll_cust, text=_("line_width"), font=ctk.CTkFont(size=10)).pack(anchor="w", pady=(2, 1))
        lbl_w_val = ctk.CTkLabel(scroll_cust, text=f"{fft_config.get('linewidth', 1.2):.1f} px", font=ctk.CTkFont(size=10))
        lbl_w_val.pack(anchor="e")

        def _on_slider_w(val):
            lbl_w_val.configure(text=f"{val:.1f} px")
            on_prop_change_callback(fft_id, "linewidth", round(val, 1))

        slider_w = ctk.CTkSlider(scroll_cust, from_=0.5, to=5.0, number_of_steps=45, command=_on_slider_w)
        slider_w.set(fft_config.get("linewidth", 1.2))
        slider_w.pack(fill="x", pady=(0, 8))

        # Style de ligne
        ctk.CTkLabel(scroll_cust, text=_("line_style"), font=ctk.CTkFont(size=10)).pack(anchor="w", pady=(2, 1))
        style_map = {"Continu (-)": "-", "Pointillé (--)": "--", "Points (..)": ":", "Tiret-Point (-.)": "-."}
        combo_style = ctk.CTkOptionMenu(
            scroll_cust, values=list(style_map.keys()), font=ctk.CTkFont(size=10),
            command=lambda chosen: on_prop_change_callback(fft_id, "linestyle", style_map.get(chosen, "-"))
        )
        current_st = fft_config.get("linestyle", "-")
        for k, v in style_map.items():
            if v == current_st: combo_style.set(k); break
        combo_style.pack(fill="x", pady=(0, 8))

        # --- ONGLET 3 : CURSEURS & PEAK SEARCH ---
        tab_cur = tabview.tab(tab_cursor_name)
        scroll_cur = ctk.CTkScrollableFrame(tab_cur)
        scroll_cur.pack(fill="both", expand=True)

        self._build_cursors_tab_content(scroll_cur, fft_id, fft_config, available_signals, selected_signal_ids, on_prop_change_callback, is_fft=True)

    # --- HELPER RÉUTILISABLE POUR L'ONGLET CURSEURS & PEAKS ---
    def _build_cursors_tab_content(self, parent_scroll, item_id, item_config, available_signals, selected_signal_ids, on_prop_change_callback, is_fft=False):
        cursors_enabled = item_config.get("cursors_enabled", False)
        var_cur = ctk.BooleanVar(value=cursors_enabled)
        show_overlay = item_config.get("show_cursor_overlay", True)
        var_overlay = ctk.BooleanVar(value=show_overlay)

        # Build list of displayed signals
        displayed_signals = []
        for sid in selected_signal_ids:
            if sid in available_signals:
                displayed_signals.append((sid, available_signals[sid]["name"]))

        if not displayed_signals:
            ctk.CTkLabel(parent_scroll, text=_("no_curve_displayed"), text_color="gray", font=ctk.CTkFont(size=10)).pack(anchor="w", pady=(0, 6))
            return

        sig_names = [name for _, name in displayed_signals]

        c1_target_id = item_config.get("cursor1_target_id")
        if not any(sid == c1_target_id for sid, _ in displayed_signals):
            c1_target_id = displayed_signals[0][0]
            item_config["cursor1_target_id"] = c1_target_id

        c2_target_id = item_config.get("cursor2_target_id")
        if not any(sid == c2_target_id for sid, _ in displayed_signals):
            c2_target_id = displayed_signals[0][0]
            item_config["cursor2_target_id"] = c2_target_id

        # Extract X & Y vectors for cursor 1 and cursor 2
        if is_fft:
            comp_specs = item_config.get("computed_spectrums", {})
            c1_spec = comp_specs.get(c1_target_id, {})
            c2_spec = comp_specs.get(c2_target_id, {})

            x1_vec = c1_spec.get("freqs", np.array([]))
            y1_vec = c1_spec.get("amplitude", np.array([]))
            c1_sig_name = f"FFT({c1_spec.get('name', available_signals.get(c1_target_id, {}).get('name', ''))})"

            x2_vec = c2_spec.get("freqs", np.array([]))
            y2_vec = c2_spec.get("amplitude", np.array([]))
            c2_sig_name = f"FFT({c2_spec.get('name', available_signals.get(c2_target_id, {}).get('name', ''))})"
        else:
            sig1_data = available_signals.get(c1_target_id, available_signals[displayed_signals[0][0]])
            sig2_data = available_signals.get(c2_target_id, available_signals[displayed_signals[0][0]])

            x1_vec = sig1_data["df"][sig1_data["x_col"]].values
            y1_vec = sig1_data["df"][sig1_data["y_col"]].values
            x2_vec = sig2_data["df"][sig2_data["x_col"]].values
            y2_vec = sig2_data["df"][sig2_data["y_col"]].values

            c1_sig_name = sig1_data["name"]
            c2_sig_name = sig2_data["name"]

        x_min_data = 0.0
        x_max_data = 1.0
        if len(x1_vec) > 0 and len(x2_vec) > 0:
            x_min_data = float(min(np.min(x1_vec), np.min(x2_vec)))
            x_max_data = float(max(np.max(x1_vec), np.max(x2_vec)))

        def _on_toggle_cursors():
            enabled = var_cur.get()
            if enabled and (item_config.get("cursor1_x") is None or item_config.get("cursor2_x") is None):
                c1_init = round(x_min_data + 0.25 * (x_max_data - x_min_data), 5)
                c2_init = round(x_min_data + 0.75 * (x_max_data - x_min_data), 5)
                item_config["cursor1_x"] = c1_init
                item_config["cursor2_x"] = c2_init
                on_prop_change_callback(item_id, "cursor1_x", c1_init)
                on_prop_change_callback(item_id, "cursor2_x", c2_init)
            on_prop_change_callback(item_id, "cursors_enabled", enabled)

        def _on_toggle_overlay():
            on_prop_change_callback(item_id, "show_cursor_overlay", var_overlay.get())

        chk_cur = ctk.CTkCheckBox(
            parent_scroll, text=_("enable_cursors"), variable=var_cur, font=ctk.CTkFont(size=10, weight="bold"),
            command=_on_toggle_cursors
        )
        chk_cur.pack(anchor="w", pady=(2, 4))

        chk_overlay = ctk.CTkCheckBox(
            parent_scroll, text=_("show_overlay"), variable=var_overlay, font=ctk.CTkFont(size=10),
            command=_on_toggle_overlay
        )
        chk_overlay.pack(anchor="w", pady=(0, 8))

        # Peak Search section
        peak_enabled = item_config.get("peak_search_enabled", False)
        var_peak = ctk.BooleanVar(value=peak_enabled)

        def _on_toggle_peaks():
            on_prop_change_callback(item_id, "peak_search_enabled", var_peak.get())

        chk_peak = ctk.CTkCheckBox(
            parent_scroll, text=_("peak_search_title"), variable=var_peak, font=ctk.CTkFont(size=10, weight="bold"),
            command=_on_toggle_peaks
        )
        chk_peak.pack(anchor="w", pady=(0, 8))

        if var_peak.get():
            pk_frame = ctk.CTkFrame(parent_scroll, fg_color="#1f2421", corner_radius=5)
            pk_frame.pack(fill="x", pady=(0, 8), padx=1)

            ctk.CTkLabel(pk_frame, text=_("num_peaks_label"), font=ctk.CTkFont(size=10)).pack(side="left", padx=(6, 4), pady=4)
            combo_p_count = ctk.CTkOptionMenu(
                pk_frame, values=["1", "2", "3", "4", "5", "6", "8", "10"], width=60, font=ctk.CTkFont(size=10),
                command=lambda k: on_prop_change_callback(item_id, "num_peaks", int(k))
            )
            combo_p_count.set(str(item_config.get("num_peaks", 5)))
            combo_p_count.pack(side="left", padx=(0, 6), pady=4)

            # Table of peaks
            peaks_list = item_config.get("detected_peaks", [])
            if peaks_list:
                tbl_frame = ctk.CTkFrame(parent_scroll, fg_color="#181818", corner_radius=5)
                tbl_frame.pack(fill="x", pady=(0, 8), padx=1)

                ctk.CTkLabel(tbl_frame, text=_("peak_table_header"), font=ctk.CTkFont(size=10, weight="bold"), text_color="#ffb703").pack(anchor="w", padx=6, pady=(4, 2))

                hdr_grid = ctk.CTkFrame(tbl_frame, fg_color="transparent")
                hdr_grid.pack(fill="x", padx=6, pady=(0, 2))

                ctk.CTkLabel(hdr_grid, text=_("peak_rank"), font=ctk.CTkFont(size=9, weight="bold"), width=35, anchor="w").grid(row=0, column=0)
                ctk.CTkLabel(hdr_grid, text=_("peak_freq"), font=ctk.CTkFont(size=9, weight="bold"), width=80, anchor="e").grid(row=0, column=1)
                ctk.CTkLabel(hdr_grid, text=_("peak_amp"), font=ctk.CTkFont(size=9, weight="bold"), width=70, anchor="e").grid(row=0, column=2)

                for p in peaks_list:
                    r_grid = ctk.CTkFrame(tbl_frame, fg_color="transparent")
                    r_grid.pack(fill="x", padx=6, pady=1)

                    ctk.CTkLabel(r_grid, text=f"P{p['rank']}", font=ctk.CTkFont(size=9), text_color="#ffb703", width=35, anchor="w").grid(row=0, column=0)
                    ctk.CTkLabel(r_grid, text=f"{p['freq']:.2f}", font=ctk.CTkFont(family="monospace", size=9), width=80, anchor="e").grid(row=0, column=1)
                    ctk.CTkLabel(r_grid, text=f"{p['amplitude']:.3f}", font=ctk.CTkFont(family="monospace", size=9), width=70, anchor="e").grid(row=0, column=2)

        if len(sig_names) > 1:
            # Dropdown C1 Curve
            ctk.CTkLabel(parent_scroll, text=_("curve_c1"), font=ctk.CTkFont(size=10, weight="bold"), text_color="#ff4d4d").pack(anchor="w", pady=(2, 1))

            def _on_c1_sig_changed(chosen_name):
                for sid, name in displayed_signals:
                    if name == chosen_name:
                        on_prop_change_callback(item_id, "cursor1_target_id", sid)
                        break

            combo_c1_sig = ctk.CTkOptionMenu(
                parent_scroll, values=sig_names, font=ctk.CTkFont(size=10),
                command=_on_c1_sig_changed
            )
            c1_display_name = available_signals[c1_target_id]["name"] if c1_target_id in available_signals else sig_names[0]
            combo_c1_sig.set(c1_display_name)
            combo_c1_sig.pack(fill="x", pady=(0, 6))

            # Dropdown C2 Curve
            ctk.CTkLabel(parent_scroll, text=_("curve_c2"), font=ctk.CTkFont(size=10, weight="bold"), text_color="#00e676").pack(anchor="w", pady=(2, 1))

            def _on_c2_sig_changed(chosen_name):
                for sid, name in displayed_signals:
                    if name == chosen_name:
                        on_prop_change_callback(item_id, "cursor2_target_id", sid)
                        break

            combo_c2_sig = ctk.CTkOptionMenu(
                parent_scroll, values=sig_names, font=ctk.CTkFont(size=10),
                command=_on_c2_sig_changed
            )
            c2_display_name = available_signals[c2_target_id]["name"] if c2_target_id in available_signals else sig_names[0]
            combo_c2_sig.set(c2_display_name)
            combo_c2_sig.pack(fill="x", pady=(0, 10))

        if len(x1_vec) > 0 and len(x2_vec) > 0:
            # Reference Frequency for Phase
            f0_frame = ctk.CTkFrame(parent_scroll, fg_color="transparent")
            f0_frame.pack(fill="x", pady=(0, 8))
            ctk.CTkLabel(f0_frame, text=_("ref_freq_label"), font=ctk.CTkFont(size=10)).pack(side="left", padx=(0, 4))
            entry_f0 = ctk.CTkEntry(f0_frame, font=ctk.CTkFont(size=10), width=65)
            ref_f = item_config.get("ref_freq", 50.0)
            entry_f0.insert(0, str(ref_f))
            entry_f0.pack(side="left")

            def _on_f0_changed(event=None):
                try:
                    vf = float(entry_f0.get())
                    on_prop_change_callback(item_id, "ref_freq", vf)
                except ValueError: pass

            entry_f0.bind("<Return>", _on_f0_changed)
            entry_f0.bind("<FocusOut>", _on_f0_changed)

            c1_val = item_config.get("cursor1_x")
            if c1_val is None:
                c1_val = round(x_min_data + 0.25 * (x_max_data - x_min_data), 5)
                item_config["cursor1_x"] = c1_val

            c2_val = item_config.get("cursor2_x")
            if c2_val is None:
                c2_val = round(x_min_data + 0.75 * (x_max_data - x_min_data), 5)
                item_config["cursor2_x"] = c2_val

            if var_cur.get():
                # Card 1: Curseur 1 (Rouge)
                c1_card = ctk.CTkFrame(parent_scroll, fg_color="#221818", border_width=1, border_color="#ff4d4d", corner_radius=6)
                c1_card.pack(fill="x", pady=(0, 8), padx=1)

                lbl_c1_title = ctk.CTkLabel(c1_card, text=_("c1_card_title", c1_sig_name), font=ctk.CTkFont(size=10, weight="bold"), text_color="#ff4d4d")
                lbl_c1_title.pack(anchor="w", padx=6, pady=(4, 2))

                entry_c1 = ctk.CTkEntry(c1_card, font=ctk.CTkFont(size=10), height=22)
                entry_c1.insert(0, f"{c1_val:.5g}")
                entry_c1.pack(fill="x", padx=6, pady=(0, 2))

                lbl_c1_res = ctk.CTkLabel(c1_card, text="", font=ctk.CTkFont(family="monospace", size=10), text_color="#ff8080")
                lbl_c1_res.pack(anchor="w", padx=6, pady=(0, 4))

                # Card 2: Curseur 2 (Vert)
                c2_card = ctk.CTkFrame(parent_scroll, fg_color="#182218", border_width=1, border_color="#00e676", corner_radius=6)
                c2_card.pack(fill="x", pady=(0, 8), padx=1)

                lbl_c2_title = ctk.CTkLabel(c2_card, text=_("c2_card_title", c2_sig_name), font=ctk.CTkFont(size=10, weight="bold"), text_color="#00e676")
                lbl_c2_title.pack(anchor="w", padx=6, pady=(4, 2))

                entry_c2 = ctk.CTkEntry(c2_card, font=ctk.CTkFont(size=10), height=22)
                entry_c2.insert(0, f"{c2_val:.5g}")
                entry_c2.pack(fill="x", padx=6, pady=(0, 2))

                lbl_c2_res = ctk.CTkLabel(c2_card, text="", font=ctk.CTkFont(family="monospace", size=10), text_color="#80ffb4")
                lbl_c2_res.pack(anchor="w", padx=6, pady=(0, 4))

                # Card 3: Deltas & Phase (Cyan)
                delta_card = ctk.CTkFrame(parent_scroll, fg_color="#121e24", border_width=1, border_color="#00f5d4", corner_radius=6)
                delta_card.pack(fill="x", pady=(0, 8), padx=1)

                lbl_d_title = ctk.CTkLabel(delta_card, text=_("measures_deltas"), font=ctk.CTkFont(size=10, weight="bold"), text_color="#00f5d4")
                lbl_d_title.pack(anchor="w", padx=6, pady=(4, 4))

                grid_m = ctk.CTkFrame(delta_card, fg_color="transparent")
                grid_m.pack(fill="x", padx=6, pady=(0, 6))

                lbl_dx_v = ctk.CTkLabel(grid_m, text="", font=ctk.CTkFont(family="monospace", size=10, weight="bold"), text_color="#ffffff")
                lbl_freq_v = ctk.CTkLabel(grid_m, text="", font=ctk.CTkFont(family="monospace", size=10, weight="bold"), text_color="#00f5d4")
                lbl_dy_v = ctk.CTkLabel(grid_m, text="", font=ctk.CTkFont(family="monospace", size=10, weight="bold"), text_color="#ffffff")
                lbl_pdeg_v = ctk.CTkLabel(grid_m, text="", font=ctk.CTkFont(family="monospace", size=10, weight="bold"), text_color="#ffb703")
                lbl_prad_v = ctk.CTkLabel(grid_m, text="", font=ctk.CTkFont(family="monospace", size=10, weight="bold"), text_color="#ffb703")

                unit_x = "Hz" if is_fft else "s"
                unit_inv = "s" if is_fft else "Hz"

                ctk.CTkLabel(grid_m, text=_("delta_x_label"), font=ctk.CTkFont(size=10), text_color="gray70").grid(row=0, column=0, sticky="w")
                lbl_dx_v.grid(row=0, column=1, sticky="e", padx=(4,0))

                ctk.CTkLabel(grid_m, text=_("freq_label"), font=ctk.CTkFont(size=10), text_color="gray70").grid(row=1, column=0, sticky="w")
                lbl_freq_v.grid(row=1, column=1, sticky="e", padx=(4,0))

                ctk.CTkLabel(grid_m, text=_("delta_y_label"), font=ctk.CTkFont(size=10), text_color="gray70").grid(row=2, column=0, sticky="w")
                lbl_dy_v.grid(row=2, column=1, sticky="e", padx=(4,0))

                ctk.CTkLabel(grid_m, text=_("phase_deg_label"), font=ctk.CTkFont(size=10), text_color="gray70").grid(row=3, column=0, sticky="w")
                lbl_pdeg_v.grid(row=3, column=1, sticky="e", padx=(4,0))

                ctk.CTkLabel(grid_m, text=_("phase_rad_label"), font=ctk.CTkFont(size=10), text_color="gray70").grid(row=4, column=0, sticky="w")
                lbl_prad_v.grid(row=4, column=1, sticky="e", padx=(4,0))

                def _update_card_labels(cur1_val, cur2_val):
                    idx1 = np.argsort(x1_vec)
                    idx2 = np.argsort(x2_vec)

                    y1 = float(np.interp(cur1_val, x1_vec[idx1], y1_vec[idx1])) if len(x1_vec) > 0 else 0.0
                    y2 = float(np.interp(cur2_val, x2_vec[idx2], y2_vec[idx2])) if len(x2_vec) > 0 else 0.0

                    dx = cur2_val - cur1_val
                    dy = y2 - y1
                    f_val = 1.0 / abs(dx) if abs(dx) > 1e-12 else 0.0

                    f0_curr = item_config.get("ref_freq", 50.0)
                    if not f0_curr or f0_curr <= 0: f0_curr = 50.0

                    d_deg = 360.0 * f0_curr * dx
                    d_rad = 2.0 * np.pi * f0_curr * dx

                    lbl_c1_res.configure(text=f"X1 = {cur1_val:.4g}  |  Y1 = {y1:.4g}")
                    lbl_c2_res.configure(text=f"X2 = {cur2_val:.4g}  |  Y2 = {y2:.4g}")

                    lbl_dx_v.configure(text=f"{dx:.4g} {unit_x}")
                    lbl_freq_v.configure(text=f"{f_val:.4g} {unit_inv}")
                    lbl_dy_v.configure(text=f"{dy:.4g}")
                    lbl_pdeg_v.configure(text=f"{d_deg:.1f}°")
                    lbl_prad_v.configure(text=f"{d_rad:.3f} rad")

                _update_card_labels(c1_val, c2_val)

                def _on_c1_slider(v):
                    val = round(v, 5)
                    entry_c1.delete(0, "end"); entry_c1.insert(0, f"{val:.5g}")
                    _update_card_labels(val, item_config.get("cursor2_x", c2_val))
                    on_prop_change_callback(item_id, "cursor1_x", val)

                def _on_c2_slider(v):
                    val = round(v, 5)
                    entry_c2.delete(0, "end"); entry_c2.insert(0, f"{val:.5g}")
                    _update_card_labels(item_config.get("cursor1_x", c1_val), val)
                    on_prop_change_callback(item_id, "cursor2_x", val)

                def _on_c1_entry_commit(event=None):
                    try:
                        v = float(entry_c1.get())
                        slider_c1.set(v)
                        _update_card_labels(v, item_config.get("cursor2_x", c2_val))
                        on_prop_change_callback(item_id, "cursor1_x", v)
                    except ValueError: pass

                def _on_c2_entry_commit(event=None):
                    try:
                        v = float(entry_c2.get())
                        slider_c2.set(v)
                        _update_card_labels(item_config.get("cursor1_x", c1_val), v)
                        on_prop_change_callback(item_id, "cursor2_x", v)
                    except ValueError: pass

                entry_c1.bind("<Return>", _on_c1_entry_commit)
                entry_c1.bind("<FocusOut>", _on_c1_entry_commit)

                entry_c2.bind("<Return>", _on_c2_entry_commit)
                entry_c2.bind("<FocusOut>", _on_c2_entry_commit)

                slider_c1 = ctk.CTkSlider(c1_card, from_=x_min_data, to=x_max_data, number_of_steps=200, height=14, command=_on_c1_slider)
                slider_c1.set(c1_val)
                slider_c1.pack(fill="x", padx=6, pady=(0, 4))

                slider_c2 = ctk.CTkSlider(c2_card, from_=x_min_data, to=x_max_data, number_of_steps=200, height=14, command=_on_c2_slider)
                slider_c2.set(c2_val)
                slider_c2.pack(fill="x", padx=6, pady=(0, 4))
