# nodes/noise.py
from PySide6.QtCore import Qt, QRectF
from PySide6.QtGui import QColor, QBrush, QPen, QPainter
from PySide6.QtWidgets import QGraphicsItem
from engine import NoiseEngine


class NoiseNode(QGraphicsItem):
    """Nœud 'Injecteur de Bruit' (Catégorie Bruits & Perturbations - Orange/Ambre #FF9800)."""
    def __init__(self, name="Injecteur de Bruit 1", x=0, y=0):
        super().__init__()
        self.node_type = "noise_generator"
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
            "noise_type": "Bruit blanc gaussien",
            "std_dev": 0.1,
            "spike_prob": 0.01,
            "spike_amp": 1.0
        }
        self.is_dirty = True
        self.t_data = None
        self.y_data = None

    def mark_dirty(self):
        self.is_dirty = True
        self.update()

    def recalculate(self):
        if self.input_node and self.input_node.t_data is not None and self.input_node.y_data is not None:
            self.t_data = self.input_node.t_data
            self.y_data = NoiseEngine.apply_noise(
                self.t_data,
                self.input_node.y_data,
                noise_type=self.params.get("noise_type", "Bruit blanc gaussien"),
                std_dev=float(self.params.get("std_dev", 0.1)),
                spike_prob=float(self.params.get("spike_prob", 0.01)),
                spike_amp=float(self.params.get("spike_amp", 1.0))
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
        border_color = QColor("#FF9800") if self.is_dirty else QColor("#F57C00")
        if self.isSelected():
            border_color = QColor("#FFFFFF")

        painter.setBrush(QBrush(QColor("#2B2E3A")))
        painter.setPen(QPen(border_color, 2 if self.isSelected() or self.is_dirty else 1))
        painter.drawRoundedRect(0, 0, self.width, self.height, 8, 8)

        header_color = QColor("#E65100") if self.is_dirty else QColor("#F57C00")
        painter.setBrush(QBrush(header_color))
        painter.drawRoundedRect(0, 0, self.width, 24, 8, 8)
        painter.fillRect(0, 14, self.width, 10, header_color)
        
        painter.setPen(QPen(Qt.white))
        status_badge = "⚠️" if self.is_dirty else "✓"
        painter.drawText(QRectF(8, 3, self.width - 16, 18), Qt.AlignLeft | Qt.AlignVCenter, f"{status_badge} Bruit & Perturbations")

        painter.setPen(QPen(QColor("#EEEEEE")))
        painter.drawText(QRectF(10, 32, self.width - 20, 20), Qt.AlignLeft, self.params["name"])

        src_info = self.input_node.params['name'] if self.input_node else "Aucune"
        painter.setPen(QPen(QColor("#B0BEC5")))
        n_short = self.params.get('noise_type', 'Bruit')[:15]
        painter.drawText(QRectF(10, 54, self.width - 20, 18), Qt.AlignLeft, f"Type: {n_short}")
        painter.drawText(QRectF(10, 72, self.width - 20, 18), Qt.AlignLeft, f"In: {src_info}")

        # Entrée / Sortie sockets
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
