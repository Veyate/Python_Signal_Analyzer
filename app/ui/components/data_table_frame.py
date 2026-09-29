import customtkinter as ctk
from tkinter import ttk

class DataTableFrame(ctk.CTkFrame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview", background="#2b2b2b", foreground="#ffffff", fieldbackground="#2b2b2b", rowheight=22)
        style.map("Treeview", background=[('selected', '#1f538d')])

        self.tree = ttk.Treeview(self, show="headings")
        self.tree.grid(row=0, column=0, sticky="nsew", padx=3, pady=3)

        vsb = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        vsb.grid(row=0, column=1, sticky="ns")
        self.tree.configure(yscrollcommand=vsb.set)

    def load_dataframe(self, df):
        for child in self.tree.get_children(""):
            self.tree.delete(child)

        cols = list(df.columns)
        self.tree["columns"] = cols

        for col in cols:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=120, anchor="center")

        max_rows = min(500, len(df))
        for i in range(max_rows):
            row_vals = [str(val) for val in df.iloc[i].values]
            self.tree.insert("", "end", values=row_vals)
