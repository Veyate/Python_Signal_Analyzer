# nodes/do160.py
from PySide6.QtCore import Qt, QRectF
from PySide6.QtGui import QColor, QBrush, QPen, QPainter
from PySide6.QtWidgets import QGraphicsItem
from engine import DO160Engine


class DO160DoubleExpNode(QGraphicsItem):
    """Nœud Générateur Impulsion Double Exponentielle DO-160 Section 22 (Rouge Foudre #D81B60)."""
    def __init__(self, name="Impulsion DO-160 1", x=0, y=0):
        super().__init__()
        self.node_type = "do160_double_exp"
        self.width = 195
        self.height = 95
        self.setPos(x, y)
        self.setFlags(
            QGraphicsItem.ItemIsMovable |
            QGraphicsItem.ItemIsSelectable |
            QGraphicsItem.ItemSendsGeometryChanges
        )
        self.connections = []
        self.input_node = None  # Source autonome

        self.params = {
            "name": name,
            "preset": "WF4 (6.4 µs / 69 µs - Tension)",
            "level": "Niveau 3 (300V / 600A)",
            "v_peak": 300.0,
            "t1_us": 6.4,
            "t2_us": 69.0,
            "t2_mode": "50% Amplitude (Standard)",
            "t_offset_us": 1.0,
            "sampling_rate_mhz": 50.0,
            "duration_us": 200.0
        }
        self.is_dirty = True
        self.t_data = None
        self.y_data = None
        self.recalculate()

    def mark_dirty(self):
        self.is_dirty = True
        self.update()

    def recalculate(self):
        self.t_data, self.y_data = DO160Engine.generate_double_exponential(
            t1_us=float(self.params.get("t1_us", 6.4)),
            t2_us=float(self.params.get("t2_us", 69.0)),
            v_peak=float(self.params.get("v_peak", 300.0)),
            t2_mode=str(self.params.get("t2_mode", "50% Amplitude (Standard)")),
            t_offset_us=float(self.params.get("t_offset_us", 1.0)),
            sampling_rate_mhz=float(self.params.get("sampling_rate_mhz", 50.0)),
            duration_us=float(self.params.get("duration_us", 200.0))
        )
        self.is_dirty = False
        self.update()

    def boundingRect(self):
        margin = 12
        return QRectF(-margin, -margin, self.width + 2 * margin, self.height + 2 * margin)

    def paint(self, painter, option, widget=None):
        painter.setRenderHint(QPainter.Antialiasing, True)
        border_color = QColor("#FF9800") if self.is_dirty else QColor("#D81B60")
        if self.isSelected():
            border_color = QColor("#FFFFFF")

        painter.setBrush(QBrush(QColor("#2B2E3A")))
        painter.setPen(QPen(border_color, 2 if self.isSelected() or self.is_dirty else 1))
        painter.drawRoundedRect(0, 0, self.width, self.height, 8, 8)

        header_color = QColor("#E65100") if self.is_dirty else QColor("#D81B60")
        painter.setBrush(QBrush(header_color))
        painter.drawRoundedRect(0, 0, self.width, 24, 8, 8)
        painter.fillRect(0, 14, self.width, 10, header_color)
        
        painter.setPen(QPen(Qt.white))
        status_badge = "⚠️" if self.is_dirty else "⚡"
        painter.drawText(QRectF(8, 3, self.width - 16, 18), Qt.AlignLeft | Qt.AlignVCenter, f"{status_badge} DO-160 Double Exp")

        painter.setPen(QPen(QColor("#EEEEEE")))
        painter.drawText(QRectF(10, 32, self.width - 20, 20), Qt.AlignLeft, self.params["name"])

        painter.setPen(QPen(QColor("#B0BEC5")))
        t1 = self.params.get('t1_us', 6.4)
        t2 = self.params.get('t2_us', 69.0)
        v = self.params.get('v_peak', 300.0)
        painter.drawText(QRectF(10, 54, self.width - 20, 18), Qt.AlignLeft, f"T1/T2: {t1}/{t2} µs")
        painter.drawText(QRectF(10, 72, self.width - 20, 18), Qt.AlignLeft, f"Vpeak: {v} V")

        painter.setBrush(QBrush(QColor("#FF5722")))
        painter.setPen(QPen(QColor("#FFFFFF"), 1.5))
        painter.drawEllipse(self.width - 6, self.height // 2 - 6, 12, 12)

    def itemChange(self, change, value):
        if change in (QGraphicsItem.ItemPositionHasChanged, QGraphicsItem.ItemPositionChange):
            for conn in self.connections:
                conn.update_path()
        return super().itemChange(change, value)


class DO160DampedSineNode(QGraphicsItem):
    """Nœud Générateur Sinus Amorti WF3 DO-160 Section 22 (Rouge Violet #C2185B)."""
    def __init__(self, name="Sinus Amorti WF3 1", x=0, y=0):
        super().__init__()
        self.node_type = "do160_damped_sine"
        self.width = 195
        self.height = 95
        self.setPos(x, y)
        self.setFlags(
            QGraphicsItem.ItemIsMovable |
            QGraphicsItem.ItemIsSelectable |
            QGraphicsItem.ItemSendsGeometryChanges
        )
        self.connections = []
        self.input_node = None  # Source autonome

        self.params = {
            "name": name,
            "preset": "WF3 - 1 MHz (Sinus Amorti)",
            "level": "Niveau 3 (300V / 600A)",
            "v_peak": 600.0,
            "freq_mhz": 1.0,
            "r5_percent": 50.0,
            "phase_deg": 0.0,
            "t_offset_us": 1.0,
            "sampling_rate_mhz": 100.0,
            "duration_us": 10.0
        }
        self.is_dirty = True
        self.t_data = None
        self.y_data = None
        self.recalculate()

    def mark_dirty(self):
        self.is_dirty = True
        self.update()

    def recalculate(self):
        self.t_data, self.y_data = DO160Engine.generate_damped_sine(
            freq_mhz=float(self.params.get("freq_mhz", 1.0)),
            v_peak=float(self.params.get("v_peak", 600.0)),
            r5_percent=float(self.params.get("r5_percent", 50.0)),
            phase_deg=float(self.params.get("phase_deg", 0.0)),
            t_offset_us=float(self.params.get("t_offset_us", 1.0)),
            sampling_rate_mhz=float(self.params.get("sampling_rate_mhz", 100.0)),
            duration_us=float(self.params.get("duration_us", 10.0))
        )
        self.is_dirty = False
        self.update()

    def boundingRect(self):
        margin = 12
        return QRectF(-margin, -margin, self.width + 2 * margin, self.height + 2 * margin)

    def paint(self, painter, option, widget=None):
        painter.setRenderHint(QPainter.Antialiasing, True)
        border_color = QColor("#FF9800") if self.is_dirty else QColor("#C2185B")
        if self.isSelected():
            border_color = QColor("#FFFFFF")

        painter.setBrush(QBrush(QColor("#2B2E3A")))
        painter.setPen(QPen(border_color, 2 if self.isSelected() or self.is_dirty else 1))
        painter.drawRoundedRect(0, 0, self.width, self.height, 8, 8)

        header_color = QColor("#E65100") if self.is_dirty else QColor("#C2185B")
        painter.setBrush(QBrush(header_color))
        painter.drawRoundedRect(0, 0, self.width, 24, 8, 8)
        painter.fillRect(0, 14, self.width, 10, header_color)
        
        painter.setPen(QPen(Qt.white))
        status_badge = "⚠️" if self.is_dirty else "⚡"
        painter.drawText(QRectF(8, 3, self.width - 16, 18), Qt.AlignLeft | Qt.AlignVCenter, f"{status_badge} DO-160 Sinus Amorti")

        painter.setPen(QPen(QColor("#EEEEEE")))
        painter.drawText(QRectF(10, 32, self.width - 20, 20), Qt.AlignLeft, self.params["name"])

        painter.setPen(QPen(QColor("#B0BEC5")))
        f = self.params.get('freq_mhz', 1.0)
        v = self.params.get('v_peak', 600.0)
        r5 = self.params.get('r5_percent', 50.0)
        painter.drawText(QRectF(10, 54, self.width - 20, 18), Qt.AlignLeft, f"Fréq: {f} MHz | R5: {r5}%")
        painter.drawText(QRectF(10, 72, self.width - 20, 18), Qt.AlignLeft, f"Vpeak: {v} V")

        painter.setBrush(QBrush(QColor("#FF5722")))
        painter.setPen(QPen(QColor("#FFFFFF"), 1.5))
        painter.drawEllipse(self.width - 6, self.height // 2 - 6, 12, 12)

        painter.setItemChange = True

    def itemChange(self, change, value):
        if change in (QGraphicsItem.ItemPositionHasChanged, QGraphicsItem.ItemPositionChange):
            for conn in self.connections:
                conn.update_path()
        return super().itemChange(change, value)
