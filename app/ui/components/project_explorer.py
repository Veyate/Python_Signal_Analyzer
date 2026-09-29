"""
Explorateur de projet (Treeview) avec menu contextuel et mise à jour dynamique des noms.
"""
import customtkinter as ctk
from tkinter import ttk, Menu
from app.utils.i18n import _

class ProjectExplorerFrame(ctk.CTkFrame):
    def __init__(self, parent, on_select_item=None, on_delete_item=None, **kwargs):
        super().__init__(parent, **kwargs)
        self.on_select_item = on_select_item
        self.on_delete_item = on_delete_item

        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        label = ctk.CTkLabel(self, text=_("project_title"), font=ctk.CTkFont(size=13, weight="bold"))
        label.grid(row=0, column=0, padx=8, pady=4, sticky="w")

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview", background="#2b2b2b", foreground="#ffffff", fieldbackground="#2b2b2b", rowheight=24)
        style.map("Treeview", background=[('selected', '#1f538d')])

        self.tree = ttk.Treeview(self, show="tree")
        self.tree.grid(row=1, column=0, sticky="nsew", padx=3, pady=3)

        self.root_node = self.tree.insert("", "end", text=_("tree_projects"), open=True)
        self.signals_cat_node = None
        self.displays_cat_node = None
        self.analyses_cat_node = None

        self.node_mapping = {}

        self.tree.bind("<<TreeviewSelect>>", self._on_select)
        self.tree.bind("<Button-3>", self._on_right_click)
        self.tree.bind("<Button-2>", self._on_right_click)

        self.context_menu = Menu(self, tearoff=0, bg="#2b2b2b", fg="#ffffff", activebackground="#1f538d")
        self.context_menu.add_command(label=_("ctx_delete"), command=self._delete_selected)

    def clear_tree(self):
        for child in self.tree.get_children(""):
            self.tree.delete(child)
        self.root_node = self.tree.insert("", "end", text=_("tree_projects"), open=True)
        self.signals_cat_node = None
        self.displays_cat_node = None
        self.analyses_cat_node = None
        self.node_mapping.clear()

    def add_imported_signal(self, signal_id, file_name):
        if self.signals_cat_node is None:
            self.signals_cat_node = self.tree.insert(self.root_node, "end", text=_("tree_imported_signals"), open=True)

        item_node = self.tree.insert(self.signals_cat_node, "end", text=f" 📄 {file_name}", open=True)
        self.node_mapping[item_node] = {"id": signal_id, "text": file_name, "type": "signal"}
        self.tree.selection_set(item_node)

    def add_display_item(self, display_id, display_name):
        if self.displays_cat_node is None:
            self.displays_cat_node = self.tree.insert(self.root_node, "end", text=_("tree_displays"), open=True)

        item_node = self.tree.insert(self.displays_cat_node, "end", text=f" 📊 {display_name}", open=True)
        self.node_mapping[item_node] = {"id": display_id, "text": display_name, "type": "display"}
        self.tree.selection_set(item_node)

    def add_fft_item(self, fft_id, fft_name):
        if self.analyses_cat_node is None:
            self.analyses_cat_node = self.tree.insert(self.root_node, "end", text=_("tree_analyses"), open=True)

        item_node = self.tree.insert(self.analyses_cat_node, "end", text=f" ⚡ {fft_name}", open=True)
        self.node_mapping[item_node] = {"id": fft_id, "text": fft_name, "type": "fft"}
        self.tree.selection_set(item_node)

    def update_item_name(self, item_id, new_name):
        for node, meta in self.node_mapping.items():
            if meta["id"] == item_id:
                meta["text"] = new_name
                if meta["type"] == "signal":
                    self.tree.item(node, text=f" 📄 {new_name}")
                elif meta["type"] == "display":
                    self.tree.item(node, text=f" 📊 {new_name}")
                elif meta["type"] == "fft":
                    self.tree.item(node, text=f" ⚡ {new_name}")
                break

    def _on_select(self, event):
        selected = self.tree.selection()
        if selected and self.on_select_item:
            node = selected[0]
            if node in self.node_mapping:
                meta = self.node_mapping[node]
                self.on_select_item(meta["id"], meta["text"], meta["type"])

    def _on_right_click(self, event):
        item = self.tree.identify_row(event.y)
        if item and item in self.node_mapping:
            self.tree.selection_set(item)
            self.context_menu.post(event.x_root, event.y_root)

    def _delete_selected(self):
        selected = self.tree.selection()
        if selected:
            node = selected[0]
            if node in self.node_mapping:
                meta = self.node_mapping.pop(node)
                self.tree.delete(node)
                if self.on_delete_item:
                    self.on_delete_item(meta["id"], meta["type"])
