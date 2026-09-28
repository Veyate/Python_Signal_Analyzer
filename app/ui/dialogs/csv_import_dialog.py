"""
Dialogue d'importation CSV.
"""
import os
import customtkinter as ctk
from tkinter import filedialog, messagebox
from app.controllers.csv_importer import CSVImporter
from app.utils.i18n import _

class CSVImportDialog(ctk.CTkToplevel):
    def __init__(self, parent, on_import_callback=None):
        super().__init__(parent)
        self.parent = parent
        self.on_import_callback = on_import_callback

        self.title(_("menu_import"))
        self.geometry("620x480")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        self.file_path = ""
        self.columns = []
        self._create_widgets()

    def _create_widgets(self):
        file_frame = ctk.CTkFrame(self)
        file_frame.pack(fill="x", padx=12, pady=(12, 6))

        self.lbl_file_path = ctk.CTkLabel(file_frame, text="Aucun fichier sélectionné", anchor="w")
        self.lbl_file_path.pack(side="left", fill="x", expand=True, padx=8, pady=8)

        btn_browse = ctk.CTkButton(file_frame, text="Parcourir...", width=90, command=self._browse_file)
        btn_browse.pack(side="right", padx=8, pady=8)

        options_frame = ctk.CTkFrame(self)
        options_frame.pack(fill="x", padx=12, pady=4)

        ctk.CTkLabel(options_frame, text="Séparateur :").grid(row=0, column=0, padx=8, pady=8, sticky="w")
        self.combo_sep = ctk.CTkOptionMenu(
            options_frame, values=["; (Point-virgule)", ", (Virgule)", "\t (Tabulation)", "Espace"],
            command=self._update_preview
        )
        self.combo_sep.grid(row=0, column=1, padx=8, pady=8)

        ctk.CTkLabel(options_frame, text="Décimale :").grid(row=0, column=2, padx=8, pady=8, sticky="w")
        self.combo_dec = ctk.CTkOptionMenu(
            options_frame, values=[". (Point)", ", (Virgule)"],
            command=self._update_preview
        )
        self.combo_dec.grid(row=0, column=3, padx=8, pady=8)

        mapping_frame = ctk.CTkFrame(self)
        mapping_frame.pack(fill="x", padx=12, pady=4)

        ctk.CTkLabel(mapping_frame, text="Axe X (Temps) :").grid(row=0, column=0, padx=8, pady=8, sticky="w")
        self.combo_x_col = ctk.CTkOptionMenu(mapping_frame, values=["---"])
        self.combo_x_col.grid(row=0, column=1, padx=8, pady=8)

        ctk.CTkLabel(mapping_frame, text="Axe Y (Amplitude) :").grid(row=0, column=2, padx=8, pady=8, sticky="w")
        self.combo_y_col = ctk.CTkOptionMenu(mapping_frame, values=["---"])
        self.combo_y_col.grid(row=0, column=3, padx=8, pady=8)

        self.preview_box = ctk.CTkTextbox(self, height=160)
        self.preview_box.pack(fill="both", expand=True, padx=12, pady=8)
        self.preview_box.insert("1.0", "Sélectionnez un fichier CSV pour voir l'aperçu...")
        self.preview_box.configure(state="disabled")

        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=12, pady=8)

        btn_cancel = ctk.CTkButton(btn_frame, text="Annuler", fg_color="gray30", command=self.destroy)
        btn_cancel.pack(side="right", padx=4)

        btn_confirm = ctk.CTkButton(btn_frame, text="Importer le Signal", fg_color="#2b5b84", command=self._confirm_import)
        btn_confirm.pack(side="right", padx=4)

    def _get_sep_char(self):
        val = self.combo_sep.get()
        if ";" in val: return ";"
        if "," in val: return ","
        if "Tabulation" in val: return "\t"
        return " "

    def _get_dec_char(self):
        return "." if "." in self.combo_dec.get() else ","

    def _browse_file(self):
        path = filedialog.askopenfilename(
            title="Sélectionner un fichier CSV",
            filetypes=[("Fichiers CSV", "*.csv"), ("Fichiers texte", "*.txt"), ("Tous les fichiers", "*.*")]
        )
        if path:
            if isinstance(path, (tuple, list)): path = path[0]
            self.file_path = path
            self.lbl_file_path.configure(text=os.path.basename(path))
            self._update_preview()

    def _update_preview(self, choice=None):
        if not self.file_path: return
        sep = self._get_sep_char()
        dec = self._get_dec_char()

        success, df_or_err, cols = CSVImporter.preview_csv(self.file_path, sep=sep, decimal=dec, nrows=8)
        self.preview_box.configure(state="normal")
        self.preview_box.delete("1.0", "end")

        if success:
            self.columns = cols
            self.combo_x_col.configure(values=cols)
            self.combo_y_col.configure(values=cols)
            if len(cols) >= 1: self.combo_x_col.set(cols[0])
            if len(cols) >= 2: self.combo_y_col.set(cols[1])
            elif len(cols) == 1: self.combo_y_col.set(cols[0])

            self.preview_box.insert("1.0", f"--- APERÇU DE DONNÉES ({len(cols)} colonnes) ---\n\n")
            self.preview_box.insert("end", df_or_err.to_string())
        else:
            self.preview_box.insert("1.0", f"Erreur de lecture :\n{df_or_err}")

        self.preview_box.configure(state="disabled")

    def _confirm_import(self):
        if not self.file_path:
            messagebox.showwarning("Attention", "Veuillez choisir un fichier.")
            return

        x_col = self.combo_x_col.get()
        y_col = self.combo_y_col.get()
        if x_col == "---" or y_col == "---":
            messagebox.showwarning("Attention", "Veuillez sélectionner les colonnes X et Y.")
            return

        sep = self._get_sep_char()
        dec = self._get_dec_char()

        success, msg, df_clean = CSVImporter.load_csv(self.file_path, x_col, y_col, sep=sep, decimal=dec)
        if success:
            if self.on_import_callback:
                self.on_import_callback(df_clean, x_col, y_col, self.file_path)
            self.destroy()
        else:
            messagebox.showerror("Erreur d'importation", msg)
