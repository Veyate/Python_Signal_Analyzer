"""
Canvas graphique Matplotlib avec superposition de signaux multiples, curseurs de mesure et détection de pics.
"""
import customtkinter as ctk
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from app.utils.i18n import _

class PlotCanvasFrame(ctk.CTkFrame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=0)
        self.grid_columnconfigure(0, weight=1)

        self.fig, self.ax = plt.subplots(figsize=(6, 4), dpi=100)
        self.fig.patch.set_facecolor("#2b2b2b")
        self._style_axis()

        self.canvas = FigureCanvasTkAgg(self.fig, master=self)
        self.canvas.get_tk_widget().configure(width=1, height=1)
        self.canvas.get_tk_widget().grid(row=0, column=0, sticky="nsew")

        self.toolbar_frame = ctk.CTkFrame(self, height=35)
        self.toolbar_frame.grid(row=1, column=0, sticky="ew")

        self.toolbar = NavigationToolbar2Tk(self.canvas, self.toolbar_frame)
        self.toolbar.update()

        self.ax.text(0.5, 0.5, _("plot_select_signals_hint"),
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
                           linewidth=1.2, linestyle="-", x_min=None, x_max=None, y_min=None, y_max=None,
                           cursors_enabled=False, cursor1_x=None, cursor1_target_id=None,
                           cursor2_x=None, cursor2_target_id=None, ref_freq=50.0, show_cursor_overlay=True,
                           peaks=None):
        self.ax.clear()
        self._style_axis()

        has_data = False
        if signals_to_plot:
            for s in signals_to_plot:
                if len(s.get("x_data", [])) > 0:
                    has_data = True
                    break

        if not has_data:
            self.ax.text(0.5, 0.5, _("plot_no_signal_selected"), color="gray", ha="center", va="center", transform=self.ax.transAxes)
            self.ax.set_xlabel(x_label)
            self.ax.set_ylabel(y_label)
            self.ax.set_title(title)
            self.ax.grid(True, color="#333333", linestyle="--", alpha=0.7)
            self.canvas.draw()
            return

        default_colors = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd", "#17becf", "#bcbd22"]

        for i, sig in enumerate(signals_to_plot):
            color = sig.get("color") or default_colors[i % len(default_colors)]
            x_data = sig["x_data"]
            y_data = sig["y_data"]
            name = sig["name"]
            self.ax.plot(x_data, y_data, color=color, linewidth=linewidth, linestyle=linestyle, label=name)

        # Custom Axis Limits (Zoom)
        if x_min is not None or x_max is not None:
            self.ax.set_xlim(left=x_min, right=x_max)
        if y_min is not None or y_max is not None:
            self.ax.set_ylim(bottom=y_min, top=y_max)

        # Peak Markers Rendering (Peak Search)
        if peaks:
            for p in peaks:
                f_k = p["freq"]
                a_k = p["amplitude"]
                rank = p["rank"]
                self.ax.plot(f_k, a_k, 'v', color="#ffb703", markeredgecolor="black", markersize=7, zorder=6)
                self.ax.annotate(f"P{rank}", xy=(f_k, a_k), xytext=(0, 5), textcoords="offset points",
                                 ha='center', va='bottom', fontsize=8, fontweight='bold', color="#ffb703")

        # Cursors Rendering
        if cursors_enabled and signals_to_plot:
            sig1 = None
            if cursor1_target_id:
                for s in signals_to_plot:
                    if s.get("id") == cursor1_target_id:
                        sig1 = s
                        break
            if sig1 is None:
                sig1 = signals_to_plot[0]

            sig2 = None
            if cursor2_target_id:
                for s in signals_to_plot:
                    if s.get("id") == cursor2_target_id:
                        sig2 = s
                        break
            if sig2 is None:
                sig2 = signals_to_plot[0]

            y1, y2 = None, None
            c1_name = sig1["name"]
            c2_name = sig2["name"]

            if cursor1_x is not None and len(sig1["x_data"]) > 0:
                tx1 = sig1["x_data"]
                ty1 = sig1["y_data"]
                idx1 = np.argsort(tx1)
                y1 = float(np.interp(cursor1_x, tx1[idx1], ty1[idx1]))
                self.ax.axvline(x=cursor1_x, color="#ff4d4d", linestyle="--", linewidth=1.5, alpha=0.85)
                self.ax.plot(cursor1_x, y1, 'o', color="#ff4d4d", markeredgecolor="white", markeredgewidth=1.2, markersize=7, zorder=5)

            if cursor2_x is not None and len(sig2["x_data"]) > 0:
                tx2 = sig2["x_data"]
                ty2 = sig2["y_data"]
                idx2 = np.argsort(tx2)
                y2 = float(np.interp(cursor2_x, tx2[idx2], ty2[idx2]))
                self.ax.axvline(x=cursor2_x, color="#00e676", linestyle="--", linewidth=1.5, alpha=0.85)
                self.ax.plot(cursor2_x, y2, 'o', color="#00e676", markeredgecolor="white", markeredgewidth=1.2, markersize=7, zorder=5)

            if show_cursor_overlay and cursor1_x is not None and cursor2_x is not None and y1 is not None and y2 is not None:
                dx = cursor2_x - cursor1_x
                dy = y2 - y1
                freq = 1.0 / abs(dx) if abs(dx) > 1e-12 else 0.0

                f0 = ref_freq if (ref_freq and ref_freq > 0) else 50.0
                d_phi_deg = (360.0 * f0 * dx)
                d_phi_rad = (2.0 * np.pi * f0 * dx)

                c_header = _("plot_cursor_title")
                info_txt = (
                    f"{c_header}\n"
                    f"🔴 C1 [{c1_name}]: ({cursor1_x:.4g}, {y1:.4g})\n"
                    f"🟢 C2 [{c2_name}]: ({cursor2_x:.4g}, {y2:.4g})\n"
                    f"─────────────────────────────\n"
                    f"ΔX : {dx:.4g}  |  1/|ΔX|: {freq:.4g}\n"
                    f"ΔY : {dy:.4g}\n"
                    f"ΔΦ : {d_phi_deg:.1f}° ({d_phi_rad:.3f} rad @ {f0:.1f}Hz)"
                )
                self.ax.text(0.02, 0.95, info_txt, transform=self.ax.transAxes,
                             verticalalignment='top', fontfamily='monospace', fontsize=8.5, color="white",
                             bbox=dict(boxstyle="round,pad=0.5", fc="#151515", ec="#00f5d4", lw=1.2, alpha=0.88))

        self.ax.set_xlabel(x_label)
        self.ax.set_ylabel(y_label)
        self.ax.set_title(title)
        self.ax.grid(True, color="#333333", linestyle="--", alpha=0.7)
        self.ax.legend(facecolor="#2b2b2b", edgecolor="gray", labelcolor="white")
        self.canvas.draw()
