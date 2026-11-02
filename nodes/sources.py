import os
from PySide6.QtCore import Qt, QRectF
from PySide6.QtGui import QColor, QBrush, QPen, QPainter
from PySide6.QtWidgets import QGraphicsItem
from engine import SignalGeneratorEngine, CSVImportEngine


class SignalGeneratorNode(QGraphicsItem):
    """Nœud 'Générateur simple' (Catégorie Source)."""
    def __init__(self, name="Générateur 1", x=0, y=0):
        super().__init__()
        self.node_type = "generator"
        self.width = 170
        self.height = 90
        self.setPos(x, y)
        self.setFlags(
            QGraphicsItem.ItemIsMovable |
            QGraphicsItem.ItemIsSelectable |
            QGraphicsItem.ItemSendsGeometryChanges
        )
        self.connections = []

        self.params = {
            "name": name,
            "waveform": "Sinus",
            "frequency": 5.0,        # Hz
            "amplitude": 1.0,        # V
            "sampling_rate": 1000.0, # Hz
            "duration": 1.0,         # s
            "offset": 0.0,
            "phase": 0.0
        }
        
        self.is_dirty = True
        self.t_data = None
        self.y_data = None
        self.recalculate()

    def mark_dirty(self):
        self.is_dirty = True
        self.update()

    def recalculate(self):
        self.t_data, self.y_data = SignalGeneratorEngine.generate_signal(
            waveform=self.params["waveform"],
            frequency=self.params["frequency"],
            amplitude=self.params["amplitude"],
            sampling_rate=self.params["sampling_rate"],
            duration=self.params["duration"],
            offset=self.params["offset"],
            phase_deg=self.params.get("phase", 0.0)
        )
        self.is_dirty = False
        self.update()

    def boundingRect(self):
        margin = 12
        return QRectF(-margin, -margin, self.width + 2 * margin, self.height + 2 * margin)

    def paint(self, painter, option, widget=None):
        painter.setRenderHint(QPainter.Antialiasing, True)
        border_color = QColor("#FF9800") if self.is_dirty else QColor("#00ADB5")
        if self.isSelected():
            border_color = QColor("#FFFFFF")

        # Corps du nœud
        painter.setBrush(QBrush(QColor("#2B2E3A")))
        painter.setPen(QPen(border_color, 2 if self.isSelected() or self.is_dirty else 1))
        painter.drawRoundedRect(0, 0, self.width, self.height, 8, 8)

        # En-tête (Cyan)
        header_color = QColor("#E65100") if self.is_dirty else QColor("#00ADB5")
        painter.setBrush(QBrush(header_color))
        painter.drawRoundedRect(0, 0, self.width, 24, 8, 8)
        painter.fillRect(0, 14, self.width, 10, header_color)
        
        # Titre En-tête
        painter.setPen(QPen(Qt.white))
        status_badge = "⚠️" if self.is_dirty else "✓"
        painter.drawText(QRectF(8, 3, self.width - 16, 18), Qt.AlignLeft | Qt.AlignVCenter, f"{status_badge} Générateur simple")

        # Libellés
        painter.setPen(QPen(QColor("#EEEEEE")))
        painter.drawText(QRectF(10, 32, self.width - 20, 20), Qt.AlignLeft, self.params["name"])

        painter.setPen(QPen(QColor("#AAAAAA")))
        painter.drawText(QRectF(10, 56, self.width - 20, 20), Qt.AlignLeft, f"~ {self.params['waveform']} ({self.params['frequency']} Hz)")

        # Port de sortie (droit)
        painter.setBrush(QBrush(QColor("#FF5722")))
        painter.setPen(QPen(QColor("#FFFFFF"), 1.5))
        painter.drawEllipse(self.width - 6, self.height // 2 - 6, 12, 12)

    def itemChange(self, change, value):
        if change in (QGraphicsItem.ItemPositionHasChanged, QGraphicsItem.ItemPositionChange):
            for conn in self.connections:
                conn.update_path()
        return super().itemChange(change, value)


class CSVImportNode(QGraphicsItem):
    """Nœud 'Import CSV' (Catégorie Source)."""
    def __init__(self, name="Import CSV 1", x=0, y=0):
        super().__init__()
        self.node_type = "csv_import"
        self.width = 175
        self.height = 90
        self.setPos(x, y)
        self.setFlags(
            QGraphicsItem.ItemIsMovable |
            QGraphicsItem.ItemIsSelectable |
            QGraphicsItem.ItemSendsGeometryChanges
        )
        self.connections = []

        self.params = {
            "name": name,
            "file_path": "",
            "delimiter": "Virgule (,)",
            "has_header": True,
            "time_col_idx": 0,
            "signal_col_idx": 1,
            "sampling_rate": 1000.0
        }
        
        self.is_dirty = True
        self.status_msg = "Aucun fichier"
        self.t_data = None
        self.y_data = None

    def mark_dirty(self):
        self.is_dirty = True
        self.update()

    def recalculate(self):
        self.t_data, self.y_data, self.status_msg = CSVImportEngine.load_csv(
            file_path=self.params["file_path"],
            delimiter_str=self.params["delimiter"],
            has_header=self.params["has_header"],
            time_col_idx=self.params["time_col_idx"],
            signal_col_idx=self.params["signal_col_idx"],
            default_sampling_rate=self.params["sampling_rate"]
        )
        self.is_dirty = False
        self.update()

    def boundingRect(self):
        margin = 12
        return QRectF(-margin, -margin, self.width + 2 * margin, self.height + 2 * margin)

    def paint(self, painter, option, widget=None):
        painter.setRenderHint(QPainter.Antialiasing, True)
        
        border_color = QColor("#FF9800") if self.is_dirty else QColor("#00ADB5")
        if self.isSelected():
            border_color = QColor("#FFFFFF")

        # Corps
        painter.setBrush(QBrush(QColor("#2B2E3A")))
        painter.setPen(QPen(border_color, 2 if self.isSelected() or self.is_dirty else 1))
        painter.drawRoundedRect(0, 0, self.width, self.height, 8, 8)

        # En-tête (Cyan)
        header_color = QColor("#E65100") if self.is_dirty else QColor("#00ADB5")
        painter.setBrush(QBrush(header_color))
        painter.drawRoundedRect(0, 0, self.width, 24, 8, 8)
        painter.fillRect(0, 14, self.width, 10, header_color)
        
        # Titre
        painter.setPen(QPen(Qt.white))
        status_badge = "⚠️" if self.is_dirty else "✓"
        painter.drawText(QRectF(8, 3, self.width - 16, 18), Qt.AlignLeft | Qt.AlignVCenter, f"{status_badge} Import CSV")

        # Nom
        painter.setPen(QPen(QColor("#EEEEEE")))
        painter.drawText(QRectF(10, 32, self.width - 20, 20), Qt.AlignLeft, self.params["name"])

        # Info Fichier
        file_disp = os.path.basename(self.params["file_path"]) if self.params["file_path"] else "Aucun fichier"
        painter.setPen(QPen(QColor("#AAAAAA")))
        painter.drawText(QRectF(10, 56, self.width - 20, 20), Qt.AlignLeft, f"📁 {file_disp[:18]}")

        # Port de sortie (droit)
        painter.setBrush(QBrush(QColor("#FF5722")))
        painter.setPen(QPen(QColor("#FFFFFF"), 1.5))
        painter.drawEllipse(self.width - 6, self.height // 2 - 6, 12, 12)

    def itemChange(self, change, value):
        if change in (QGraphicsItem.ItemPositionHasChanged, QGraphicsItem.ItemPositionChange):
            for conn in self.connections:
                conn.update_path()
        return super().itemChange(change, value)
