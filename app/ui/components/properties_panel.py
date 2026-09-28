"""
Panneau de propriétés dynamique adaptatif selon le type d'élément sélectionné.
- Élément Signal (Données brutes) -> Renommage + Métadonnées
- Élément Affichage (Graphique) -> Onglets 'Général' et 'Style' avec zoom permanent (X/Y min/max).
"""
import customtkinter as ctk

class PropertiesPanelFrame(ctk.CTkFrame):
    def __init__(self, parent, on_property_change=None, **kwargs):
        super().__init__(parent, **kwargs)
        self.on_property_change = on_property_change

        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.title_lbl = ctk.CTkLabel(self, text="⚙️ Propriétés", font=ctk.CTkFont(size=12, weight="bold"))
        self.title_lbl.grid(row=0, column=0, padx=6, pady=3, sticky="w")

        self.container = ctk.CTkFrame(self, fg_color="transparent")
        self.container.grid(row=1, column=0, sticky="nsew", padx=2, pady=2)
        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)

        self.current_item_id = None
        self.current_item_type = None
        self.show_empty()

    def show_empty(self):
        for widget in self.container.winfo_children():
            widget.destroy()
        lbl = ctk.CTkLabel(self.container, text="Sélectionnez un élément dans la vue en arbre", text_color="gray", font=ctk.CTkFont(size=10))
        lbl.pack(pady=15, padx=4)

    # --- 1. PROPRIÉTÉS POUR SIGNAL BRUT ---
    def display_signal_properties(self, signal_id, signal_data, on_rename_callback=None):
        for widget in self.container.winfo_children():
            widget.destroy()

        self.current_item_id = signal_id
        self.current_item_type = "signal"

        scroll_frame = ctk.CTkScrollableFrame(self.container)
        scroll_frame.pack(fill="both", expand=True, padx=2, pady=2)

        ctk.CTkLabel(scroll_frame, text="📄 Signal Importé", font=ctk.CTkFont(size=11, weight="bold")).pack(anchor="w", pady=(2, 6))

        # Field to rename signal
        ctk.CTkLabel(scroll_frame, text="Nom du signal :", font=ctk.CTkFont(size=10)).pack(anchor="w", pady=(2, 1))
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
        ctk.CTkLabel(scroll_frame, text="Nombre de points :", font=ctk.CTkFont(size=10)).pack(anchor="w")
        lbl_pts = ctk.CTkLabel(scroll_frame, text=str(points_cnt), fg_color="#1f1f1f", corner_radius=3, font=ctk.CTkFont(size=10))
        lbl_pts.pack(fill="x", pady=(0, 5))

        ctk.CTkLabel(scroll_frame, text="Axe X :", font=ctk.CTkFont(size=10)).pack(anchor="w")
        lbl_x = ctk.CTkLabel(scroll_frame, text=signal_data.get("x_col", "-"), fg_color="#1f1f1f", corner_radius=3, font=ctk.CTkFont(size=10))
        lbl_x.pack(fill="x", pady=(0, 5))

        ctk.CTkLabel(scroll_frame, text="Axe Y :", font=ctk.CTkFont(size=10)).pack(anchor="w")
        lbl_y = ctk.CTkLabel(scroll_frame, text=signal_data.get("y_col", "-"), fg_color="#1f1f1f", corner_radius=3, font=ctk.CTkFont(size=10))
        lbl_y.pack(fill="x", pady=(0, 5))

    # --- 2. PROPRIÉTÉS POUR AFFICHEUR GRAPHIQUE ---
    def display_display_properties(self, display_id, display_config, available_signals,
                                   is_pinned, on_pin_toggle_callback,
                                   on_signals_toggle_callback, on_prop_change_callback):
        for widget in self.container.winfo_children():
            widget.destroy()

        self.current_item_id = display_id
        self.current_item_type = "display"

        tabview = ctk.CTkTabview(self.container, width=100)
        tabview.pack(fill="both", expand=True)

        tab_gen_name = "⚙️ Général"
        tab_custom_name = "🎨 Style"

        tabview.add(tab_gen_name)
        tabview.add(tab_custom_name)

        # --- ONGLET 1 : GÉNÉRAL ---
        tab_gen = tabview.tab(tab_gen_name)
        scroll_gen = ctk.CTkScrollableFrame(tab_gen)
        scroll_gen.pack(fill="both", expand=True)

        chk_pin_var = ctk.BooleanVar(value=is_pinned)
        chk_pin = ctk.CTkCheckBox(
            scroll_gen, text="📌 Épingler l'onglet", variable=chk_pin_var, font=ctk.CTkFont(size=10, weight="bold"),
            command=lambda: on_pin_toggle_callback(f"📈 {display_config.get('name')}", chk_pin_var.get())
        )
        chk_pin.pack(anchor="w", pady=(2, 10))

        ctk.CTkLabel(scroll_gen, text="Courbes à afficher :", font=ctk.CTkFont(size=10, weight="bold")).pack(anchor="w", pady=(4, 2))

        selected_signal_ids = display_config.get("selected_signal_ids", set())

        if not available_signals:
            ctk.CTkLabel(scroll_gen, text="(Aucun signal importé)", text_color="gray", font=ctk.CTkFont(size=10)).pack(anchor="w")
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

        # Titre du graph
        ctk.CTkLabel(scroll_cust, text="Nom / Titre du graph :", font=ctk.CTkFont(size=10)).pack(anchor="w", pady=(2, 1))
        entry_title = ctk.CTkEntry(scroll_cust, font=ctk.CTkFont(size=10))
        entry_title.insert(0, display_config.get("title", display_config.get("name", "Graphique")))
        entry_title.pack(fill="x", pady=(0, 6))

        def _apply_title_change(event=None):
            new_title = entry_title.get().strip()
            if new_title:
                on_prop_change_callback(display_id, "name", new_title)

        entry_title.bind("<Return>", _apply_title_change)
        entry_title.bind("<FocusOut>", _apply_title_change)

        # Axe X Libellé
        ctk.CTkLabel(scroll_cust, text="Libellé Axe X :", font=ctk.CTkFont(size=10)).pack(anchor="w", pady=(2, 1))
        entry_x = ctk.CTkEntry(scroll_cust, font=ctk.CTkFont(size=10))
        entry_x.insert(0, display_config.get("x_label", "Temps"))
        entry_x.pack(fill="x", pady=(0, 6))
        entry_x.bind("<Return>", lambda e: on_prop_change_callback(display_id, "x_label", entry_x.get()))

        # Axe Y Libellé
        ctk.CTkLabel(scroll_cust, text="Libellé Axe Y :", font=ctk.CTkFont(size=10)).pack(anchor="w", pady=(2, 1))
        entry_y = ctk.CTkEntry(scroll_cust, font=ctk.CTkFont(size=10))
        entry_y.insert(0, display_config.get("y_label", "Amplitude"))
        entry_y.pack(fill="x", pady=(0, 6))
        entry_y.bind("<Return>", lambda e: on_prop_change_callback(display_id, "y_label", entry_y.get()))

        # LIMITES DES AXES (ZOOM PERMANENT)
        ctk.CTkLabel(scroll_cust, text="Zoom & Limites des axes :", font=ctk.CTkFont(size=10, weight="bold")).pack(anchor="w", pady=(6, 2))

        lim_grid = ctk.CTkFrame(scroll_cust, fg_color="transparent")
        lim_grid.pack(fill="x", pady=(0, 4))

        ctk.CTkLabel(lim_grid, text="X min:", font=ctk.CTkFont(size=10)).grid(row=0, column=0, sticky="w", padx=(0, 1))
        entry_xmin = ctk.CTkEntry(lim_grid, font=ctk.CTkFont(size=10), width=42)
        entry_xmin.grid(row=0, column=1, padx=(0, 3), pady=2)
        if display_config.get("x_min") is not None:
            entry_xmin.insert(0, str(display_config["x_min"]))

        ctk.CTkLabel(lim_grid, text="X max:", font=ctk.CTkFont(size=10)).grid(row=0, column=2, sticky="w", padx=(0, 1))
        entry_xmax = ctk.CTkEntry(lim_grid, font=ctk.CTkFont(size=10), width=42)
        entry_xmax.grid(row=0, column=3, pady=2)
        if display_config.get("x_max") is not None:
            entry_xmax.insert(0, str(display_config["x_max"]))

        ctk.CTkLabel(lim_grid, text="Y min:", font=ctk.CTkFont(size=10)).grid(row=1, column=0, sticky="w", padx=(0, 1))
        entry_ymin = ctk.CTkEntry(lim_grid, font=ctk.CTkFont(size=10), width=42)
        entry_ymin.grid(row=1, column=1, padx=(0, 3), pady=2)
        if display_config.get("y_min") is not None:
            entry_ymin.insert(0, str(display_config["y_min"]))

        ctk.CTkLabel(lim_grid, text="Y max:", font=ctk.CTkFont(size=10)).grid(row=1, column=2, sticky="w", padx=(0, 1))
        entry_ymax = ctk.CTkEntry(lim_grid, font=ctk.CTkFont(size=10), width=42)
        entry_ymax.grid(row=1, column=3, pady=2)
        if display_config.get("y_max") is not None:
            entry_ymax.insert(0, str(display_config["y_max"]))

        def _apply_limits():
            def _parse_val(val_str):
                try:
                    s = val_str.strip()
                    return float(s) if s else None
                except Exception:
                    return None

            on_prop_change_callback(display_id, "x_min", _parse_val(entry_xmin.get()))
            on_prop_change_callback(display_id, "x_max", _parse_val(entry_xmax.get()))
            on_prop_change_callback(display_id, "y_min", _parse_val(entry_ymin.get()))
            on_prop_change_callback(display_id, "y_max", _parse_val(entry_ymax.get()))

        for ent in [entry_xmin, entry_xmax, entry_ymin, entry_ymax]:
            ent.bind("<Return>", lambda e: _apply_limits())

        btn_apply_lim = ctk.CTkButton(
            scroll_cust, text="Appliquer Limites", font=ctk.CTkFont(size=10), height=22, fg_color="#2b5b84",
            command=_apply_limits
        )
        btn_apply_lim.pack(fill="x", pady=(2, 4))

        def _reset_limits():
            entry_xmin.delete(0, "end")
            entry_xmax.delete(0, "end")
            entry_ymin.delete(0, "end")
            entry_ymax.delete(0, "end")
            on_prop_change_callback(display_id, "x_min", None)
            on_prop_change_callback(display_id, "x_max", None)
            on_prop_change_callback(display_id, "y_min", None)
            on_prop_change_callback(display_id, "y_max", None)

        btn_reset_lim = ctk.CTkButton(
            scroll_cust, text="↺ Réinitialiser Axes", font=ctk.CTkFont(size=10), height=22, fg_color="gray30", hover_color="gray40",
            command=_reset_limits
        )
        btn_reset_lim.pack(fill="x", pady=(0, 8))

        # Épaisseur
        ctk.CTkLabel(scroll_cust, text="Épaisseur de ligne :", font=ctk.CTkFont(size=10)).pack(anchor="w", pady=(2, 1))
        lbl_width_val = ctk.CTkLabel(scroll_cust, text=f"{display_config.get('linewidth', 1.2):.1f} px", font=ctk.CTkFont(size=10))
        lbl_width_val.pack(anchor="e")

        def _on_slider_width(val):
            lbl_width_val.configure(text=f"{val:.1f} px")
            on_prop_change_callback(display_id, "linewidth", round(val, 1))

        slider_width = ctk.CTkSlider(scroll_cust, from_=0.5, to=5.0, number_of_steps=45, command=_on_slider_width)
        slider_width.set(display_config.get("linewidth", 1.2))
        slider_width.pack(fill="x", pady=(0, 8))

        # Style de ligne
        ctk.CTkLabel(scroll_cust, text="Style de ligne :", font=ctk.CTkFont(size=10)).pack(anchor="w", pady=(2, 1))
        style_map = {"Continu (-)": "-", "Pointillé (--)": "--", "Points (..)": ":", "Tiret-Point (-.)": "-."}
        combo_style = ctk.CTkOptionMenu(
            scroll_cust, values=list(style_map.keys()), font=ctk.CTkFont(size=10),
            command=lambda chosen: on_prop_change_callback(display_id, "linestyle", style_map.get(chosen, "-"))
        )
        current_st = display_config.get("linestyle", "-")
        for k, v in style_map.items():
            if v == current_st:
                combo_style.set(k)
                break
        combo_style.pack(fill="x", pady=(0, 8))
