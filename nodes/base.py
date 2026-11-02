from PySide6.QtCore import Qt, QPointF
from PySide6.QtGui import QColor, QPen, QPainter, QPainterPath, QPainterPathStroker
from PySide6.QtWidgets import QGraphicsPathItem


class NodeConnectionItem(QGraphicsPathItem):
    """Lien graphique réactif et sélectionnable entre deux nœuds."""
    def __init__(self, start_item, end_item, target_port="a"):
        super().__init__()
        self.start_item = start_item
        self.end_item = end_item
        self.target_port = target_port
        self.setFlags(QGraphicsPathItem.ItemIsSelectable)
        self.setPen(QPen(QColor("#00ADB5"), 3, Qt.DashLine))
        self.setZValue(-1)
        self.update_path()

    def shape(self):
        """Agrandit la zone de clic pour faciliter la sélection du lien."""
        path = super().shape()
        stroker = QPainterPathStroker()
        stroker.setWidth(14)
        return stroker.createStroke(path)

    def paint(self, painter, option, widget=None):
        painter.setRenderHint(QPainter.Antialiasing, True)
        if self.isSelected():
            self.setPen(QPen(QColor("#FF5722"), 4, Qt.SolidLine))
        else:
            self.setPen(QPen(QColor("#00ADB5"), 3, Qt.DashLine))
        super().paint(painter, option, widget)

    def update_path(self):
        if not self.start_item or not self.end_item:
            return
        self.prepareGeometryChange()
        p1 = self.start_item.scenePos() + QPointF(self.start_item.width, self.start_item.height / 2)
        
        target_port = getattr(self, "target_port", "a")
        if hasattr(self.end_item, "input_node_b") and (target_port == "b" or (getattr(self.end_item, "input_node_b", None) == self.start_item and getattr(self.end_item, "input_node_a", None) != self.start_item)):
            p2 = self.end_item.scenePos() + QPointF(0, self.end_item.height * 0.65)
        elif hasattr(self.end_item, "input_node_a"):
            p2 = self.end_item.scenePos() + QPointF(0, self.end_item.height * 0.35)
        else:
            p2 = self.end_item.scenePos() + QPointF(0, self.end_item.height / 2)

        path = QPainterPath(p1)
        dx = max(abs(p2.x() - p1.x()) * 0.5, 30)
        path.cubicTo(p1.x() + dx, p1.y(), p2.x() - dx, p2.y(), p2.x(), p2.y())
        self.setPath(path)
