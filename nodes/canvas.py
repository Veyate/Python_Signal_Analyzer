# nodes/canvas.py
from PySide6.QtCore import Qt, QPointF
from PySide6.QtGui import QColor, QPen, QPainter, QPainterPath
from PySide6.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsPathItem, QMenu
from i18n import i18n
from nodes.base import NodeConnectionItem
from nodes.sources import SignalGeneratorNode, CSVImportNode
from nodes.filters import (
    LowPassFilterNode, HighPassFilterNode, BandPassFilterNode, BandStopFilterNode
)
from nodes.maths import (
    DerivativeNode, IntegratorNode, GainNode, InversionNode, AbsNode, LogNode, ExpNode, PowerNode, AdditionNode
)
from nodes.noise import NoiseNode
from nodes.sampling import ResampleNode, InterpolationNode, DACNode
from nodes.dsp_filters import FixedAverageNode, MovingAverageNode, MedianFilterNode
from nodes.do160 import DO160DoubleExpNode, DO160DampedSineNode
from nodes.analysis import FFTAnalysisNode, THDAnalysisNode

ALL_NODE_TYPES = (
    SignalGeneratorNode, CSVImportNode,
    DO160DoubleExpNode, DO160DampedSineNode,
    LowPassFilterNode, HighPassFilterNode, BandPassFilterNode, BandStopFilterNode,
    DerivativeNode, IntegratorNode, GainNode, InversionNode, AbsNode, LogNode, ExpNode, PowerNode, AdditionNode,
    NoiseNode, ResampleNode, InterpolationNode, DACNode,
    FixedAverageNode, MovingAverageNode, MedianFilterNode,
    AdditionNode,
    FFTAnalysisNode, THDAnalysisNode
)

PROCESSOR_NODE_TYPES = (
    LowPassFilterNode, HighPassFilterNode, BandPassFilterNode, BandStopFilterNode,
    DerivativeNode, IntegratorNode, GainNode, InversionNode, AbsNode, LogNode, ExpNode, PowerNode, AdditionNode,
    NoiseNode, ResampleNode, InterpolationNode, DACNode,
    FixedAverageNode, MovingAverageNode, MedianFilterNode,
    AdditionNode,
    FFTAnalysisNode, THDAnalysisNode
)


class NodeEditorCanvas(QGraphicsView):
    """Canevas interactif d'édition de nœuds."""
    def __init__(self, selection_callback=None, double_click_callback=None,
                 view_graph_cb=None, view_table_cb=None, export_csv_cb=None,
                 connect_cb=None, delete_node_cb=None):
        super().__init__()
        self.selection_callback = selection_callback
        self.double_click_callback = double_click_callback
        self.view_graph_cb = view_graph_cb
        self.view_table_cb = view_table_cb
        self.export_csv_cb = export_csv_cb
        self.connect_cb = connect_cb
        self.delete_node_cb = delete_node_cb

        self.scene = QGraphicsScene(-1000, -1000, 2000, 2000)
        self.setScene(self.scene)
        self.setRenderHint(QPainter.Antialiasing)
        self.setBackgroundBrush(QColor("#1A1C23"))

        # Mode de sélection par cadre (RubberBand) pour déplacer plusieurs nœuds
        self.setDragMode(QGraphicsView.RubberBandDrag)
        self.setRubberBandSelectionMode(Qt.IntersectsItemShape)

        # Variables pour la création interactive de liens
        self.dragging_wire = False
        self.wire_source_node = None
        self.temp_wire_path = None

        self.scene.selectionChanged.connect(self.on_selection_changed)

    # --- Ajout de Nœuds par type ---
    def add_generator_node(self, name="Générateur 1", x=-850, y=-50) -> SignalGeneratorNode:
        node = SignalGeneratorNode(name, x, y)
        self.scene.addItem(node)
        return node

    def add_csv_node(self, name="Import CSV 1", x=-850, y=80) -> CSVImportNode:
        node = CSVImportNode(name, x, y)
        self.scene.addItem(node)
        return node

    def add_do160_double_exp_node(self, name="Impulsion DO-160 1", x=-850, y=200) -> DO160DoubleExpNode:
        node = DO160DoubleExpNode(name, x, y)
        self.scene.addItem(node)
        return node

    def add_do160_damped_sine_node(self, name="Sinus Amorti WF3 1", x=-850, y=320) -> DO160DampedSineNode:
        node = DO160DampedSineNode(name, x, y)
        self.scene.addItem(node)
        return node

    def add_lowpass_node(self, name="Filtre Passe-Bas 1", x=-580, y=-50) -> LowPassFilterNode:
        node = LowPassFilterNode(name, x, y)
        self.scene.addItem(node)
        return node

    def add_highpass_node(self, name="Filtre Passe-Haut 1", x=-580, y=10) -> HighPassFilterNode:
        node = HighPassFilterNode(name, x, y)
        self.scene.addItem(node)
        return node

    def add_bandpass_node(self, name="Filtre Passe-Bande 1", x=-580, y=70) -> BandPassFilterNode:
        node = BandPassFilterNode(name, x, y)
        self.scene.addItem(node)
        return node

    def add_bandstop_node(self, name="Filtre Coupe-Bande 1", x=-580, y=130) -> BandStopFilterNode:
        node = BandStopFilterNode(name, x, y)
        self.scene.addItem(node)
        return node

    def add_filter_node(self, name="Filtre 1", x=120, y=-40, filter_kind="lowpass"):
        if filter_kind == "highpass":
            return self.add_highpass_node(name, x, y)
        elif filter_kind == "bandpass":
            return self.add_bandpass_node(name, x, y)
        elif filter_kind == "bandstop":
            return self.add_bandstop_node(name, x, y)
        else:
            return self.add_lowpass_node(name, x, y)

    def add_derivative_node(self, name="Dérivateur 1", x=-580, y=190) -> DerivativeNode:
        node = DerivativeNode(name, x, y)
        self.scene.addItem(node)
        return node

    def add_integrator_node(self, name="Intégrateur 1", x=-580, y=250) -> IntegratorNode:
        node = IntegratorNode(name, x, y)
        self.scene.addItem(node)
        return node

    def add_gain_node(self, name="Gain 1", x=-580, y=310) -> GainNode:
        node = GainNode(name, x, y)
        self.scene.addItem(node)
        return node

    def add_inversion_node(self, name="Inversion 1", x=-580, y=370) -> InversionNode:
        node = InversionNode(name, x, y)
        self.scene.addItem(node)
        return node

    def add_abs_node(self, name="Absolue 1", x=-580, y=430) -> AbsNode:
        node = AbsNode(name, x, y)
        self.scene.addItem(node)
        return node

    def add_log_node(self, name="Logarithme 1", x=-580, y=490) -> LogNode:
        node = LogNode(name, x, y)
        self.scene.addItem(node)
        return node

    def add_exp_node(self, name="Exponentielle 1", x=-580, y=550) -> ExpNode:
        node = ExpNode(name, x, y)
        self.scene.addItem(node)
        return node

    def add_power_node(self, name="Puissance 1", x=-580, y=610) -> PowerNode:
        node = PowerNode(name, x, y)
        self.scene.addItem(node)
        return node

    def add_addition_node(self, name="Addition 1", x=-580, y=670) -> AdditionNode:
        node = AdditionNode(name, x, y)
        self.scene.addItem(node)
        return node

    def add_noise_node(self, name="Injecteur de Bruit 1", x=-580, y=730) -> NoiseNode:
        node = NoiseNode(name, x, y)
        self.scene.addItem(node)
        return node

    def add_resample_node(self, name="Rééchantillonnage 1", x=-580, y=790) -> ResampleNode:
        node = ResampleNode(name, x, y)
        self.scene.addItem(node)
        return node

    def add_interpolation_node(self, name="Interpolation 1", x=-580, y=850) -> InterpolationNode:
        node = InterpolationNode(name, x, y)
        self.scene.addItem(node)
        return node

    def add_dac_node(self, name="Simulation DAC 1", x=-580, y=910) -> DACNode:
        node = DACNode(name, x, y)
        self.scene.addItem(node)
        return node

    def add_fixed_average_node(self, name="Moyenne Fixe 1", x=-580, y=970) -> FixedAverageNode:
        node = FixedAverageNode(name, x, y)
        self.scene.addItem(node)
        return node

    def add_moving_average_node(self, name="Moyenne Glissante 1", x=-580, y=1030) -> MovingAverageNode:
        node = MovingAverageNode(name, x, y)
        self.scene.addItem(node)
        return node

    def add_median_filter_node(self, name="Filtre Médian 1", x=-580, y=1090) -> MedianFilterNode:
        node = MedianFilterNode(name, x, y)
        self.scene.addItem(node)
        return node

    
    def add_thd_node(self, name="Analyse THD 1", x=-310, y=-50) -> THDAnalysisNode:
        node = THDAnalysisNode(name, x, y)
        self.scene.addItem(node)
        return node

    def add_fft_node(self, name="Analyse FFT 1", x=-310, y=100) -> FFTAnalysisNode:
        node = FFTAnalysisNode(name, x, y)
        self.scene.addItem(node)
        return node

    def create_connection(self, source_node, target_node, target_port="a") -> NodeConnectionItem:
        """Connecte la sortie d'un nœud source à l'entrée (A ou B) d'un nœud cible."""
        if not source_node or not target_node or source_node == target_node:
            return None

        if hasattr(target_node, "input_node_b") and target_port == "b":
            self.remove_connection_for_target(target_node, target_port="b")
            target_node.input_node_b = source_node
        elif hasattr(target_node, "input_node_a"):
            self.remove_connection_for_target(target_node, target_port="a")
            target_node.input_node_a = source_node
            target_node.input_node = source_node
        elif hasattr(target_node, "input_node"):
            self.remove_connection_for_target(target_node, target_port="a")
            target_node.input_node = source_node

        conn = NodeConnectionItem(source_node, target_node, target_port=target_port)
        source_node.connections.append(conn)
        target_node.connections.append(conn)
        self.scene.addItem(conn)
        
        target_node.mark_dirty()
        return conn

    def remove_connection_for_target(self, target_node, target_port="a"):
        to_remove = []
        for conn in getattr(target_node, "connections", []):
            if conn.end_item == target_node and getattr(conn, "target_port", "a") == target_port:
                to_remove.append(conn)

        for conn in to_remove:
            self.delete_connection(conn)

        if target_port == "b" and hasattr(target_node, "input_node_b"):
            target_node.input_node_b = None
        elif hasattr(target_node, "input_node_a"):
            target_node.input_node_a = None
            target_node.input_node = None
        elif hasattr(target_node, "input_node"):
            target_node.input_node = None

        target_node.mark_dirty()

    def delete_connection(self, conn: NodeConnectionItem):
        """Supprime proprement un câble entre deux nœuds."""
        if not conn:
            return
        if conn.start_item and conn in conn.start_item.connections:
            conn.start_item.connections.remove(conn)
        if conn.end_item and conn in conn.end_item.connections:
            conn.end_item.connections.remove(conn)
            port = getattr(conn, "target_port", "a")
            if port == "b" and hasattr(conn.end_item, "input_node_b") and conn.end_item.input_node_b == conn.start_item:
                conn.end_item.input_node_b = None
                conn.end_item.mark_dirty()
            elif hasattr(conn.end_item, "input_node_a") and conn.end_item.input_node_a == conn.start_item:
                conn.end_item.input_node_a = None
                conn.end_item.input_node = None
                conn.end_item.mark_dirty()
            elif hasattr(conn.end_item, "input_node") and conn.end_item.input_node == conn.start_item:
                conn.end_item.input_node = None
                conn.end_item.mark_dirty()
        
        if conn.scene() == self.scene:
            self.scene.removeItem(conn)

    # --- Événements Souris pour le Traçage Interactif de Liens ---
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            scene_pos = self.mapToScene(event.position().toPoint())
            
            # Clic sur port de sortie
            for item in self.scene.items(scene_pos):
                if isinstance(item, ALL_NODE_TYPES):
                    out_socket_pos = item.scenePos() + QPointF(item.width, item.height / 2)
                    if (scene_pos - out_socket_pos).manhattanLength() < 16:
                        self.dragging_wire = True
                        self.wire_source_node = item
                        self.temp_wire_path = QGraphicsPathItem()
                        self.temp_wire_path.setPen(QPen(QColor("#FF5722"), 2.5, Qt.DashLine))
                        self.scene.addItem(self.temp_wire_path)
                        self.update_temp_wire(scene_pos)
                        return

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.dragging_wire and self.wire_source_node:
            scene_pos = self.mapToScene(event.position().toPoint())
            self.update_temp_wire(scene_pos)
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self.dragging_wire and self.wire_source_node:
            scene_pos = self.mapToScene(event.position().toPoint())
            target_node = None
            
            for item in self.scene.items(scene_pos):
                if isinstance(item, PROCESSOR_NODE_TYPES) and item != self.wire_source_node:
                    target_node = item
                    break

            if target_node:
                target_port = "a"
                if hasattr(target_node, "input_node_b"):
                    node_top_y = target_node.scenePos().y()
                    mid_y = node_top_y + target_node.height * 0.5
                    if scene_pos.y() >= mid_y:
                        target_port = "b"

                self.create_connection(self.wire_source_node, target_node, target_port=target_port)
                if self.connect_cb:
                    self.connect_cb(self.wire_source_node, target_node)

            if self.temp_wire_path:
                self.scene.removeItem(self.temp_wire_path)
                self.temp_wire_path = None
            self.dragging_wire = False
            self.wire_source_node = None
            return

        super().mouseReleaseEvent(event)

    def update_temp_wire(self, target_pos):
        if not self.wire_source_node or not self.temp_wire_path:
            return
        p1 = self.wire_source_node.scenePos() + QPointF(self.wire_source_node.width, self.wire_source_node.height / 2)
        p2 = target_pos
        path = QPainterPath(p1)
        dx = max(abs(p2.x() - p1.x()) * 0.5, 30)
        path.cubicTo(p1.x() + dx, p1.y(), p2.x() - dx, p2.y(), p2.x(), p2.y())
        self.temp_wire_path.setPath(path)

    def mouseDoubleClickEvent(self, event):
        item = self.itemAt(event.position().toPoint())
        if isinstance(item, ALL_NODE_TYPES) and self.double_click_callback:
            self.double_click_callback(item)
        super().mouseDoubleClickEvent(event)

    def keyPressEvent(self, event):
        """Touche Suppr / Retour arrière pour supprimer les éléments sélectionnés."""
        if event.key() in (Qt.Key_Delete, Qt.Key_Backspace):
            selected_items = list(self.scene.selectedItems())
            for item in selected_items:
                if isinstance(item, NodeConnectionItem):
                    self.delete_connection(item)
                    if self.connect_cb:
                        self.connect_cb(None, None)
                elif isinstance(item, ALL_NODE_TYPES):
                    if self.delete_node_cb:
                        self.delete_node_cb(item)
            return
        super().keyPressEvent(event)

    def contextMenuEvent(self, event):
        item = self.itemAt(event.pos())
        
        # Menu sur un Nœud
        if isinstance(item, ALL_NODE_TYPES):
            menu = QMenu(self)
            act_graph = menu.addAction(i18n.tr("view_graph"))
            act_table = menu.addAction(i18n.tr("view_table"))
            act_export = menu.addAction(i18n.tr("export_csv_action"))
            menu.addSeparator()
            act_params = menu.addAction(i18n.tr("edit_params"))
            
            if isinstance(item, PROCESSOR_NODE_TYPES) and item.input_node:
                menu.addSeparator()
                act_disconn = menu.addAction(i18n.tr("disconnect"))
            else:
                act_disconn = None

            menu.addSeparator()
            act_del = menu.addAction(i18n.tr("delete_node"))

            action = menu.exec(event.globalPos())
            if action == act_graph and self.view_graph_cb:
                self.view_graph_cb(item)
            elif action == act_table and self.view_table_cb:
                self.view_table_cb(item)
            elif action == act_export and self.export_csv_cb:
                self.export_csv_cb(item)
            elif action == act_params and self.selection_callback:
                self.scene.clearSelection()
                item.setSelected(True)
                self.selection_callback(item)
            elif act_disconn and action == act_disconn:
                self.remove_connection_for_target(item)
                if self.connect_cb:
                    self.connect_cb(None, item)
            elif action == act_del and self.delete_node_cb:
                self.delete_node_cb(item)
            return

        # Menu sur un Câble / Lien
        elif isinstance(item, NodeConnectionItem):
            menu = QMenu(self)
            act_del_wire = menu.addAction(i18n.tr("delete_wire"))
            action = menu.exec(event.globalPos())
            if action == act_del_wire:
                self.delete_connection(item)
                if self.connect_cb:
                    self.connect_cb(None, None)
            return

        super().contextMenuEvent(event)

    def on_selection_changed(self):
        try:
            if not self.scene:
                return
            selected = self.scene.selectedItems()
            if selected and self.selection_callback:
                item = selected[0]
                if isinstance(item, ALL_NODE_TYPES):
                    self.selection_callback(item)
        except (RuntimeError, AttributeError):
            pass
