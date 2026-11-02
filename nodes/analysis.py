# nodes/analysis.py
from PySide6.QtCore import Qt, QRectF
from PySide6.QtGui import QColor, QBrush, QPen, QPainter
from PySide6.QtWidgets import QGraphicsItem
from engine import FFTAnalysisEngine, THDAnalysisEngine


class FFTAnalysisNode(QGraphicsItem):
    """Nœud 'Analyse FFT' (Catégorie Analyses)."""
    def __init__(self, name="Analyse FFT 1", x=0, y=0):
        super().__init__()
        self.node_type = "fft_analysis"
        self.width = 175
        self.height = 95
        self.setPos(x, y)
        self.setFlags(
            QGraphicsItem.ItemIsMovable |
            QGraphicsItem.ItemIsSelectable |
            QGraphicsItem.ItemSendsGeometryChanges
        )
        self.connections = []

        self.input_node = None  # Nœud source ou filtre connecté en entrée

        self.params = {
            "name": name,
            "window_type": "Rectangulaire",
            "n_fft": "1024",
            "unit": "Amplitude (V)"
        }
        
        self.is_dirty = True
        self.is_fft = True
        self.t_data = None  # Fréquences (Hz)
        self.y_data = None  # Spectre (V ou dB)

    def mark_dirty(self):
        self.is_dirty = True
        self.update()

    def recalculate(self):
        """Exécute la FFT sur le signal du nœud d'entrée."""
        if self.input_node and self.input_node.t_data is not None and self.input_node.y_data is not None:
            self.t_data, self.y_data = FFTAnalysisEngine.compute_fft(
                t=self.input_node.t_data,
                y=self.input_node.y_data,
                window_type=self.params.get("window_type", "Hann"),
                n_fft_str=str(self.params.get("n_fft", "1024")),
                unit=self.params.get("unit", "Amplitude (V)")
            )
        else:
            self.t_data = None
            self.y_data = None

        self.is_dirty = False
        self.update()

    def boundingRect(self):
        margin = 12
        return QRectF(-margin, -margin, self.width + 2 * margin, self.height + 2 * margin)

    def paint(self, painter, option, widget=None):
        painter.setRenderHint(QPainter.Antialiasing, True)
        border_color = QColor("#FF9800") if self.is_dirty else QColor("#E91E63")
        if self.isSelected():
            border_color = QColor("#FFFFFF")

        # Corps
        painter.setBrush(QBrush(QColor("#2B2E3A")))
        painter.setPen(QPen(border_color, 2 if self.isSelected() or self.is_dirty else 1))
        painter.drawRoundedRect(0, 0, self.width, self.height, 8, 8)

        # En-tête (Rose / Magenta)
        header_color = QColor("#E65100") if self.is_dirty else QColor("#E91E63")
        painter.setBrush(QBrush(header_color))
        painter.drawRoundedRect(0, 0, self.width, 24, 8, 8)
        painter.fillRect(0, 14, self.width, 10, header_color)
        
        painter.setPen(QPen(Qt.white))
        status_badge = "⚠️" if self.is_dirty else "✓"
        painter.drawText(QRectF(8, 3, self.width - 16, 18), Qt.AlignLeft | Qt.AlignVCenter, f"{status_badge} Analyse FFT")

        # Nom
        painter.setPen(QPen(QColor("#EEEEEE")))
        painter.drawText(QRectF(10, 32, self.width - 20, 20), Qt.AlignLeft, self.params["name"])

        # Paramètres
        src_info = self.input_node.params['name'] if self.input_node else "Aucune"
        painter.setPen(QPen(QColor("#B0BEC5")))
        painter.drawText(QRectF(10, 54, self.width - 20, 18), Qt.AlignLeft, f"Win: {self.params['window_type']} ({self.params['n_fft']} pts)")
        painter.drawText(QRectF(10, 72, self.width - 20, 18), Qt.AlignLeft, f"In: {src_info}")

        # Input socket (gauche - Cyan)
        painter.setBrush(QBrush(QColor("#00ADB5")))
        painter.setPen(QPen(QColor("#FFFFFF"), 1.5))
        painter.drawEllipse(-6, self.height // 2 - 6, 12, 12)

        # Output socket (droit - Orange)
        painter.setBrush(QBrush(QColor("#FF5722")))
        painter.setPen(QPen(QColor("#FFFFFF"), 1.5))
        painter.drawEllipse(self.width - 6, self.height // 2 - 6, 12, 12)

    def itemChange(self, change, value):
        if change in (QGraphicsItem.ItemPositionHasChanged, QGraphicsItem.ItemPositionChange):
            for conn in self.connections:
                conn.update_path()
        return super().itemChange(change, value)


class THDAnalysisNode(QGraphicsItem):
    """Nœud 'Analyse THD & Harmoniques' (Catégorie Analyses - Violet #9C27B0)."""
    def __init__(self, name="Analyse THD 1", x=0, y=0):
        super().__init__()
        self.node_type = "thd_analysis"
        self.width = 185
        self.height = 95
        self.setPos(x, y)
        self.setFlags(
            QGraphicsItem.ItemIsMovable |
            QGraphicsItem.ItemIsSelectable |
            QGraphicsItem.ItemSendsGeometryChanges
        )
        self.connections = []
        self.input_node = None

        self.params = {
            "name": name,
            "fundamental_mode": "Saisie Manuelle",
            "fundamental_freq": 50.0,
            "max_harmonics": 10,
            "display_unit": "% de la Fondamentale",
            "window_type": "Rectangulaire"
        }
        
        self.is_dirty = True
        self.is_thd = True
        self.harm_orders = None
        self.harm_freqs = None
        self.y_data = None  # Display amplitudes
        self.harm_v_raw = None  # Raw amplitudes in V
        self.thd_percent = 0.0
        self.f0_detected = 50.0
        self.v1_amp = 0.0
        self.t_data = None

    def mark_dirty(self):
        self.is_dirty = True
        self.update()

    def recalculate(self):
        """Calcule le THD et le spectre harmonique du signal d'entrée."""
        if self.input_node and self.input_node.t_data is not None and self.input_node.y_data is not None:
            from engine import THDAnalysisEngine
            res = THDAnalysisEngine.compute_thd(
                t=self.input_node.t_data,
                y=self.input_node.y_data,
                fundamental_mode=str(self.params.get("fundamental_mode", "Saisie Manuelle")),
                fundamental_freq=float(self.params.get("fundamental_freq", 50.0)),
                max_harmonics=int(self.params.get("max_harmonics", 10)),
                display_unit=str(self.params.get("display_unit", "% de la Fondamentale")),
                window_type=str(self.params.get("window_type", "Rectangulaire"))
            )
            self.harm_orders, self.harm_freqs, self.y_data, self.thd_percent, self.f0_detected, self.v1_amp, self.harm_v_raw = res
            self.t_data = self.harm_orders
        else:
            self.harm_orders = None
            self.harm_freqs = None
            self.y_data = None
            self.harm_v_raw = None
            self.thd_percent = 0.0
            self.f0_detected = 50.0
            self.v1_amp = 0.0
            self.t_data = None

        self.is_dirty = False
        self.update()

    def boundingRect(self):
        margin = 12
        return QRectF(-margin, -margin, self.width + 2 * margin, self.height + 2 * margin)

    def paint(self, painter, option, widget=None):
        painter.setRenderHint(QPainter.Antialiasing, True)
        border_color = QColor("#FF9800") if self.is_dirty else QColor("#9C27B0")
        if self.isSelected():
            border_color = QColor("#FFFFFF")

        painter.setBrush(QBrush(QColor("#2B2E3A")))
        painter.setPen(QPen(border_color, 2 if self.isSelected() or self.is_dirty else 1))
        painter.drawRoundedRect(0, 0, self.width, self.height, 8, 8)

        header_color = QColor("#E65100") if self.is_dirty else QColor("#9C27B0")
        painter.setBrush(QBrush(header_color))
        painter.drawRoundedRect(0, 0, self.width, 24, 8, 8)
        painter.fillRect(0, 14, self.width, 10, header_color)
        
        painter.setPen(QPen(Qt.white))
        status_badge = "⚠️" if self.is_dirty else "📊"
        painter.drawText(QRectF(8, 3, self.width - 16, 18), Qt.AlignLeft | Qt.AlignVCenter, f"{status_badge} Analyse THD")

        painter.setPen(QPen(QColor("#EEEEEE")))
        painter.drawText(QRectF(10, 32, self.width - 20, 20), Qt.AlignLeft, self.params["name"])

        src_info = self.input_node.params['name'] if self.input_node else "Aucune"
        painter.setPen(QPen(QColor("#B0BEC5")))
        thd_str = f"THD: {self.thd_percent:.2f}%" if not self.is_dirty else "THD: -"
        max_h = self.params.get('max_harmonics', 10)
        painter.drawText(QRectF(10, 54, self.width - 20, 18), Qt.AlignLeft, f"{thd_str} ({max_h} harm.)")
        painter.drawText(QRectF(10, 72, self.width - 20, 18), Qt.AlignLeft, f"In: {src_info}")

        painter.setBrush(QBrush(QColor("#00ADB5")))
        painter.setPen(QPen(QColor("#FFFFFF"), 1.5))
        painter.drawEllipse(-6, self.height // 2 - 6, 12, 12)

        painter.setBrush(QBrush(QColor("#FF5722")))
        painter.setPen(QPen(QColor("#FFFFFF"), 1.5))
        painter.drawEllipse(self.width - 6, self.height // 2 - 6, 12, 12)

    def itemChange(self, change, value):
        if change in (QGraphicsItem.ItemPositionHasChanged, QGraphicsItem.ItemPositionChange):
            for conn in self.connections:
                conn.update_path()
        return super().itemChange(change, value)
