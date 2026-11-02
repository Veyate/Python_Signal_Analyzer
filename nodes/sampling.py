# nodes/sampling.py
from PySide6.QtCore import Qt, QRectF
from PySide6.QtGui import QColor, QBrush, QPen, QPainter
from PySide6.QtWidgets import QGraphicsItem
from engine import SamplingConversionEngine


class ResampleNode(QGraphicsItem):
    """Nœud 'Rééchantillonnage' (Catégorie Échantillonnage & Conversion - Bleu #0288D1)."""
    def __init__(self, name="Rééchantillonnage 1", x=0, y=0):
        super().__init__()
        self.node_type = "resample"
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
            "target_fs": 500.0,
            "anti_aliasing": True
        }
        self.is_dirty = True
        self.t_data = None
        self.y_data = None

    def mark_dirty(self):
        self.is_dirty = True
        self.update()

    def recalculate(self):
        if self.input_node and self.input_node.t_data is not None and self.input_node.y_data is not None:
            self.t_data, self.y_data = SamplingConversionEngine.resample_signal(
                self.input_node.t_data,
                self.input_node.y_data,
                target_fs=float(self.params.get("target_fs", 500.0)),
                anti_aliasing=bool(self.params.get("anti_aliasing", True))
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
        border_color = QColor("#FF9800") if self.is_dirty else QColor("#0288D1")
        if self.isSelected():
            border_color = QColor("#FFFFFF")

        painter.setBrush(QBrush(QColor("#2B2E3A")))
        painter.setPen(QPen(border_color, 2 if self.isSelected() or self.is_dirty else 1))
        painter.drawRoundedRect(0, 0, self.width, self.height, 8, 8)

        header_color = QColor("#E65100") if self.is_dirty else QColor("#0288D1")
        painter.setBrush(QBrush(header_color))
        painter.drawRoundedRect(0, 0, self.width, 24, 8, 8)
        painter.fillRect(0, 14, self.width, 10, header_color)
        
        painter.setPen(QPen(Qt.white))
        status_badge = "⚠️" if self.is_dirty else "✓"
        painter.drawText(QRectF(8, 3, self.width - 16, 18), Qt.AlignLeft | Qt.AlignVCenter, f"{status_badge} Rééchantillonnage")

        painter.setPen(QPen(QColor("#EEEEEE")))
        painter.drawText(QRectF(10, 32, self.width - 20, 20), Qt.AlignLeft, self.params["name"])

        src_info = self.input_node.params['name'] if self.input_node else "Aucune"
        painter.setPen(QPen(QColor("#B0BEC5")))
        painter.drawText(QRectF(10, 54, self.width - 20, 18), Qt.AlignLeft, f"Fs cible: {self.params.get('target_fs', 500.0)} Hz")
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


class InterpolationNode(QGraphicsItem):
    """Nœud 'Interpolation & Extrapolation' (Catégorie Échantillonnage & Conversion - Bleu #0288D1)."""
    def __init__(self, name="Interpolation 1", x=0, y=0):
        super().__init__()
        self.node_type = "interpolation"
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
            "target_fs": 1000.0,
            "interp_method": "Linéaire",
            "extrap_mode": "Maintien (Hold)"
        }
        self.is_dirty = True
        self.t_data = None
        self.y_data = None

    def mark_dirty(self):
        self.is_dirty = True
        self.update()

    def recalculate(self):
        if self.input_node and self.input_node.t_data is not None and self.input_node.y_data is not None:
            self.t_data, self.y_data = SamplingConversionEngine.interpolate_signal(
                self.input_node.t_data,
                self.input_node.y_data,
                target_fs=float(self.params.get("target_fs", 1000.0)),
                method=self.params.get("interp_method", "Linéaire"),
                extrap=self.params.get("extrap_mode", "Maintien (Hold)")
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
        border_color = QColor("#FF9800") if self.is_dirty else QColor("#0288D1")
        if self.isSelected():
            border_color = QColor("#FFFFFF")

        painter.setBrush(QBrush(QColor("#2B2E3A")))
        painter.setPen(QPen(border_color, 2 if self.isSelected() or self.is_dirty else 1))
        painter.drawRoundedRect(0, 0, self.width, self.height, 8, 8)

        header_color = QColor("#E65100") if self.is_dirty else QColor("#0288D1")
        painter.setBrush(QBrush(header_color))
        painter.drawRoundedRect(0, 0, self.width, 24, 8, 8)
        painter.fillRect(0, 14, self.width, 10, header_color)
        
        painter.setPen(QPen(Qt.white))
        status_badge = "⚠️" if self.is_dirty else "✓"
        painter.drawText(QRectF(8, 3, self.width - 16, 18), Qt.AlignLeft | Qt.AlignVCenter, f"{status_badge} Interpolation/Extrap")

        painter.setPen(QPen(QColor("#EEEEEE")))
        painter.drawText(QRectF(10, 32, self.width - 20, 20), Qt.AlignLeft, self.params["name"])

        src_info = self.input_node.params['name'] if self.input_node else "Aucune"
        painter.setPen(QPen(QColor("#B0BEC5")))
        m_short = self.params.get('interp_method', 'Linéaire')[:12]
        painter.drawText(QRectF(10, 54, self.width - 20, 18), Qt.AlignLeft, f"Méthode: {m_short}")
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


class DACNode(QGraphicsItem):
    """Nœud 'Simulation DAC' (Catégorie Échantillonnage & Conversion - Bleu #1E88E5)."""
    def __init__(self, name="Simulation DAC 1", x=0, y=0):
        super().__init__()
        self.node_type = "dac_simulation"
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
            "sampling_rate": 100.0,            # Fréquence d'échantillonnage DAC f_s (Hz)
            "resolution_bits": 8,               # N bits (8, 10, 12, 16...)
            "vref": 5.0,                        # Tension de référence Vref (V)
            "offset_dc": 2.5,                   # Décalage DC d'entrée V_DC (V)
            "output_unit": "Code Numérique (LSB)", # Unité de sortie (LSB ou V)
            "reconstruction": "Bloqueur d'ordre zéro (ZOH)"
        }
        self.is_dirty = True
        self.t_data = None
        self.y_data = None

    def mark_dirty(self):
        self.is_dirty = True
        self.update()

    def recalculate(self):
        if self.input_node and self.input_node.t_data is not None and self.input_node.y_data is not None:
            self.t_data, self.y_data = SamplingConversionEngine.dac_simulation(
                self.input_node.t_data,
                self.input_node.y_data,
                dac_fs=float(self.params.get("sampling_rate", 100.0)),
                bits=int(self.params.get("resolution_bits", 8)),
                vref=float(self.params.get("vref", 5.0)),
                offset_dc=float(self.params.get("offset_dc", 2.5)),
                output_unit=self.params.get("output_unit", "Code Numérique (LSB)"),
                mode=self.params.get("reconstruction", "Bloqueur d'ordre zéro (ZOH)"),
                vref_min=self.params.get("vref_min"),
                vref_max=self.params.get("vref_max")
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
        border_color = QColor("#FF9800") if self.is_dirty else QColor("#1E88E5")
        if self.isSelected():
            border_color = QColor("#FFFFFF")

        painter.setBrush(QBrush(QColor("#2B2E3A")))
        painter.setPen(QPen(border_color, 2 if self.isSelected() or self.is_dirty else 1))
        painter.drawRoundedRect(0, 0, self.width, self.height, 8, 8)

        header_color = QColor("#E65100") if self.is_dirty else QColor("#1E88E5")
        painter.setBrush(QBrush(header_color))
        painter.drawRoundedRect(0, 0, self.width, 24, 8, 8)
        painter.fillRect(0, 14, self.width, 10, header_color)
        
        painter.setPen(QPen(Qt.white))
        status_badge = "⚠️" if self.is_dirty else "✓"
        painter.drawText(QRectF(8, 3, self.width - 16, 18), Qt.AlignLeft | Qt.AlignVCenter, f"{status_badge} Simulation DAC")

        painter.setPen(QPen(QColor("#EEEEEE")))
        painter.drawText(QRectF(10, 32, self.width - 20, 20), Qt.AlignLeft, self.params["name"])

        src_info = self.input_node.params['name'] if self.input_node else "Aucune"
        painter.setPen(QPen(QColor("#B0BEC5")))
        unit_str = "LSB" if "lsb" in str(self.params.get("output_unit", "")).lower() else "V"
        painter.drawText(QRectF(10, 54, self.width - 20, 18), Qt.AlignLeft, f"Fs: {self.params.get('sampling_rate', 100.0)}Hz | {self.params.get('resolution_bits', 8)}bits ({unit_str})")
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
