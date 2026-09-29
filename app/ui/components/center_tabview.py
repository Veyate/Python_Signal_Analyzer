"""
Panneau central à onglets (Données, Graphiques et FFT avec mode Aperçu/Épinglé et renommage).
"""
import customtkinter as ctk
from app.ui.components.plot_canvas import PlotCanvasFrame
from app.ui.components.data_table_frame import DataTableFrame
from app.utils.i18n import _

class CenterTabView(ctk.CTkTabview):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.tab_widgets = {}     # key (id or title) -> widget
        self.pinned_tabs = set()  # set des titres d'onglets épinglés
        self.preview_tab_title = None

    def is_tab_pinned(self, tab_title):
        return tab_title in self.pinned_tabs

    def toggle_pin_tab(self, tab_title, is_pinned):
        if is_pinned:
            self.pinned_tabs.add(tab_title)
            if self.preview_tab_title == tab_title:
                self.preview_tab_title = None
        else:
            self.pinned_tabs.discard(tab_title)

    def close_all_tabs(self):
        titles = list(self._tab_dict.keys())
        for t in titles:
            self.delete(t)
        self.tab_widgets.clear()
        self.pinned_tabs.clear()
        self.preview_tab_title = None

    def rename_tab(self, old_title, new_title, data_df=None, display_id=None, fft_id=None):
        if old_title == new_title:
            return

        if old_title in self._tab_dict:
            was_pinned = old_title in self.pinned_tabs
            was_preview = (self.preview_tab_title == old_title)

            self.delete(old_title)
            self.tab_widgets.pop(old_title, None)

            if was_pinned:
                self.pinned_tabs.discard(old_title)
                self.pinned_tabs.add(new_title)

            if data_df is not None:
                self.add(new_title)
                table_widget = DataTableFrame(self.tab(new_title))
                table_widget.pack(fill="both", expand=True)
                table_widget.load_dataframe(data_df)
                self.tab_widgets[new_title] = table_widget
                self.set(new_title)
            elif display_id is not None or fft_id is not None:
                item_id = display_id if display_id is not None else fft_id
                self.add(new_title)
                plot_widget = PlotCanvasFrame(self.tab(new_title))
                plot_widget.pack(fill="both", expand=True)
                self.tab_widgets[item_id] = plot_widget
                self.tab_widgets[new_title] = plot_widget
                self.set(new_title)

            if was_preview:
                self.preview_tab_title = new_title

    def open_or_select_data_tab(self, signal_id, signal_name, df):
        tab_title = _("tab_data_prefix", signal_name)

        if tab_title in self._tab_dict:
            if tab_title in self.tab_widgets:
                self.tab_widgets[tab_title].load_dataframe(df)
            self.set(tab_title)
            return

        if self.preview_tab_title and self.preview_tab_title in self._tab_dict and self.preview_tab_title not in self.pinned_tabs:
            self.delete(self.preview_tab_title)
            self.tab_widgets.pop(self.preview_tab_title, None)

        self.add(tab_title)
        table_widget = DataTableFrame(self.tab(tab_title))
        table_widget.pack(fill="both", expand=True)
        table_widget.load_dataframe(df)

        self.tab_widgets[tab_title] = table_widget
        self.preview_tab_title = tab_title
        self.set(tab_title)

    def open_or_select_plot_tab(self, display_id, display_name):
        tab_title = _("tab_plot_prefix", display_name)

        if tab_title in self._tab_dict:
            self.set(tab_title)
            return self.tab_widgets.get(display_id)

        if self.preview_tab_title and self.preview_tab_title in self._tab_dict and self.preview_tab_title not in self.pinned_tabs:
            self.delete(self.preview_tab_title)
            old_id = [k for k, v in self.tab_widgets.items() if v == self.tab_widgets.get(self.preview_tab_title)]
            if old_id: self.tab_widgets.pop(old_id[0], None)

        self.add(tab_title)
        plot_widget = PlotCanvasFrame(self.tab(tab_title))
        plot_widget.pack(fill="both", expand=True)

        self.tab_widgets[display_id] = plot_widget
        self.tab_widgets[tab_title] = plot_widget
        self.preview_tab_title = tab_title
        self.set(tab_title)
        return plot_widget

    def open_or_select_fft_tab(self, fft_id, fft_name):
        tab_title = _("tab_fft_prefix", fft_name)

        if tab_title in self._tab_dict:
            self.set(tab_title)
            return self.tab_widgets.get(fft_id)

        if self.preview_tab_title and self.preview_tab_title in self._tab_dict and self.preview_tab_title not in self.pinned_tabs:
            self.delete(self.preview_tab_title)
            old_id = [k for k, v in self.tab_widgets.items() if v == self.tab_widgets.get(self.preview_tab_title)]
            if old_id: self.tab_widgets.pop(old_id[0], None)

        self.add(tab_title)
        plot_widget = PlotCanvasFrame(self.tab(tab_title))
        plot_widget.pack(fill="both", expand=True)

        self.tab_widgets[fft_id] = plot_widget
        self.tab_widgets[tab_title] = plot_widget
        self.preview_tab_title = tab_title
        self.set(tab_title)
        return plot_widget

    def get_plot_widget(self, item_id):
        return self.tab_widgets.get(item_id)

    def close_tab_by_title(self, tab_title):
        if tab_title in self._tab_dict:
            self.delete(tab_title)
            self.pinned_tabs.discard(tab_title)
            if self.preview_tab_title == tab_title:
                self.preview_tab_title = None
