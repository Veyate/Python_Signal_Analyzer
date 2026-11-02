# nodes/maths.py
from PySide6.QtCore import Qt, QRectF
from PySide6.QtGui import QColor, QBrush, QPen, QPainter
from PySide6.QtWidgets import QGraphicsItem
from engine import MathOperatorsEngine


class DerivativeNode(QGraphicsItem):
    """Nœud 'Dérivateur (dy/dt)' (Catégorie Maths - Vert #4CAF50)."""
    def __init__(self, name="Dérivateur 1", x=0, y=0):
        super().__init__()
        self.node_type = "derivative"
        self.width = 175
        self.height = 90
        self.setPos(x, y)
        self.setFlags(
            QGraphicsItem.ItemIsMovable |
            QGraphicsItem.ItemIsSelectable |
            QGraphicsItem.ItemSendsGeometryChanges
        )
        self.connections = []
        self.input_node = None

        self.params = {"name": name}
        self.is_dirty = True
        self.t_data = None
        self.y_data = None

    def mark_dirty(self):
        self.is_dirty = True
        self.update()

    def recalculate(self):
        if self.input_node and self.input_node.t_data is not None and self.input_node.y_data is not None:
            self.t_data = self.input_node.t_data
            self.y_data = MathOperatorsEngine.compute_derivative(self.t_data, self.input_node.y_data)
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
        border_color = QColor("#FF9800") if self.is_dirty else QColor("#4CAF50")
        if self.isSelected():
            border_color = QColor("#FFFFFF")

        painter.setBrush(QBrush(QColor("#2B2E3A")))
        painter.setPen(QPen(border_color, 2 if self.isSelected() or self.is_dirty else 1))
        painter.drawRoundedRect(0, 0, self.width, self.height, 8, 8)

        header_color = QColor("#E65100") if self.is_dirty else QColor("#4CAF50")
        painter.setBrush(QBrush(header_color))
        painter.drawRoundedRect(0, 0, self.width, 24, 8, 8)
        painter.fillRect(0, 14, self.width, 10, header_color)
        
        painter.setPen(QPen(Qt.white))
        status_badge = "⚠️" if self.is_dirty else "✓"
        painter.drawText(QRectF(8, 3, self.width - 16, 18), Qt.AlignLeft | Qt.AlignVCenter, f"{status_badge} Dérivateur (dy/dt)")

        painter.setPen(QPen(QColor("#EEEEEE")))
        painter.drawText(QRectF(10, 32, self.width - 20, 20), Qt.AlignLeft, self.params["name"])

        src_info = self.input_node.params['name'] if self.input_node else "Aucune"
        painter.setPen(QPen(QColor("#B0BEC5")))
        painter.drawText(QRectF(10, 58, self.width - 20, 18), Qt.AlignLeft, f"In: {src_info}")

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


class IntegratorNode(QGraphicsItem):
    """Nœud 'Intégrateur (∫y dt)' (Catégorie Maths - Vert #4CAF50)."""
    def __init__(self, name="Intégrateur 1", x=0, y=0):
        super().__init__()
        self.node_type = "integrator"
        self.width = 175
        self.height = 90
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
            "initial_val": 0.0
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
            self.y_data = MathOperatorsEngine.compute_integrator(
                self.t_data, self.input_node.y_data, initial_val=self.params.get("initial_val", 0.0)
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
        border_color = QColor("#FF9800") if self.is_dirty else QColor("#4CAF50")
        if self.isSelected():
            border_color = QColor("#FFFFFF")

        painter.setBrush(QBrush(QColor("#2B2E3A")))
        painter.setPen(QPen(border_color, 2 if self.isSelected() or self.is_dirty else 1))
        painter.drawRoundedRect(0, 0, self.width, self.height, 8, 8)

        header_color = QColor("#E65100") if self.is_dirty else QColor("#4CAF50")
        painter.setBrush(QBrush(header_color))
        painter.drawRoundedRect(0, 0, self.width, 24, 8, 8)
        painter.fillRect(0, 14, self.width, 10, header_color)
        
        painter.setPen(QPen(Qt.white))
        status_badge = "⚠️" if self.is_dirty else "✓"
        painter.drawText(QRectF(8, 3, self.width - 16, 18), Qt.AlignLeft | Qt.AlignVCenter, f"{status_badge} Intégrateur (∫y dt)")

        painter.setPen(QPen(QColor("#EEEEEE")))
        painter.drawText(QRectF(10, 32, self.width - 20, 20), Qt.AlignLeft, self.params["name"])

        src_info = self.input_node.params['name'] if self.input_node else "Aucune"
        painter.setPen(QPen(QColor("#B0BEC5")))
        painter.drawText(QRectF(10, 58, self.width - 20, 18), Qt.AlignLeft, f"y(0): {self.params.get('initial_val', 0.0)} | In: {src_info}")

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


class GainNode(QGraphicsItem):
    """Nœud 'Gain & Offset' (Catégorie Maths - Vert #4CAF50)."""
    def __init__(self, name="Gain 1", x=0, y=0):
        super().__init__()
        self.node_type = "gain"
        self.width = 175
        self.height = 90
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
            "gain": 1.0,
            "offset": 0.0
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
            self.y_data = MathOperatorsEngine.compute_gain(
                self.input_node.y_data, gain=self.params.get("gain", 1.0), offset=self.params.get("offset", 0.0)
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
        border_color = QColor("#FF9800") if self.is_dirty else QColor("#4CAF50")
        if self.isSelected():
            border_color = QColor("#FFFFFF")

        painter.setBrush(QBrush(QColor("#2B2E3A")))
        painter.setPen(QPen(border_color, 2 if self.isSelected() or self.is_dirty else 1))
        painter.drawRoundedRect(0, 0, self.width, self.height, 8, 8)

        header_color = QColor("#E65100") if self.is_dirty else QColor("#4CAF50")
        painter.setBrush(QBrush(header_color))
        painter.drawRoundedRect(0, 0, self.width, 24, 8, 8)
        painter.fillRect(0, 14, self.width, 10, header_color)
        
        painter.setPen(QPen(Qt.white))
        status_badge = "⚠️" if self.is_dirty else "✓"
        painter.drawText(QRectF(8, 3, self.width - 16, 18), Qt.AlignLeft | Qt.AlignVCenter, f"{status_badge} Gain & Offset")

        painter.setPen(QPen(QColor("#EEEEEE")))
        painter.drawText(QRectF(10, 32, self.width - 20, 20), Qt.AlignLeft, self.params["name"])

        src_info = self.input_node.params['name'] if self.input_node else "Aucune"
        painter.setPen(QPen(QColor("#B0BEC5")))
        painter.drawText(QRectF(10, 58, self.width - 20, 18), Qt.AlignLeft, f"k: {self.params.get('gain', 1.0)} | Off: {self.params.get('offset', 0.0)}V")

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


class InversionNode(QGraphicsItem):
    """Nœud 'Inversion (1/x)' (Catégorie Maths - Vert #4CAF50)."""
    def __init__(self, name="Inversion 1", x=0, y=0):
        super().__init__()
        self.node_type = "inversion"
        self.width = 175
        self.height = 90
        self.setPos(x, y)
        self.setFlags(
            QGraphicsItem.ItemIsMovable |
            QGraphicsItem.ItemIsSelectable |
            QGraphicsItem.ItemSendsGeometryChanges
        )
        self.connections = []
        self.input_node = None
        self.params = {"name": name}
        self.is_dirty = True
        self.t_data = None
        self.y_data = None

    def mark_dirty(self):
        self.is_dirty = True
        self.update()

    def recalculate(self):
        if self.input_node and self.input_node.t_data is not None and self.input_node.y_data is not None:
            self.t_data = self.input_node.t_data
            self.y_data = MathOperatorsEngine.compute_inversion(self.input_node.y_data)
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
        border_color = QColor("#FF9800") if self.is_dirty else QColor("#4CAF50")
        if self.isSelected():
            border_color = QColor("#FFFFFF")

        painter.setBrush(QBrush(QColor("#2B2E3A")))
        painter.setPen(QPen(border_color, 2 if self.isSelected() or self.is_dirty else 1))
        painter.drawRoundedRect(0, 0, self.width, self.height, 8, 8)

        header_color = QColor("#E65100") if self.is_dirty else QColor("#4CAF50")
        painter.setBrush(QBrush(header_color))
        painter.drawRoundedRect(0, 0, self.width, 24, 8, 8)
        painter.fillRect(0, 14, self.width, 10, header_color)
        
        painter.setPen(QPen(Qt.white))
        status_badge = "⚠️" if self.is_dirty else "✓"
        painter.drawText(QRectF(8, 3, self.width - 16, 18), Qt.AlignLeft | Qt.AlignVCenter, f"{status_badge} Inversion (1/x)")

        painter.setPen(QPen(QColor("#EEEEEE")))
        painter.drawText(QRectF(10, 32, self.width - 20, 20), Qt.AlignLeft, self.params["name"])

        src_info = self.input_node.params['name'] if self.input_node else "Aucune"
        painter.setPen(QPen(QColor("#B0BEC5")))
        painter.drawText(QRectF(10, 58, self.width - 20, 18), Qt.AlignLeft, f"In: {src_info}")

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


class AbsNode(QGraphicsItem):
    """Nœud 'Valeur Absolue (|x|)' (Catégorie Maths - Vert #4CAF50)."""
    def __init__(self, name="Absolue 1", x=0, y=0):
        super().__init__()
        self.node_type = "abs_val"
        self.width = 175
        self.height = 90
        self.setPos(x, y)
        self.setFlags(
            QGraphicsItem.ItemIsMovable |
            QGraphicsItem.ItemIsSelectable |
            QGraphicsItem.ItemSendsGeometryChanges
        )
        self.connections = []
        self.input_node = None
        self.params = {"name": name}
        self.is_dirty = True
        self.t_data = None
        self.y_data = None

    def mark_dirty(self):
        self.is_dirty = True
        self.update()

    def recalculate(self):
        if self.input_node and self.input_node.t_data is not None and self.input_node.y_data is not None:
            self.t_data = self.input_node.t_data
            self.y_data = MathOperatorsEngine.compute_abs(self.input_node.y_data)
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
        border_color = QColor("#FF9800") if self.is_dirty else QColor("#4CAF50")
        if self.isSelected():
            border_color = QColor("#FFFFFF")

        painter.setBrush(QBrush(QColor("#2B2E3A")))
        painter.setPen(QPen(border_color, 2 if self.isSelected() or self.is_dirty else 1))
        painter.drawRoundedRect(0, 0, self.width, self.height, 8, 8)

        header_color = QColor("#E65100") if self.is_dirty else QColor("#4CAF50")
        painter.setBrush(QBrush(header_color))
        painter.drawRoundedRect(0, 0, self.width, 24, 8, 8)
        painter.fillRect(0, 14, self.width, 10, header_color)
        
        painter.setPen(QPen(Qt.white))
        status_badge = "⚠️" if self.is_dirty else "✓"
        painter.drawText(QRectF(8, 3, self.width - 16, 18), Qt.AlignLeft | Qt.AlignVCenter, f"{status_badge} Valeur Absolue (|x|)")

        painter.setPen(QPen(QColor("#EEEEEE")))
        painter.drawText(QRectF(10, 32, self.width - 20, 20), Qt.AlignLeft, self.params["name"])

        src_info = self.input_node.params['name'] if self.input_node else "Aucune"
        painter.setPen(QPen(QColor("#B0BEC5")))
        painter.drawText(QRectF(10, 58, self.width - 20, 18), Qt.AlignLeft, f"In: {src_info}")

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


class LogNode(QGraphicsItem):
    """Nœud 'Logarithme (log / ln)' (Catégorie Maths - Vert #4CAF50)."""
    def __init__(self, name="Logarithme 1", x=0, y=0):
        super().__init__()
        self.node_type = "log_func"
        self.width = 175
        self.height = 90
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
            "base": "log10 (base 10)"
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
            self.y_data = MathOperatorsEngine.compute_log(self.input_node.y_data, base=self.params.get("base", "log10 (base 10)"))
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
        border_color = QColor("#FF9800") if self.is_dirty else QColor("#4CAF50")
        if self.isSelected():
            border_color = QColor("#FFFFFF")

        painter.setBrush(QBrush(QColor("#2B2E3A")))
        painter.setPen(QPen(border_color, 2 if self.isSelected() or self.is_dirty else 1))
        painter.drawRoundedRect(0, 0, self.width, self.height, 8, 8)

        header_color = QColor("#E65100") if self.is_dirty else QColor("#4CAF50")
        painter.setBrush(QBrush(header_color))
        painter.drawRoundedRect(0, 0, self.width, 24, 8, 8)
        painter.fillRect(0, 14, self.width, 10, header_color)
        
        painter.setPen(QPen(Qt.white))
        status_badge = "⚠️" if self.is_dirty else "✓"
        painter.drawText(QRectF(8, 3, self.width - 16, 18), Qt.AlignLeft | Qt.AlignVCenter, f"{status_badge} Logarithme")

        painter.setPen(QPen(QColor("#EEEEEE")))
        painter.drawText(QRectF(10, 32, self.width - 20, 20), Qt.AlignLeft, self.params["name"])

        src_info = self.input_node.params['name'] if self.input_node else "Aucune"
        painter.setPen(QPen(QColor("#B0BEC5")))
        painter.drawText(QRectF(10, 58, self.width - 20, 18), Qt.AlignLeft, f"Base: {self.params.get('base', 'log10')[:5]} | In: {src_info}")

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


class ExpNode(QGraphicsItem):
    """Nœud 'Exponentielle (exp)' (Catégorie Maths - Vert #4CAF50)."""
    def __init__(self, name="Exponentielle 1", x=0, y=0):
        super().__init__()
        self.node_type = "exp_func"
        self.width = 175
        self.height = 90
        self.setPos(x, y)
        self.setFlags(
            QGraphicsItem.ItemIsMovable |
            QGraphicsItem.ItemIsSelectable |
            QGraphicsItem.ItemSendsGeometryChanges
        )
        self.connections = []
        self.input_node = None
        self.params = {"name": name}
        self.is_dirty = True
        self.t_data = None
        self.y_data = None

    def mark_dirty(self):
        self.is_dirty = True
        self.update()

    def recalculate(self):
        if self.input_node and self.input_node.t_data is not None and self.input_node.y_data is not None:
            self.t_data = self.input_node.t_data
            self.y_data = MathOperatorsEngine.compute_exp(self.input_node.y_data)
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
        border_color = QColor("#FF9800") if self.is_dirty else QColor("#4CAF50")
        if self.isSelected():
            border_color = QColor("#FFFFFF")

        painter.setBrush(QBrush(QColor("#2B2E3A")))
        painter.setPen(QPen(border_color, 2 if self.isSelected() or self.is_dirty else 1))
        painter.drawRoundedRect(0, 0, self.width, self.height, 8, 8)

        header_color = QColor("#E65100") if self.is_dirty else QColor("#4CAF50")
        painter.setBrush(QBrush(header_color))
        painter.drawRoundedRect(0, 0, self.width, 24, 8, 8)
        painter.fillRect(0, 14, self.width, 10, header_color)
        
        painter.setPen(QPen(Qt.white))
        status_badge = "⚠️" if self.is_dirty else "✓"
        painter.drawText(QRectF(8, 3, self.width - 16, 18), Qt.AlignLeft | Qt.AlignVCenter, f"{status_badge} Exponentielle (exp)")

        painter.setPen(QPen(QColor("#EEEEEE")))
        painter.drawText(QRectF(10, 32, self.width - 20, 20), Qt.AlignLeft, self.params["name"])

        src_info = self.input_node.params['name'] if self.input_node else "Aucune"
        painter.setPen(QPen(QColor("#B0BEC5")))
        painter.drawText(QRectF(10, 58, self.width - 20, 18), Qt.AlignLeft, f"In: {src_info}")

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


class PowerNode(QGraphicsItem):
    """Nœud 'Puissance / Racine (xⁿ, √x)' (Catégorie Maths - Vert #4CAF50)."""
    def __init__(self, name="Puissance 1", x=0, y=0):
        super().__init__()
        self.node_type = "power_func"
        self.width = 175
        self.height = 90
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
            "mode": "Puissance xⁿ",
            "exponent": 2.0
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
            self.y_data = MathOperatorsEngine.compute_power(
                self.input_node.y_data,
                mode=self.params.get("mode", "Puissance xⁿ"),
                exponent=self.params.get("exponent", 2.0)
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
        border_color = QColor("#FF9800") if self.is_dirty else QColor("#4CAF50")
        if self.isSelected():
            border_color = QColor("#FFFFFF")

        painter.setBrush(QBrush(QColor("#2B2E3A")))
        painter.setPen(QPen(border_color, 2 if self.isSelected() or self.is_dirty else 1))
        painter.drawRoundedRect(0, 0, self.width, self.height, 8, 8)

        header_color = QColor("#E65100") if self.is_dirty else QColor("#4CAF50")
        painter.setBrush(QBrush(header_color))
        painter.drawRoundedRect(0, 0, self.width, 24, 8, 8)
        painter.fillRect(0, 14, self.width, 10, header_color)
        
        painter.setPen(QPen(Qt.white))
        status_badge = "⚠️" if self.is_dirty else "✓"
        title_label = "√x (Racine)" if "Racine" in self.params.get("mode", "") else f"xⁿ (n={self.params.get('exponent', 2.0)})"
        painter.drawText(QRectF(8, 3, self.width - 16, 18), Qt.AlignLeft | Qt.AlignVCenter, f"{status_badge} {title_label}")

        painter.setPen(QPen(QColor("#EEEEEE")))
        painter.drawText(QRectF(10, 32, self.width - 20, 20), Qt.AlignLeft, self.params["name"])

        src_info = self.input_node.params['name'] if self.input_node else "Aucune"
        painter.setPen(QPen(QColor("#B0BEC5")))
        painter.drawText(QRectF(10, 58, self.width - 20, 18), Qt.AlignLeft, f"In: {src_info}")

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


class AdditionNode(QGraphicsItem):
    """Nœud 'Addition (A + B)' multivariable à 2 entrées (Catégorie Maths - Vert #4CAF50)."""
    def __init__(self, name="Addition 1", x=0, y=0):
        super().__init__()
        self.node_type = "addition"
        self.width = 185
        self.height = 100
        self.setPos(x, y)
        self.setFlags(
            QGraphicsItem.ItemIsMovable |
            QGraphicsItem.ItemIsSelectable |
            QGraphicsItem.ItemSendsGeometryChanges
        )
        self.connections = []
        self.input_node_a = None
        self.input_node_b = None

        self.params = {
            "name": name,
            "coef_a": 1.0,
            "coef_b": 1.0
        }
        self.is_dirty = True
        self.t_data = None
        self.y_data = None

    @property
    def input_node(self):
        return self.input_node_a

    @input_node.setter
    def input_node(self, node):
        self.input_node_a = node

    def mark_dirty(self):
        self.is_dirty = True
        self.update()

    def recalculate(self):
        t_a = self.input_node_a.t_data if self.input_node_a else None
        y_a = self.input_node_a.y_data if self.input_node_a else None
        t_b = self.input_node_b.t_data if self.input_node_b else None
        y_b = self.input_node_b.y_data if self.input_node_b else None

        self.t_data, self.y_data = MathOperatorsEngine.compute_addition(
            t_a, y_a, t_b, y_b,
            coef_a=float(self.params.get("coef_a", 1.0)),
            coef_b=float(self.params.get("coef_b", 1.0))
        )
        self.is_dirty = False
        self.update()

    def boundingRect(self):
        margin = 12
        return QRectF(-margin, -margin, self.width + 2 * margin, self.height + 2 * margin)

    def paint(self, painter, option, widget=None):
        painter.setRenderHint(QPainter.Antialiasing, True)
        border_color = QColor("#FF9800") if self.is_dirty else QColor("#4CAF50")
        if self.isSelected():
            border_color = QColor("#FFFFFF")

        painter.setBrush(QBrush(QColor("#2B2E3A")))
        painter.setPen(QPen(border_color, 2 if self.isSelected() or self.is_dirty else 1))
        painter.drawRoundedRect(0, 0, self.width, self.height, 8, 8)

        header_color = QColor("#E65100") if self.is_dirty else QColor("#4CAF50")
        painter.setBrush(QBrush(header_color))
        painter.drawRoundedRect(0, 0, self.width, 24, 8, 8)
        painter.fillRect(0, 14, self.width, 10, header_color)
        
        painter.setPen(QPen(Qt.white))
        status_badge = "⚠️" if self.is_dirty else "✓"
        painter.drawText(QRectF(8, 3, self.width - 16, 18), Qt.AlignLeft | Qt.AlignVCenter, f"{status_badge} Addition (A + B)")

        painter.setPen(QPen(QColor("#EEEEEE")))
        painter.drawText(QRectF(10, 32, self.width - 20, 20), Qt.AlignLeft, self.params["name"])

        src_a = self.input_node_a.params['name'] if self.input_node_a else "Aucune"
        src_b = self.input_node_b.params['name'] if self.input_node_b else "Aucune"
        painter.setPen(QPen(QColor("#B0BEC5")))
        painter.drawText(QRectF(10, 56, self.width - 20, 18), Qt.AlignLeft, f"A: {src_a}")
        painter.drawText(QRectF(10, 74, self.width - 20, 18), Qt.AlignLeft, f"B: {src_b}")

        # Ports d'entrée A et B
        painter.setBrush(QBrush(QColor("#00ADB5")))
        painter.setPen(QPen(QColor("#FFFFFF"), 1.5))
        painter.drawEllipse(-6, int(self.height * 0.35) - 6, 12, 12)
        painter.drawEllipse(-6, int(self.height * 0.65) - 6, 12, 12)

        # Port de sortie
        painter.setBrush(QBrush(QColor("#FF5722")))
        painter.setPen(QPen(QColor("#FFFFFF"), 1.5))
        painter.drawEllipse(self.width - 6, self.height // 2 - 6, 12, 12)

    def itemChange(self, change, value):
        if change in (QGraphicsItem.ItemPositionHasChanged, QGraphicsItem.ItemPositionChange):
            for conn in self.connections:
                conn.update_path()
        return super().itemChange(change, value)
