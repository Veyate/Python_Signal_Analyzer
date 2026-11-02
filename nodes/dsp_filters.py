# nodes/dsp_filters.py
from PySide6.QtCore import Qt, QRectF
from PySide6.QtGui import QColor, QBrush, QPen, QPainter
from PySide6.QtWidgets import QGraphicsItem
from engine import DSPFilterEngine


class FixedAverageNode(QGraphicsItem):
    """Nœud 'Moyenne Fixe (Bloc)' (Catégorie Filtres Numériques DSP - Vert Canard #00897B)."""
    def __init__(self, name="Moyenne Fixe 1", x=0, y=0):
        super().__init__()
        self.node_type = "fixed_average"
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
            "sample_size": 16,                             # N = 2^n
            "rate_mode": "Fréquence (Hz)",                 # Mode de saisie
            "sampling_rate": 1000.0,                      # fs (Hz)
            "time_offset": 0.0,                           # Décalage asynchrone (s / ms)
            "window_type": "Rectangulaire (Uniforme)",     # Fenêtrage
            "output_mode": "Signal Décimé (1 point/bloc)"  # Décimé ou Continu ZOH
        }
        self.is_dirty = True
        self.t_data = None
        self.y_data = None

    def mark_dirty(self):
        self.is_dirty = True
        self.update()

    def recalculate(self):
        if self.input_node and self.input_node.t_data is not None and self.input_node.y_data is not None:
            self.t_data, self.y_data = DSPFilterEngine.fixed_average(
                self.input_node.t_data,
                self.input_node.y_data,
                sample_size=int(self.params.get("sample_size", 16)),
                sampling_rate=float(self.params.get("sampling_rate", 1000.0)),
                time_offset=float(self.params.get("time_offset", 0.0)),
                window_type=self.params.get("window_type", "Rectangulaire (Uniforme)"),
                output_mode=self.params.get("output_mode", "Signal Décimé (1 point/bloc)")
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
        border_color = QColor("#FF9800") if self.is_dirty else QColor("#00897B")
        if self.isSelected():
            border_color = QColor("#FFFFFF")

        painter.setBrush(QBrush(QColor("#2B2E3A")))
        painter.setPen(QPen(border_color, 2 if self.isSelected() or self.is_dirty else 1))
        painter.drawRoundedRect(0, 0, self.width, self.height, 8, 8)

        header_color = QColor("#E65100") if self.is_dirty else QColor("#00897B")
        painter.setBrush(QBrush(header_color))
        painter.drawRoundedRect(0, 0, self.width, 24, 8, 8)
        painter.fillRect(0, 14, self.width, 10, header_color)
        
        painter.setPen(QPen(Qt.white))
        status_badge = "⚠️" if self.is_dirty else "✓"
        painter.drawText(QRectF(8, 3, self.width - 16, 18), Qt.AlignLeft | Qt.AlignVCenter, f"{status_badge} Moyenne Fixe (Bloc)")

        painter.setPen(QPen(QColor("#EEEEEE")))
        painter.drawText(QRectF(10, 32, self.width - 20, 20), Qt.AlignLeft, self.params["name"])

        src_info = self.input_node.params['name'] if self.input_node else "Aucune"
        painter.setPen(QPen(QColor("#B0BEC5")))
        n_val = self.params.get('sample_size', 16)
        painter.drawText(QRectF(10, 54, self.width - 20, 18), Qt.AlignLeft, f"Taille: N={n_val} samples")
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


class MovingAverageNode(QGraphicsItem):
    """Nœud 'Moyenne Glissante (FIR)' (Catégorie Filtres Numériques DSP - Vert Canard #00796B)."""
    def __init__(self, name="Moyenne Glissante 1", x=0, y=0):
        super().__init__()
        self.node_type = "moving_average"
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
            "sample_size": 16,                             # N = 2^n
            "rate_mode": "Fréquence (Hz)",                 # Mode de saisie
            "sampling_rate": 1000.0,                      # fs (Hz)
            "time_offset": 0.0,                           # Décalage asynchrone (s / ms)
            "window_type": "Rectangulaire (Uniforme)"      # Fenêtrage
        }
        self.is_dirty = True
        self.t_data = None
        self.y_data = None

    def mark_dirty(self):
        self.is_dirty = True
        self.update()

    def recalculate(self):
        if self.input_node and self.input_node.t_data is not None and self.input_node.y_data is not None:
            self.t_data, self.y_data = DSPFilterEngine.moving_average(
                self.input_node.t_data,
                self.input_node.y_data,
                sample_size=int(self.params.get("sample_size", 16)),
                sampling_rate=float(self.params.get("sampling_rate", 1000.0)),
                time_offset=float(self.params.get("time_offset", 0.0)),
                window_type=self.params.get("window_type", "Rectangulaire (Uniforme)")
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
        border_color = QColor("#FF9800") if self.is_dirty else QColor("#00796B")
        if self.isSelected():
            border_color = QColor("#FFFFFF")

        painter.setBrush(QBrush(QColor("#2B2E3A")))
        painter.setPen(QPen(border_color, 2 if self.isSelected() or self.is_dirty else 1))
        painter.drawRoundedRect(0, 0, self.width, self.height, 8, 8)

        header_color = QColor("#E65100") if self.is_dirty else QColor("#00796B")
        painter.setBrush(QBrush(header_color))
        painter.drawRoundedRect(0, 0, self.width, 24, 8, 8)
        painter.fillRect(0, 14, self.width, 10, header_color)
        
        painter.setPen(QPen(Qt.white))
        status_badge = "⚠️" if self.is_dirty else "✓"
        painter.drawText(QRectF(8, 3, self.width - 16, 18), Qt.AlignLeft | Qt.AlignVCenter, f"{status_badge} Moyenne Glissante (FIR)")

        painter.setPen(QPen(QColor("#EEEEEE")))
        painter.drawText(QRectF(10, 32, self.width - 20, 20), Qt.AlignLeft, self.params["name"])

        src_info = self.input_node.params['name'] if self.input_node else "Aucune"
        painter.setPen(QPen(QColor("#B0BEC5")))
        n_val = self.params.get('sample_size', 16)
        painter.drawText(QRectF(10, 54, self.width - 20, 18), Qt.AlignLeft, f"Fenêtre: N={n_val} points")
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



class MedianFilterNode(QGraphicsItem):
    """Nœud 'Filtre Médian' (Catégorie Filtres Numériques DSP - Vert Canard #00695C)."""
    def __init__(self, name="Filtre Médian 1", x=0, y=0):
        super().__init__()
        self.node_type = "median_filter"
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
            "kernel_size": 5,                               # N impair (3, 5, 7, 9...)
            "rate_mode": "Fréquence (Hz)",
            "sampling_rate": 1000.0,
            "time_offset": 0.0
        }
        self.is_dirty = True
        self.t_data = None
        self.y_data = None

    def mark_dirty(self):
        self.is_dirty = True
        self.update()

    def recalculate(self):
        if self.input_node and self.input_node.t_data is not None and self.input_node.y_data is not None:
            self.t_data, self.y_data = DSPFilterEngine.median_filter(
                self.input_node.t_data,
                self.input_node.y_data,
                kernel_size=int(self.params.get("kernel_size", 5)),
                sampling_rate=float(self.params.get("sampling_rate", 1000.0)),
                time_offset=float(self.params.get("time_offset", 0.0))
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
        border_color = QColor("#FF9800") if self.is_dirty else QColor("#00695C")
        if self.isSelected():
            border_color = QColor("#FFFFFF")

        painter.setBrush(QBrush(QColor("#2B2E3A")))
        painter.setPen(QPen(border_color, 2 if self.isSelected() or self.is_dirty else 1))
        painter.drawRoundedRect(0, 0, self.width, self.height, 8, 8)

        header_color = QColor("#E65100") if self.is_dirty else QColor("#00695C")
        painter.setBrush(QBrush(header_color))
        painter.drawRoundedRect(0, 0, self.width, 24, 8, 8)
        painter.fillRect(0, 14, self.width, 10, header_color)
        
        painter.setPen(QPen(Qt.white))
        status_badge = "⚠️" if self.is_dirty else "✓"
        painter.drawText(QRectF(8, 3, self.width - 16, 18), Qt.AlignLeft | Qt.AlignVCenter, f"{status_badge} Filtre Médian (Impuls.)")

        painter.setPen(QPen(QColor("#EEEEEE")))
        painter.drawText(QRectF(10, 32, self.width - 20, 20), Qt.AlignLeft, self.params["name"])

        src_info = self.input_node.params['name'] if self.input_node else "Aucune"
        painter.setPen(QPen(QColor("#B0BEC5")))
        n_val = self.params.get('kernel_size', 5)
        painter.drawText(QRectF(10, 54, self.width - 20, 18), Qt.AlignLeft, f"Taille: N={n_val} pts")
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
