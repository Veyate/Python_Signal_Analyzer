from PySide6.QtCore import Qt, QRectF
from PySide6.QtGui import QColor, QBrush, QPen, QPainter
from PySide6.QtWidgets import QGraphicsItem
from engine import FilterEngine


class LowPassFilterNode(QGraphicsItem):
    """Nœud 'Filtre Passe-Bas' (Catégorie Filtre)."""
    def __init__(self, name="Filtre Passe-Bas 1", x=0, y=0):
        super().__init__()
        self.node_type = "lowpass_filter"
        self.width = 175
        self.height = 95
        self.setPos(x, y)
        self.setFlags(
            QGraphicsItem.ItemIsMovable |
            QGraphicsItem.ItemIsSelectable |
            QGraphicsItem.ItemSendsGeometryChanges
        )
        self.connections = []

        self.input_node = None  # Nœud source connecté en entrée

        self.params = {
            "name": name,
            "cutoff": 10.0,            # Fréquence de coupure fc (Hz)
            "order": 2,                # Ordre du filtre
            "filter_type": "Butterworth"
        }
        
        self.is_dirty = True
        self.t_data = None
        self.y_data = None

    def mark_dirty(self):
        self.is_dirty = True
        self.update()

    def recalculate(self):
        """Exécute le filtrage sur le signal de la source d'entrée."""
        if self.input_node and self.input_node.t_data is not None and self.input_node.y_data is not None:
            self.t_data = self.input_node.t_data
            y_in = self.input_node.y_data
            sampling_rate = self.input_node.params.get("sampling_rate", 1000.0)

            self.y_data = FilterEngine.apply_filter(
                t=self.t_data,
                y=y_in,
                cutoff_freq=self.params["cutoff"],
                sampling_rate=sampling_rate,
                order=self.params["order"],
                filter_type=self.params["filter_type"],
                btype="low"
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
        border_color = QColor("#FF9800") if self.is_dirty else QColor("#9C27B0")
        if self.isSelected():
            border_color = QColor("#FFFFFF")

        # Corps
        painter.setBrush(QBrush(QColor("#2B2E3A")))
        painter.setPen(QPen(border_color, 2 if self.isSelected() or self.is_dirty else 1))
        painter.drawRoundedRect(0, 0, self.width, self.height, 8, 8)

        # En-tête (Violet)
        header_color = QColor("#E65100") if self.is_dirty else QColor("#9C27B0")
        painter.setBrush(QBrush(header_color))
        painter.drawRoundedRect(0, 0, self.width, 24, 8, 8)
        painter.fillRect(0, 14, self.width, 10, header_color)
        
        painter.setPen(QPen(Qt.white))
        status_badge = "⚠️" if self.is_dirty else "✓"
        painter.drawText(QRectF(8, 3, self.width - 16, 18), Qt.AlignLeft | Qt.AlignVCenter, f"{status_badge} Filtre Passe-Bas")

        # Nom
        painter.setPen(QPen(QColor("#EEEEEE")))
        painter.drawText(QRectF(10, 32, self.width - 20, 20), Qt.AlignLeft, self.params["name"])

        # Paramètres
        src_info = self.input_node.params['name'] if self.input_node else "Aucune"
        painter.setPen(QPen(QColor("#B0BEC5")))
        painter.drawText(QRectF(10, 54, self.width - 20, 18), Qt.AlignLeft, f"fc: {self.params['cutoff']} Hz | Ordre: {self.params['order']}")
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


class HighPassFilterNode(QGraphicsItem):
    """Nœud 'Filtre Passe-Haut' (Catégorie Filtre)."""
    def __init__(self, name="Filtre Passe-Haut 1", x=0, y=0):
        super().__init__()
        self.node_type = "highpass_filter"
        self.width = 175
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
            "cutoff": 50.0,            # Fréquence de coupure fc (Hz)
            "order": 2,                # Ordre du filtre
            "filter_type": "Butterworth"
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
            y_in = self.input_node.y_data
            sampling_rate = self.input_node.params.get("sampling_rate", 1000.0)

            self.y_data = FilterEngine.apply_filter(
                t=self.t_data,
                y=y_in,
                cutoff_freq=self.params["cutoff"],
                sampling_rate=sampling_rate,
                order=self.params["order"],
                filter_type=self.params["filter_type"],
                btype="high"
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
        status_badge = "⚠️" if self.is_dirty else "✓"
        painter.drawText(QRectF(8, 3, self.width - 16, 18), Qt.AlignLeft | Qt.AlignVCenter, f"{status_badge} Filtre Passe-Haut")

        painter.setPen(QPen(QColor("#EEEEEE")))
        painter.drawText(QRectF(10, 32, self.width - 20, 20), Qt.AlignLeft, self.params["name"])

        src_info = self.input_node.params['name'] if self.input_node else "Aucune"
        painter.setPen(QPen(QColor("#B0BEC5")))
        painter.drawText(QRectF(10, 54, self.width - 20, 18), Qt.AlignLeft, f"fc: {self.params['cutoff']} Hz | Ordre: {self.params['order']}")
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


class BandPassFilterNode(QGraphicsItem):
    """Nœud 'Filtre Passe-Bande' (Catégorie Filtre)."""
    def __init__(self, name="Filtre Passe-Bande 1", x=0, y=0):
        super().__init__()
        self.node_type = "bandpass_filter"
        self.width = 180
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
            "low_cutoff": 10.0,         # f1 (Hz)
            "high_cutoff": 100.0,       # f2 (Hz)
            "order": 2,                 # Ordre du filtre
            "filter_type": "Butterworth"
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
            y_in = self.input_node.y_data
            sampling_rate = self.input_node.params.get("sampling_rate", 1000.0)

            self.y_data = FilterEngine.apply_filter(
                t=self.t_data,
                y=y_in,
                cutoff_freq=[self.params["low_cutoff"], self.params["high_cutoff"]],
                sampling_rate=sampling_rate,
                order=self.params["order"],
                filter_type=self.params["filter_type"],
                btype="bandpass"
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
        status_badge = "⚠️" if self.is_dirty else "✓"
        painter.drawText(QRectF(8, 3, self.width - 16, 18), Qt.AlignLeft | Qt.AlignVCenter, f"{status_badge} Filtre Passe-Bande")

        painter.setPen(QPen(QColor("#EEEEEE")))
        painter.drawText(QRectF(10, 32, self.width - 20, 20), Qt.AlignLeft, self.params["name"])

        src_info = self.input_node.params['name'] if self.input_node else "Aucune"
        painter.setPen(QPen(QColor("#B0BEC5")))
        painter.drawText(QRectF(10, 54, self.width - 20, 18), Qt.AlignLeft, f"[{self.params['low_cutoff']} - {self.params['high_cutoff']}] Hz")
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


class BandStopFilterNode(QGraphicsItem):
    """Nœud 'Filtre Coupe-Bande' (Catégorie Filtre)."""
    def __init__(self, name="Filtre Coupe-Bande 1", x=0, y=0):
        super().__init__()
        self.node_type = "bandstop_filter"
        self.width = 180
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
            "low_cutoff": 48.0,         # f1 (Hz) e.g. rejet 50Hz
            "high_cutoff": 52.0,        # f2 (Hz)
            "order": 2,                 # Ordre du filtre
            "filter_type": "Butterworth"
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
            y_in = self.input_node.y_data
            sampling_rate = self.input_node.params.get("sampling_rate", 1000.0)

            self.y_data = FilterEngine.apply_filter(
                t=self.t_data,
                y=y_in,
                cutoff_freq=[self.params["low_cutoff"], self.params["high_cutoff"]],
                sampling_rate=sampling_rate,
                order=self.params["order"],
                filter_type=self.params["filter_type"],
                btype="bandstop"
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
        status_badge = "⚠️" if self.is_dirty else "✓"
        painter.drawText(QRectF(8, 3, self.width - 16, 18), Qt.AlignLeft | Qt.AlignVCenter, f"{status_badge} Coupe-Bande")

        painter.setPen(QPen(QColor("#EEEEEE")))
        painter.drawText(QRectF(10, 32, self.width - 20, 20), Qt.AlignLeft, self.params["name"])

        src_info = self.input_node.params['name'] if self.input_node else "Aucune"
        painter.setPen(QPen(QColor("#B0BEC5")))
        painter.drawText(QRectF(10, 54, self.width - 20, 18), Qt.AlignLeft, f"Rejet [{self.params['low_cutoff']}-{self.params['high_cutoff']}] Hz")
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
