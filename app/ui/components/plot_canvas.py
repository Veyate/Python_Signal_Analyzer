"""
Canvas graphique Matplotlib avec superposition de signaux multiples.
"""
import customtkinter as ctk
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk

class PlotCanvasFrame(ctk.CTkFrame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=0)
        self.grid_columnconfigure(0, weight=1)

        self.fig, self.ax = plt.subplots(figsize=(3, 2), dpi=100)
        self.fig.patch.set_facecolor("#2b2b2b")
        self._style_axis()

        self.canvas = FigureCanvasTkAgg(self.fig, master=self)
        canvas_widget = self.canvas.get_tk_widget()
        canvas_widget.configure(width=1, height=1)
        canvas_widget.grid(row=0, column=0, sticky="nsew")

        self.toolbar_frame = ctk.CTkFrame(self, height=32)
        self.toolbar_frame.grid(row=1, column=0, sticky="ew")

        self.toolbar = NavigationToolbar2Tk(self.canvas, self.toolbar_frame)
        self.toolbar.update()

        self.ax.text(0.5, 0.5, "Cochez des signaux dans le panneau de droite",
                    color="gray", ha="center", va="center", transform=self.ax.transAxes)
        self.canvas.draw()

    def _style_axis(self):
        self.ax.set_facecolor("#1f1f1f")
        self.ax.tick_params(colors="white")
        self.ax.xaxis.label.set_color("white")
        self.ax.yaxis.label.set_color("white")
        self.ax.title.set_color("white")
        for spine in self.ax.spines.values():
            spine.set_color("gray")

    def plot_multi_signals(self, signals_to_plot, title="Graphique", x_label="Temps", y_label="Amplitude",
                           linewidth=1.2, linestyle="-", x_min=None, x_max=None, y_min=None, y_max=None):
        self.ax.clear()
        self._style_axis()

        if not signals_to_plot:
            self.ax.text(0.5, 0.5, "Aucun signal sélectionné", color="gray", ha="center", va="center", transform=self.ax.transAxes)
            self.canvas.draw()
            return

        default_colors = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd", "#17becf", "#bcbd22"]

        for i, sig in enumerate(signals_to_plot):
            color = sig.get("color") or default_colors[i % len(default_colors)]
            x_data = sig["x_data"]
            y_data = sig["y_data"]
            name = sig["name"]
            self.ax.plot(x_data, y_data, color=color, linewidth=linewidth, linestyle=linestyle, label=name)

        self.ax.set_xlabel(x_label)
        self.ax.set_ylabel(y_label)
        self.ax.set_title(title)
        self.ax.grid(True, color="#333333", linestyle="--", alpha=0.7)

        # Apply custom axis limits if set (Zoom permanent)
        if x_min is not None or x_max is not None:
            self.ax.set_xlim(left=x_min, right=x_max)
        if y_min is not None or y_max is not None:
            self.ax.set_ylim(bottom=y_min, top=y_max)

        self.ax.legend(facecolor="#2b2b2b", edgecolor="gray", labelcolor="white")
        self.canvas.draw()
