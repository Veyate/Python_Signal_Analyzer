"""
Tableau de données (Données brutes).
"""
import customtkinter as ctk
from tkinter import ttk

class DataTableFrame(ctk.CTkFrame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview", background="#2b2b2b", foreground="#ffffff", fieldbackground="#2b2b2b", rowheight=24)
        style.configure("Treeview.Heading", background="#1f1f1f", foreground="#ffffff", relief="flat")
        style.map("Treeview", background=[('selected', '#1f538d')])

        self.tree_frame = ctk.CTkFrame(self)
        self.tree_frame.grid(row=0, column=0, sticky="nsew", padx=3, pady=3)
        self.tree_frame.grid_rowconfigure(0, weight=1)
        self.tree_frame.grid_columnconfigure(0, weight=1)

        self.tree = ttk.Treeview(self.tree_frame, show="headings")
        self.vsb = ttk.Scrollbar(self.tree_frame, orient="vertical", command=self.tree.yview)
        self.hsb = ttk.Scrollbar(self.tree_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=self.vsb.set, xscrollcommand=self.hsb.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        self.vsb.grid(row=0, column=1, sticky="ns")
        self.hsb.grid(row=1, column=0, sticky="ew")

    def load_dataframe(self, df, max_rows=2000):
        self.tree.delete(*self.tree.get_children())
        if df is None or not hasattr(df, "columns"): return

        cols = list(df.columns)
        self.tree["columns"] = cols
        for col in cols:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=110, anchor="center")

        df_preview = df.head(max_rows)
        for _, row in df_preview.iterrows():
            vals = [f"{val:.6g}" if isinstance(val, (float, int)) else str(val) for val in row]
            self.tree.insert("", "end", values=vals)
