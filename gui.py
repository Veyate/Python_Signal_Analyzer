# gui.py
import os
import numpy as np
import scipy.integrate as integrate
from PySide6.QtCore import Qt, QByteArray
from PySide6.QtGui import QAction, QKeySequence, QFont, QColor
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QTreeWidget, QTreeWidgetItem, QTableWidget, QTableWidgetItem,
    QTabWidget, QDockWidget, QLineEdit, QComboBox, QCheckBox,
    QDoubleSpinBox, QSpinBox, QGroupBox, QPushButton, QLabel, QMenu,
    QFileDialog, QFontDialog, QApplication, QMessageBox, QSplitter, QScrollArea, QFrame, QColorDialog
)

import matplotlib
matplotlib.use('QtAgg')
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg, NavigationToolbar2QT
from matplotlib.figure import Figure

from i18n import i18n
from settings import SettingsManager
from project_io import ProjectIOManager
from engine import SignalGeneratorEngine, CSVImportEngine, FilterEngine, LowPassFilterEngine, MathOperatorsEngine, NoiseEngine, SamplingConversionEngine, DSPFilterEngine, DO160Engine, FFTAnalysisEngine, THDAnalysisEngine, THDAnalysisEngine

from nodes import NodeEditorCanvas, SignalGeneratorNode, CSVImportNode, LowPassFilterNode, HighPassFilterNode, BandPassFilterNode, BandStopFilterNode, DerivativeNode, IntegratorNode, GainNode, InversionNode, AbsNode, LogNode, ExpNode, PowerNode, NoiseNode, ResampleNode, InterpolationNode, DACNode, FixedAverageNode, MovingAverageNode, MedianFilterNode, AdditionNode, DO160DoubleExpNode, DO160DampedSineNode, FFTAnalysisNode, THDAnalysisNode, THDAnalysisNode

PROCESSOR_INPUT_TYPES = (
    SignalGeneratorNode, CSVImportNode, DO160DoubleExpNode, DO160DampedSineNode,
    LowPassFilterNode, HighPassFilterNode, BandPassFilterNode, BandStopFilterNode,
    DerivativeNode, IntegratorNode, GainNode, InversionNode, AbsNode, LogNode, ExpNode, PowerNode,
    NoiseNode, ResampleNode, InterpolationNode, DACNode,
    FixedAverageNode, MovingAverageNode, MedianFilterNode, AdditionNode, THDAnalysisNode
)



class SignalGeneratorParamWidget(QWidget):
    """Formulaire de réglage des paramètres du Générateur de Signal."""
    def __init__(self, node: SignalGeneratorNode, on_recalculate_cb=None, on_view_graph_cb=None, on_view_table_cb=None, on_export_csv_cb=None, on_delete_cb=None):
        super().__init__()
        self.node = node
        self.on_recalculate_cb = on_recalculate_cb
        self.on_view_graph_cb = on_view_graph_cb
        self.on_view_table_cb = on_view_table_cb
        self.on_delete_cb = on_delete_cb
        self.on_export_csv_cb = on_export_csv_cb

        layout = QVBoxLayout(self)

        form_group = QGroupBox("Paramètres du Générateur")
        form_layout = QFormLayout(form_group)

        # Nom
        self.name_edit = QLineEdit(node.params["name"])
        self.name_edit.textChanged.connect(self.on_param_modified)
        form_layout.addRow("Nom :", self.name_edit)

        # Forme d'onde
        self.waveform_combo = QComboBox()
        self.waveform_combo.addItems(SignalGeneratorEngine.WAVEFORMS)
        self.waveform_combo.setCurrentText(node.params["waveform"])
        self.waveform_combo.currentTextChanged.connect(self.on_param_modified)
        form_layout.addRow("Forme d'onde :", self.waveform_combo)

        # Fréquence (Hz)
        self.freq_spin = QDoubleSpinBox()
        self.freq_spin.setRange(0.1, 100000.0)
        self.freq_spin.setValue(node.params["frequency"])
        self.freq_spin.setSuffix(" Hz")
        self.freq_spin.valueChanged.connect(self.on_param_modified)
        form_layout.addRow("Fréquence :", self.freq_spin)

        # Amplitude (V)
        self.amp_spin = QDoubleSpinBox()
        self.amp_spin.setRange(0.0, 1000.0)
        self.amp_spin.setValue(node.params["amplitude"])
        self.amp_spin.setSuffix(" V")
        self.amp_spin.valueChanged.connect(self.on_param_modified)
        form_layout.addRow("Amplitude :", self.amp_spin)

        # Phase (deg)
        self.phase_spin = QDoubleSpinBox()
        self.phase_spin.setRange(-360.0, 360.0)
        self.phase_spin.setValue(node.params.get("phase", 0.0))
        self.phase_spin.setSuffix(" °")
        self.phase_spin.valueChanged.connect(self.on_param_modified)
        form_layout.addRow("Phase :", self.phase_spin)

        # Offset (V)
        self.offset_spin = QDoubleSpinBox()
        self.offset_spin.setRange(-500.0, 500.0)
        self.offset_spin.setValue(node.params["offset"])
        self.offset_spin.setSuffix(" V")
        self.offset_spin.valueChanged.connect(self.on_param_modified)
        form_layout.addRow("Offset :", self.offset_spin)

        # Taux d'échantillonnage
        self.rate_spin = QDoubleSpinBox()
        self.rate_spin.setRange(10.0, 1000000.0)
        self.rate_spin.setValue(node.params["sampling_rate"])
        self.rate_spin.setSuffix(" Hz")
        self.rate_spin.valueChanged.connect(self.on_param_modified)
        form_layout.addRow("Échantillonnage :", self.rate_spin)

        # Durée (s)
        self.dur_spin = QDoubleSpinBox()
        self.dur_spin.setRange(0.0001, 100000.0)
        self.dur_spin.setDecimals(4)
        self.dur_spin.setValue(float(node.params.get("duration", 1.0)))
        self.dur_spin.setSuffix(" s")
        self.dur_spin.valueChanged.connect(self.on_param_modified)
        form_layout.addRow("Durée :", self.dur_spin)

        layout.addWidget(form_group)

        # État + Recalculer
        status_group = QGroupBox("État du Nœud")
        status_layout = QVBoxLayout(status_group)
        
        self.status_label = QLabel()
        self.update_status_label()
        status_layout.addWidget(self.status_label)

        self.btn_recalc = QPushButton("🔄 Recalculer le nœud")
        self.btn_recalc.setStyleSheet("background-color: #00ADB5; color: white; font-weight: bold; padding: 6px;")
        self.btn_recalc.clicked.connect(self.on_recalc_clicked)
        status_layout.addWidget(self.btn_recalc)

        layout.addWidget(status_group)

        # Actions de Visualisation
        view_group = QGroupBox("Visualisation du Signal")
        view_layout = QVBoxLayout(view_group)

        self.btn_graph = QPushButton("📈 Voir le graphique (Matplotlib)")
        self.btn_graph.setStyleSheet("padding: 5px;")
        self.btn_graph.clicked.connect(lambda: self.on_view_graph_cb(self.node) if self.on_view_graph_cb else None)
        view_layout.addWidget(self.btn_graph)

        self.btn_table = QPushButton("📊 Voir le tableau de données (NumPy)")
        self.btn_table.setStyleSheet("padding: 5px;")
        self.btn_table.clicked.connect(lambda: self.on_view_table_cb(self.node) if self.on_view_table_cb else None)
        view_layout.addWidget(self.btn_table)

        self.btn_export_csv = QPushButton("💾 Exporter les données (CSV)...")
        self.btn_export_csv.setStyleSheet("padding: 5px;")
        self.btn_export_csv.clicked.connect(lambda: self.on_export_csv_cb(self.node) if getattr(self, "on_export_csv_cb", None) else None)
        view_layout.addWidget(self.btn_export_csv)

        layout.addWidget(view_group)

        # Bouton Supprimer Nœud
        self.btn_delete = QPushButton("🗑️ Supprimer ce nœud")
        self.btn_delete.setStyleSheet("background-color: #D32F2F; color: white; font-weight: bold; padding: 6px; margin-top: 10px;")
        self.btn_delete.clicked.connect(lambda: self.on_delete_cb(self.node) if self.on_delete_cb else None)
        layout.addWidget(self.btn_delete)

        layout.addStretch()

    def update_status_label(self):
        if self.node.is_dirty:
            self.status_label.setText("⚠️ Données non à jour (Paramètres modifiés)")
            self.status_label.setStyleSheet("color: #FF9800; font-weight: bold;")
        else:
            self.status_label.setText("✅ Données à jour")
            self.status_label.setStyleSheet("color: #4CAF50; font-weight: bold;")

    def on_param_modified(self):
        self.node.params["name"] = self.name_edit.text()
        self.node.params["waveform"] = self.waveform_combo.currentText()
        self.node.params["frequency"] = self.freq_spin.value()
        self.node.params["amplitude"] = self.amp_spin.value()
        self.node.params["phase"] = self.phase_spin.value()
        self.node.params["offset"] = self.offset_spin.value()
        self.node.params["sampling_rate"] = self.rate_spin.value()
        self.node.params["duration"] = self.dur_spin.value()

        self.node.mark_dirty()
        self.update_status_label()

        if self.on_recalculate_cb:
            self.on_recalculate_cb(self.node, executed=False)

    def on_recalc_clicked(self):
        self.node.recalculate()
        if "auto" in str(self.node.params.get("fundamental_mode", "")).lower():
            self.f0_spin.blockSignals(True)
            self.f0_spin.setValue(float(self.node.f0_detected))
            self.f0_spin.blockSignals(False)
        self.update_status_label()

        if self.on_recalculate_cb:
            self.on_recalculate_cb(self.node, executed=True)


class CSVImportParamWidget(QWidget):
    """Formulaire de réglage des paramètres du Nœud Import CSV."""
    def __init__(self, node: CSVImportNode, on_recalculate_cb=None, on_view_graph_cb=None, on_view_table_cb=None, on_export_csv_cb=None, on_delete_cb=None):
        super().__init__()
        self.node = node
        self.on_recalculate_cb = on_recalculate_cb
        self.on_view_graph_cb = on_view_graph_cb
        self.on_view_table_cb = on_view_table_cb
        self.on_delete_cb = on_delete_cb
        self.on_export_csv_cb = on_export_csv_cb

        layout = QVBoxLayout(self)

        form_group = QGroupBox("Paramètres de l'Import CSV")
        form_layout = QFormLayout(form_group)

        # Nom
        self.name_edit = QLineEdit(node.params["name"])
        self.name_edit.textChanged.connect(self.on_param_modified)
        form_layout.addRow("Nom :", self.name_edit)

        # Sélection de Fichier CSV
        file_box = QHBoxLayout()
        self.file_edit = QLineEdit(node.params["file_path"])
        self.file_edit.textChanged.connect(self.on_param_modified)
        btn_browse = QPushButton("📁 Parcourir...")
        btn_browse.clicked.connect(self.browse_file)
        file_box.addWidget(self.file_edit)
        file_box.addWidget(btn_browse)
        form_layout.addRow("Fichier CSV :", file_box)

        # Délimiteur
        self.delim_combo = QComboBox()
        self.delim_combo.addItems(CSVImportEngine.DELIMITERS)
        self.delim_combo.setCurrentText(node.params["delimiter"])
        self.delim_combo.currentTextChanged.connect(self.on_param_modified)
        form_layout.addRow("Séparateur :", self.delim_combo)

        # En-tête
        self.header_check = QCheckBox("Le fichier contient un en-tête")
        self.header_check.setChecked(node.params.get("has_header", True))
        self.header_check.stateChanged.connect(self.on_param_modified)
        form_layout.addRow("", self.header_check)

        # Index Colonne Temps
        self.time_col_spin = QSpinBox()
        self.time_col_spin.setRange(0, 50)
        self.time_col_spin.setValue(node.params.get("time_col_idx", 0))
        self.time_col_spin.valueChanged.connect(self.on_param_modified)
        form_layout.addRow("Col. Temps (0-index) :", self.time_col_spin)

        # Index Colonne Signal
        self.sig_col_spin = QSpinBox()
        self.sig_col_spin.setRange(0, 50)
        self.sig_col_spin.setValue(node.params.get("signal_col_idx", 1))
        self.sig_col_spin.valueChanged.connect(self.on_param_modified)
        form_layout.addRow("Col. Signal (0-index) :", self.sig_col_spin)

        # Taux d'échantillonnage par défaut
        self.rate_spin = QDoubleSpinBox()
        self.rate_spin.setRange(10.0, 1000000.0)
        self.rate_spin.setValue(node.params.get("sampling_rate", 1000.0))
        self.rate_spin.setSuffix(" Hz")
        self.rate_spin.valueChanged.connect(self.on_param_modified)
        form_layout.addRow("Échantillonnage par défaut :", self.rate_spin)

        layout.addWidget(form_group)

        # État + Bouton Charger/Recalculer
        status_group = QGroupBox("État du Fichier")
        status_layout = QVBoxLayout(status_group)
        
        self.status_label = QLabel()
        self.update_status_label()
        status_layout.addWidget(self.status_label)

        self.btn_recalc = QPushButton("🔄 Importer / Recalculer")
        self.btn_recalc.setStyleSheet("background-color: #009688; color: white; font-weight: bold; padding: 6px;")
        self.btn_recalc.clicked.connect(self.on_recalc_clicked)
        status_layout.addWidget(self.btn_recalc)

        layout.addWidget(status_group)

        # Actions de Visualisation
        view_group = QGroupBox("Visualisation du Signal CSV")
        view_layout = QVBoxLayout(view_group)

        self.btn_graph = QPushButton("📈 Voir le graphique (Matplotlib)")
        self.btn_graph.setStyleSheet("padding: 5px;")
        self.btn_graph.clicked.connect(lambda: self.on_view_graph_cb(self.node) if self.on_view_graph_cb else None)
        view_layout.addWidget(self.btn_graph)

        self.btn_table = QPushButton("📊 Voir le tableau de données (NumPy)")
        self.btn_table.setStyleSheet("padding: 5px;")
        self.btn_table.clicked.connect(lambda: self.on_view_table_cb(self.node) if self.on_view_table_cb else None)
        view_layout.addWidget(self.btn_table)

        self.btn_export_csv = QPushButton("💾 Exporter les données (CSV)...")
        self.btn_export_csv.setStyleSheet("padding: 5px;")
        self.btn_export_csv.clicked.connect(lambda: self.on_export_csv_cb(self.node) if getattr(self, "on_export_csv_cb", None) else None)
        view_layout.addWidget(self.btn_export_csv)

        layout.addWidget(view_group)

        # Supprimer Nœud
        self.btn_delete = QPushButton("🗑️ Supprimer ce nœud")
        self.btn_delete.setStyleSheet("background-color: #D32F2F; color: white; font-weight: bold; padding: 6px; margin-top: 10px;")
        self.btn_delete.clicked.connect(lambda: self.on_delete_cb(self.node) if self.on_delete_cb else None)
        layout.addWidget(self.btn_delete)

        layout.addStretch()

    def browse_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Sélectionner un fichier CSV", "", "Fichiers CSV (*.csv *.txt *.dat);;Tous les fichiers (*)")
        if file_path:
            self.file_edit.setText(file_path)

    def update_status_label(self):
        if self.node.is_dirty:
            self.status_label.setText(f"⚠️ Importer nécessaire | {self.node.status_msg}")
            self.status_label.setStyleSheet("color: #FF9800; font-weight: bold;")
        else:
            self.status_label.setText(f"✅ Fichier chargé | {self.node.status_msg}")
            self.status_label.setStyleSheet("color: #4CAF50; font-weight: bold;")

    def on_param_modified(self):
        self.node.params["name"] = self.name_edit.text()
        self.node.params["file_path"] = self.file_edit.text()
        self.node.params["delimiter"] = self.delim_combo.currentText()
        self.node.params["has_header"] = self.header_check.isChecked()
        self.node.params["time_col_idx"] = self.time_col_spin.value()
        self.node.params["signal_col_idx"] = self.sig_col_spin.value()
        self.node.params["sampling_rate"] = self.rate_spin.value()

        self.node.mark_dirty()
        self.update_status_label()

        if self.on_recalculate_cb:
            self.on_recalculate_cb(self.node, executed=False)

    def on_recalc_clicked(self):
        self.node.recalculate()
        if "auto" in str(self.node.params.get("fundamental_mode", "")).lower():
            self.f0_spin.blockSignals(True)
            self.f0_spin.setValue(float(self.node.f0_detected))
            self.f0_spin.blockSignals(False)
        self.update_status_label()

        if self.on_recalculate_cb:
            self.on_recalculate_cb(self.node, executed=True)


class LowPassFilterParamWidget(QWidget):
    """Formulaire de réglage des paramètres du Filtre Passe-Bas."""
    def __init__(self, node: LowPassFilterNode, available_sources=None, on_recalculate_cb=None, on_connect_cb=None, on_view_graph_cb=None, on_view_table_cb=None, on_export_csv_cb=None, on_delete_cb=None):
        super().__init__()
        self.node = node
        self.available_sources = available_sources or []
        self.on_recalculate_cb = on_recalculate_cb
        self.on_connect_cb = on_connect_cb
        self.on_view_graph_cb = on_view_graph_cb
        self.on_view_table_cb = on_view_table_cb
        self.on_delete_cb = on_delete_cb
        self.on_export_csv_cb = on_export_csv_cb

        layout = QVBoxLayout(self)

        form_group = QGroupBox("Paramètres du Filtre Passe-Bas")
        form_layout = QFormLayout(form_group)

        # Nom
        self.name_edit = QLineEdit(node.params["name"])
        self.name_edit.textChanged.connect(self.on_param_modified)
        form_layout.addRow("Nom du filtre :", self.name_edit)

        # Source d'entrée connectée
        self.source_combo = QComboBox()
        self.update_source_combo()
        self.source_combo.currentIndexChanged.connect(self.on_source_changed)
        form_layout.addRow("Signal d'entrée :", self.source_combo)

        # Fréquence de coupure fc (Hz)
        self.cutoff_spin = QDoubleSpinBox()
        self.cutoff_spin.setRange(0.1, 100000.0)
        self.cutoff_spin.setValue(node.params["cutoff"])
        self.cutoff_spin.setSuffix(" Hz")
        self.cutoff_spin.valueChanged.connect(self.on_param_modified)
        form_layout.addRow("Fréquence de coupure (fc) :", self.cutoff_spin)

        # Ordre du filtre
        self.order_spin = QSpinBox()
        self.order_spin.setRange(1, 10)
        self.order_spin.setValue(node.params["order"])
        self.order_spin.valueChanged.connect(self.on_param_modified)
        form_layout.addRow("Ordre du filtre :", self.order_spin)

        # Type de filtre
        self.type_combo = QComboBox()
        self.type_combo.addItems(LowPassFilterEngine.FILTER_TYPES)
        self.type_combo.setCurrentText(node.params["filter_type"])
        self.type_combo.currentTextChanged.connect(self.on_param_modified)
        form_layout.addRow("Type de filtre :", self.type_combo)

        layout.addWidget(form_group)

        # État + Recalculer
        status_group = QGroupBox("État du Nœud")
        status_layout = QVBoxLayout(status_group)
        
        self.status_label = QLabel()
        self.update_status_label()
        status_layout.addWidget(self.status_label)

        self.btn_recalc = QPushButton("🔄 Recalculer le filtre")
        self.btn_recalc.setStyleSheet("background-color: #9C27B0; color: white; font-weight: bold; padding: 6px;")
        self.btn_recalc.clicked.connect(self.on_recalc_clicked)
        status_layout.addWidget(self.btn_recalc)

        layout.addWidget(status_group)

        # Actions de Visualisation
        view_group = QGroupBox("Visualisation du Pipeline")
        view_layout = QVBoxLayout(view_group)

        self.btn_graph = QPushButton("📈 Voir le graphique (Entrée vs Filtré)")
        self.btn_graph.setStyleSheet("padding: 5px;")
        self.btn_graph.clicked.connect(lambda: self.on_view_graph_cb(self.node) if self.on_view_graph_cb else None)
        view_layout.addWidget(self.btn_graph)

        self.btn_table = QPushButton("📊 Voir le tableau pipeline (NumPy)")
        self.btn_table.setStyleSheet("padding: 5px;")
        self.btn_table.clicked.connect(lambda: self.on_view_table_cb(self.node) if self.on_view_table_cb else None)
        view_layout.addWidget(self.btn_table)

        layout.addWidget(view_group)

        # Supprimer Nœud
        self.btn_delete = QPushButton("🗑️ Supprimer ce nœud")
        self.btn_delete.setStyleSheet("background-color: #D32F2F; color: white; font-weight: bold; padding: 6px; margin-top: 10px;")
        self.btn_delete.clicked.connect(lambda: self.on_delete_cb(self.node) if self.on_delete_cb else None)
        layout.addWidget(self.btn_delete)

        layout.addStretch()

    def update_source_combo(self):
        self.source_combo.blockSignals(True)
        self.source_combo.clear()
        self.source_combo.addItem("Aucune connexion", None)

        selected_idx = 0
        for idx, src in enumerate(self.available_sources):
            self.source_combo.addItem(f"Source : {src.params['name']}", src)
            if self.node.input_node == src:
                selected_idx = idx + 1

        self.source_combo.setCurrentIndex(selected_idx)
        self.source_combo.blockSignals(False)

    def on_source_changed(self):
        selected_src = self.source_combo.currentData()
        if self.on_connect_cb:
            self.on_connect_cb(selected_src, self.node)
        self.on_param_modified()

    def update_status_label(self):
        if self.node.is_dirty:
            self.status_label.setText("⚠️ Données non à jour (Paramètres modifiés)")
            self.status_label.setStyleSheet("color: #FF9800; font-weight: bold;")
        else:
            self.status_label.setText("✅ Filtre à jour")
            self.status_label.setStyleSheet("color: #4CAF50; font-weight: bold;")

    def on_param_modified(self):
        self.node.params["name"] = self.name_edit.text()
        self.node.params["cutoff"] = self.cutoff_spin.value()
        self.node.params["order"] = self.order_spin.value()
        self.node.params["filter_type"] = self.type_combo.currentText()

        self.node.mark_dirty()
        self.update_status_label()

        if self.on_recalculate_cb:
            self.on_recalculate_cb(self.node, executed=False)

    def on_recalc_clicked(self):
        self.node.recalculate()
        if "auto" in str(self.node.params.get("fundamental_mode", "")).lower():
            self.f0_spin.blockSignals(True)
            self.f0_spin.setValue(float(self.node.f0_detected))
            self.f0_spin.blockSignals(False)
        self.update_status_label()

        if self.on_recalculate_cb:
            self.on_recalculate_cb(self.node, executed=True)


class HighPassFilterParamWidget(QWidget):
    """Formulaire de réglage des paramètres du Filtre Passe-Bas."""
    def __init__(self, node: HighPassFilterNode, available_sources=None, on_recalculate_cb=None, on_connect_cb=None, on_view_graph_cb=None, on_view_table_cb=None, on_export_csv_cb=None, on_delete_cb=None):
        super().__init__()
        self.node = node
        self.available_sources = available_sources or []
        self.on_recalculate_cb = on_recalculate_cb
        self.on_connect_cb = on_connect_cb
        self.on_view_graph_cb = on_view_graph_cb
        self.on_view_table_cb = on_view_table_cb
        self.on_delete_cb = on_delete_cb
        self.on_export_csv_cb = on_export_csv_cb

        layout = QVBoxLayout(self)

        form_group = QGroupBox("Paramètres du Filtre Passe-Haut")
        form_layout = QFormLayout(form_group)

        # Nom
        self.name_edit = QLineEdit(node.params["name"])
        self.name_edit.textChanged.connect(self.on_param_modified)
        form_layout.addRow("Nom du filtre :", self.name_edit)

        # Source d'entrée connectée
        self.source_combo = QComboBox()
        self.update_source_combo()
        self.source_combo.currentIndexChanged.connect(self.on_source_changed)
        form_layout.addRow("Signal d'entrée :", self.source_combo)

        # Fréquence de coupure fc (Hz)
        self.cutoff_spin = QDoubleSpinBox()
        self.cutoff_spin.setRange(0.1, 100000.0)
        self.cutoff_spin.setValue(node.params["cutoff"])
        self.cutoff_spin.setSuffix(" Hz")
        self.cutoff_spin.valueChanged.connect(self.on_param_modified)
        form_layout.addRow("Fréquence de coupure (fc) :", self.cutoff_spin)

        # Ordre du filtre
        self.order_spin = QSpinBox()
        self.order_spin.setRange(1, 10)
        self.order_spin.setValue(node.params["order"])
        self.order_spin.valueChanged.connect(self.on_param_modified)
        form_layout.addRow("Ordre du filtre :", self.order_spin)

        # Type de filtre
        self.type_combo = QComboBox()
        self.type_combo.addItems(LowPassFilterEngine.FILTER_TYPES)
        self.type_combo.setCurrentText(node.params["filter_type"])
        self.type_combo.currentTextChanged.connect(self.on_param_modified)
        form_layout.addRow("Type de filtre :", self.type_combo)

        layout.addWidget(form_group)

        # État + Recalculer
        status_group = QGroupBox("État du Nœud")
        status_layout = QVBoxLayout(status_group)
        
        self.status_label = QLabel()
        self.update_status_label()
        status_layout.addWidget(self.status_label)

        self.btn_recalc = QPushButton("🔄 Recalculer le filtre")
        self.btn_recalc.setStyleSheet("background-color: #3F51B5; color: white; font-weight: bold; padding: 6px;")
        self.btn_recalc.clicked.connect(self.on_recalc_clicked)
        status_layout.addWidget(self.btn_recalc)

        layout.addWidget(status_group)

        # Actions de Visualisation
        view_group = QGroupBox("Visualisation du Pipeline")
        view_layout = QVBoxLayout(view_group)

        self.btn_graph = QPushButton("📈 Voir le graphique (Entrée vs Filtré)")
        self.btn_graph.setStyleSheet("padding: 5px;")
        self.btn_graph.clicked.connect(lambda: self.on_view_graph_cb(self.node) if self.on_view_graph_cb else None)
        view_layout.addWidget(self.btn_graph)

        self.btn_table = QPushButton("📊 Voir le tableau pipeline (NumPy)")
        self.btn_table.setStyleSheet("padding: 5px;")
        self.btn_table.clicked.connect(lambda: self.on_view_table_cb(self.node) if self.on_view_table_cb else None)
        view_layout.addWidget(self.btn_table)

        layout.addWidget(view_group)

        # Supprimer Nœud
        self.btn_delete = QPushButton("🗑️ Supprimer ce nœud")
        self.btn_delete.setStyleSheet("background-color: #D32F2F; color: white; font-weight: bold; padding: 6px; margin-top: 10px;")
        self.btn_delete.clicked.connect(lambda: self.on_delete_cb(self.node) if self.on_delete_cb else None)
        layout.addWidget(self.btn_delete)

        layout.addStretch()

    def update_source_combo(self):
        self.source_combo.blockSignals(True)
        self.source_combo.clear()
        self.source_combo.addItem("Aucune connexion", None)

        selected_idx = 0
        for idx, src in enumerate(self.available_sources):
            self.source_combo.addItem(f"Source : {src.params['name']}", src)
            if self.node.input_node == src:
                selected_idx = idx + 1

        self.source_combo.setCurrentIndex(selected_idx)
        self.source_combo.blockSignals(False)

    def on_source_changed(self):
        selected_src = self.source_combo.currentData()
        if self.on_connect_cb:
            self.on_connect_cb(selected_src, self.node)
        self.on_param_modified()

    def update_status_label(self):
        if self.node.is_dirty:
            self.status_label.setText("⚠️ Données non à jour (Paramètres modifiés)")
            self.status_label.setStyleSheet("color: #FF9800; font-weight: bold;")
        else:
            self.status_label.setText("✅ Filtre à jour")
            self.status_label.setStyleSheet("color: #4CAF50; font-weight: bold;")

    def on_param_modified(self):
        self.node.params["name"] = self.name_edit.text()
        self.node.params["cutoff"] = self.cutoff_spin.value()
        self.node.params["order"] = self.order_spin.value()
        self.node.params["filter_type"] = self.type_combo.currentText()

        self.node.mark_dirty()
        self.update_status_label()

        if self.on_recalculate_cb:
            self.on_recalculate_cb(self.node, executed=False)

    def on_recalc_clicked(self):
        self.node.recalculate()
        if "auto" in str(self.node.params.get("fundamental_mode", "")).lower():
            self.f0_spin.blockSignals(True)
            self.f0_spin.setValue(float(self.node.f0_detected))
            self.f0_spin.blockSignals(False)
        self.update_status_label()

        if self.on_recalculate_cb:
            self.on_recalculate_cb(self.node, executed=True)



class BandPassFilterParamWidget(QWidget):
    """Formulaire de réglage des paramètres du Filtre Passe-Bande."""
    def __init__(self, node: BandPassFilterNode, available_sources=None, on_recalculate_cb=None, on_connect_cb=None, on_view_graph_cb=None, on_view_table_cb=None, on_export_csv_cb=None, on_delete_cb=None):
        super().__init__()
        self.node = node
        self.available_sources = available_sources or []
        self.on_recalculate_cb = on_recalculate_cb
        self.on_connect_cb = on_connect_cb
        self.on_view_graph_cb = on_view_graph_cb
        self.on_view_table_cb = on_view_table_cb
        self.on_export_csv_cb = on_export_csv_cb
        self.on_delete_cb = on_delete_cb

        layout = QVBoxLayout(self)

        form_group = QGroupBox("Paramètres du Filtre Passe-Bande")
        form_layout = QFormLayout(form_group)

        self.name_edit = QLineEdit(node.params["name"])
        self.name_edit.textChanged.connect(self.on_param_modified)
        form_layout.addRow("Nom du filtre :", self.name_edit)

        self.source_combo = QComboBox()
        self.update_source_combo()
        self.source_combo.currentIndexChanged.connect(self.on_source_changed)
        form_layout.addRow("Signal d'entrée :", self.source_combo)

        self.low_cutoff_spin = QDoubleSpinBox()
        self.low_cutoff_spin.setRange(0.1, 100000.0)
        self.low_cutoff_spin.setValue(node.params["low_cutoff"])
        self.low_cutoff_spin.setSuffix(" Hz")
        self.low_cutoff_spin.valueChanged.connect(self.on_param_modified)
        form_layout.addRow("Fréquence basse (f1) :", self.low_cutoff_spin)

        self.high_cutoff_spin = QDoubleSpinBox()
        self.high_cutoff_spin.setRange(0.1, 100000.0)
        self.high_cutoff_spin.setValue(node.params["high_cutoff"])
        self.high_cutoff_spin.setSuffix(" Hz")
        self.high_cutoff_spin.valueChanged.connect(self.on_param_modified)
        form_layout.addRow("Fréquence haute (f2) :", self.high_cutoff_spin)

        self.order_spin = QSpinBox()
        self.order_spin.setRange(1, 10)
        self.order_spin.setValue(node.params["order"])
        self.order_spin.valueChanged.connect(self.on_param_modified)
        form_layout.addRow("Ordre du filtre :", self.order_spin)

        self.type_combo = QComboBox()
        self.type_combo.addItems(FilterEngine.FILTER_TYPES)
        self.type_combo.setCurrentText(node.params["filter_type"])
        self.type_combo.currentTextChanged.connect(self.on_param_modified)
        form_layout.addRow("Type de filtre :", self.type_combo)

        layout.addWidget(form_group)

        status_group = QGroupBox("État du Nœud")
        status_layout = QVBoxLayout(status_group)
        
        self.status_label = QLabel()
        self.update_status_label()
        status_layout.addWidget(self.status_label)

        self.btn_recalc = QPushButton("🔄 Recalculer le filtre")
        self.btn_recalc.setStyleSheet("background-color: #009688; color: white; font-weight: bold; padding: 6px;")
        self.btn_recalc.clicked.connect(self.on_recalc_clicked)
        status_layout.addWidget(self.btn_recalc)

        layout.addWidget(status_group)

        view_group = QGroupBox("Visualisation du Pipeline")
        view_layout = QVBoxLayout(view_group)

        self.btn_graph = QPushButton("📈 Voir le graphique (Entrée vs Filtré)")
        self.btn_graph.setStyleSheet("padding: 5px;")
        self.btn_graph.clicked.connect(lambda: self.on_view_graph_cb(self.node) if self.on_view_graph_cb else None)
        view_layout.addWidget(self.btn_graph)

        self.btn_table = QPushButton("📊 Voir le tableau pipeline (NumPy)")
        self.btn_table.setStyleSheet("padding: 5px;")
        self.btn_table.clicked.connect(lambda: self.on_view_table_cb(self.node) if self.on_view_table_cb else None)
        view_layout.addWidget(self.btn_table)

        self.btn_export_csv = QPushButton("💾 Exporter les données (CSV)...")
        self.btn_export_csv.setStyleSheet("padding: 5px;")
        self.btn_export_csv.clicked.connect(lambda: self.on_export_csv_cb(self.node) if self.on_export_csv_cb else None)
        view_layout.addWidget(self.btn_export_csv)

        layout.addWidget(view_group)

        self.btn_delete = QPushButton("🗑️ Supprimer ce nœud")
        self.btn_delete.setStyleSheet("background-color: #D32F2F; color: white; font-weight: bold; padding: 6px; margin-top: 10px;")
        self.btn_delete.clicked.connect(lambda: self.on_delete_cb(self.node) if self.on_delete_cb else None)
        layout.addWidget(self.btn_delete)

        layout.addStretch()

    def update_source_combo(self):
        self.source_combo.blockSignals(True)
        self.source_combo.clear()
        self.source_combo.addItem("Aucune connexion", None)

        selected_idx = 0
        for idx, src in enumerate(self.available_sources):
            self.source_combo.addItem(f"Source : {src.params['name']}", src)
            if self.node.input_node == src:
                selected_idx = idx + 1

        self.source_combo.setCurrentIndex(selected_idx)
        self.source_combo.blockSignals(False)

    def on_source_changed(self):
        selected_src = self.source_combo.currentData()
        if self.on_connect_cb:
            self.on_connect_cb(selected_src, self.node)
        self.on_param_modified()

    def update_status_label(self):
        if self.node.is_dirty:
            self.status_label.setText("⚠️ Données non à jour (Paramètres modifiés)")
            self.status_label.setStyleSheet("color: #FF9800; font-weight: bold;")
        else:
            self.status_label.setText("✅ Filtre à jour")
            self.status_label.setStyleSheet("color: #4CAF50; font-weight: bold;")

    def on_param_modified(self):
        self.node.params["name"] = self.name_edit.text()
        self.node.params["low_cutoff"] = self.low_cutoff_spin.value()
        self.node.params["high_cutoff"] = self.high_cutoff_spin.value()
        self.node.params["order"] = self.order_spin.value()
        self.node.params["filter_type"] = self.type_combo.currentText()

        self.node.mark_dirty()
        self.update_status_label()

        if self.on_recalculate_cb:
            self.on_recalculate_cb(self.node, executed=False)

    def on_recalc_clicked(self):
        self.node.recalculate()
        if "auto" in str(self.node.params.get("fundamental_mode", "")).lower():
            self.f0_spin.blockSignals(True)
            self.f0_spin.setValue(float(self.node.f0_detected))
            self.f0_spin.blockSignals(False)
        self.update_status_label()

        if self.on_recalculate_cb:
            self.on_recalculate_cb(self.node, executed=True)

class BandStopFilterParamWidget(QWidget):
    """Formulaire de réglage des paramètres du Filtre Passe-Bande."""
    def __init__(self, node: BandStopFilterNode, available_sources=None, on_recalculate_cb=None, on_connect_cb=None, on_view_graph_cb=None, on_view_table_cb=None, on_export_csv_cb=None, on_delete_cb=None):
        super().__init__()
        self.node = node
        self.available_sources = available_sources or []
        self.on_recalculate_cb = on_recalculate_cb
        self.on_connect_cb = on_connect_cb
        self.on_view_graph_cb = on_view_graph_cb
        self.on_view_table_cb = on_view_table_cb
        self.on_export_csv_cb = on_export_csv_cb
        self.on_delete_cb = on_delete_cb

        layout = QVBoxLayout(self)

        form_group = QGroupBox("Paramètres du Filtre Coupe-Bande")
        form_layout = QFormLayout(form_group)

        self.name_edit = QLineEdit(node.params["name"])
        self.name_edit.textChanged.connect(self.on_param_modified)
        form_layout.addRow("Nom du filtre :", self.name_edit)

        self.source_combo = QComboBox()
        self.update_source_combo()
        self.source_combo.currentIndexChanged.connect(self.on_source_changed)
        form_layout.addRow("Signal d'entrée :", self.source_combo)

        self.low_cutoff_spin = QDoubleSpinBox()
        self.low_cutoff_spin.setRange(0.1, 100000.0)
        self.low_cutoff_spin.setValue(node.params["low_cutoff"])
        self.low_cutoff_spin.setSuffix(" Hz")
        self.low_cutoff_spin.valueChanged.connect(self.on_param_modified)
        form_layout.addRow("Fréquence basse (f1) :", self.low_cutoff_spin)

        self.high_cutoff_spin = QDoubleSpinBox()
        self.high_cutoff_spin.setRange(0.1, 100000.0)
        self.high_cutoff_spin.setValue(node.params["high_cutoff"])
        self.high_cutoff_spin.setSuffix(" Hz")
        self.high_cutoff_spin.valueChanged.connect(self.on_param_modified)
        form_layout.addRow("Fréquence haute (f2) :", self.high_cutoff_spin)

        self.order_spin = QSpinBox()
        self.order_spin.setRange(1, 10)
        self.order_spin.setValue(node.params["order"])
        self.order_spin.valueChanged.connect(self.on_param_modified)
        form_layout.addRow("Ordre du filtre :", self.order_spin)

        self.type_combo = QComboBox()
        self.type_combo.addItems(FilterEngine.FILTER_TYPES)
        self.type_combo.setCurrentText(node.params["filter_type"])
        self.type_combo.currentTextChanged.connect(self.on_param_modified)
        form_layout.addRow("Type de filtre :", self.type_combo)

        layout.addWidget(form_group)

        status_group = QGroupBox("État du Nœud")
        status_layout = QVBoxLayout(status_group)
        
        self.status_label = QLabel()
        self.update_status_label()
        status_layout.addWidget(self.status_label)

        self.btn_recalc = QPushButton("🔄 Recalculer le filtre")
        self.btn_recalc.setStyleSheet("background-color: #795548; color: white; font-weight: bold; padding: 6px;")
        self.btn_recalc.clicked.connect(self.on_recalc_clicked)
        status_layout.addWidget(self.btn_recalc)

        layout.addWidget(status_group)

        view_group = QGroupBox("Visualisation du Pipeline")
        view_layout = QVBoxLayout(view_group)

        self.btn_graph = QPushButton("📈 Voir le graphique (Entrée vs Filtré)")
        self.btn_graph.setStyleSheet("padding: 5px;")
        self.btn_graph.clicked.connect(lambda: self.on_view_graph_cb(self.node) if self.on_view_graph_cb else None)
        view_layout.addWidget(self.btn_graph)

        self.btn_table = QPushButton("📊 Voir le tableau pipeline (NumPy)")
        self.btn_table.setStyleSheet("padding: 5px;")
        self.btn_table.clicked.connect(lambda: self.on_view_table_cb(self.node) if self.on_view_table_cb else None)
        view_layout.addWidget(self.btn_table)

        self.btn_export_csv = QPushButton("💾 Exporter les données (CSV)...")
        self.btn_export_csv.setStyleSheet("padding: 5px;")
        self.btn_export_csv.clicked.connect(lambda: self.on_export_csv_cb(self.node) if self.on_export_csv_cb else None)
        view_layout.addWidget(self.btn_export_csv)

        layout.addWidget(view_group)

        self.btn_delete = QPushButton("🗑️ Supprimer ce nœud")
        self.btn_delete.setStyleSheet("background-color: #D32F2F; color: white; font-weight: bold; padding: 6px; margin-top: 10px;")
        self.btn_delete.clicked.connect(lambda: self.on_delete_cb(self.node) if self.on_delete_cb else None)
        layout.addWidget(self.btn_delete)

        layout.addStretch()

    def update_source_combo(self):
        self.source_combo.blockSignals(True)
        self.source_combo.clear()
        self.source_combo.addItem("Aucune connexion", None)

        selected_idx = 0
        for idx, src in enumerate(self.available_sources):
            self.source_combo.addItem(f"Source : {src.params['name']}", src)
            if self.node.input_node == src:
                selected_idx = idx + 1

        self.source_combo.setCurrentIndex(selected_idx)
        self.source_combo.blockSignals(False)

    def on_source_changed(self):
        selected_src = self.source_combo.currentData()
        if self.on_connect_cb:
            self.on_connect_cb(selected_src, self.node)
        self.on_param_modified()

    def update_status_label(self):
        if self.node.is_dirty:
            self.status_label.setText("⚠️ Données non à jour (Paramètres modifiés)")
            self.status_label.setStyleSheet("color: #FF9800; font-weight: bold;")
        else:
            self.status_label.setText("✅ Filtre à jour")
            self.status_label.setStyleSheet("color: #4CAF50; font-weight: bold;")

    def on_param_modified(self):
        self.node.params["name"] = self.name_edit.text()
        self.node.params["low_cutoff"] = self.low_cutoff_spin.value()
        self.node.params["high_cutoff"] = self.high_cutoff_spin.value()
        self.node.params["order"] = self.order_spin.value()
        self.node.params["filter_type"] = self.type_combo.currentText()

        self.node.mark_dirty()
        self.update_status_label()

        if self.on_recalculate_cb:
            self.on_recalculate_cb(self.node, executed=False)

    def on_recalc_clicked(self):
        self.node.recalculate()
        if "auto" in str(self.node.params.get("fundamental_mode", "")).lower():
            self.f0_spin.blockSignals(True)
            self.f0_spin.setValue(float(self.node.f0_detected))
            self.f0_spin.blockSignals(False)
        self.update_status_label()

        if self.on_recalculate_cb:
            self.on_recalculate_cb(self.node, executed=True)

class DerivativeParamWidget(QWidget):
    """Formulaire de réglage des paramètres du Dérivateur."""
    def __init__(self, node: DerivativeNode, available_sources=None, on_recalculate_cb=None, on_connect_cb=None, on_view_graph_cb=None, on_view_table_cb=None, on_export_csv_cb=None, on_delete_cb=None):
        super().__init__()
        self.node = node
        self.available_sources = available_sources or []
        self.on_recalculate_cb = on_recalculate_cb
        self.on_connect_cb = on_connect_cb
        self.on_view_graph_cb = on_view_graph_cb
        self.on_view_table_cb = on_view_table_cb
        self.on_export_csv_cb = on_export_csv_cb
        self.on_delete_cb = on_delete_cb

        layout = QVBoxLayout(self)

        form_group = QGroupBox("Paramètres du Dérivateur")
        form_layout = QFormLayout(form_group)

        self.name_edit = QLineEdit(node.params["name"])
        self.name_edit.textChanged.connect(self.on_param_modified)
        form_layout.addRow("Nom :", self.name_edit)

        self.source_combo = QComboBox()
        self.update_source_combo()
        self.source_combo.currentIndexChanged.connect(self.on_source_changed)
        form_layout.addRow("Signal d'entrée :", self.source_combo)

        layout.addWidget(form_group)

        status_group = QGroupBox("État du Nœud")
        status_layout = QVBoxLayout(status_group)
        self.status_label = QLabel()
        self.update_status_label()
        status_layout.addWidget(self.status_label)

        self.btn_recalc = QPushButton("🔄 Recalculer le dérivateur")
        self.btn_recalc.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; padding: 6px;")
        self.btn_recalc.clicked.connect(self.on_recalc_clicked)
        status_layout.addWidget(self.btn_recalc)

        layout.addWidget(status_group)

        view_group = QGroupBox("Visualisation du Pipeline")
        view_layout = QVBoxLayout(view_group)

        self.btn_graph = QPushButton("📈 Voir le graphique (Entrée vs Dérivée)")
        self.btn_graph.setStyleSheet("padding: 5px;")
        self.btn_graph.clicked.connect(lambda: self.on_view_graph_cb(self.node) if self.on_view_graph_cb else None)
        view_layout.addWidget(self.btn_graph)

        self.btn_table = QPushButton("📊 Voir le tableau pipeline (NumPy)")
        self.btn_table.setStyleSheet("padding: 5px;")
        self.btn_table.clicked.connect(lambda: self.on_view_table_cb(self.node) if self.on_view_table_cb else None)
        view_layout.addWidget(self.btn_table)

        self.btn_export_csv = QPushButton("💾 Exporter les données (CSV)...")
        self.btn_export_csv.setStyleSheet("padding: 5px; font-weight: bold;")
        self.btn_export_csv.clicked.connect(lambda: self.on_export_csv_cb(self.node) if self.on_export_csv_cb else None)
        view_layout.addWidget(self.btn_export_csv)

        layout.addWidget(view_group)

        self.btn_delete = QPushButton("🗑️ Supprimer ce nœud")
        self.btn_delete.setStyleSheet("background-color: #D32F2F; color: white; font-weight: bold; padding: 6px; margin-top: 10px;")
        self.btn_delete.clicked.connect(lambda: self.on_delete_cb(self.node) if self.on_delete_cb else None)
        layout.addWidget(self.btn_delete)

        layout.addStretch()

    def update_source_combo(self):
        self.source_combo.blockSignals(True)
        self.source_combo.clear()
        self.source_combo.addItem("Aucune connexion", None)

        selected_idx = 0
        for idx, src in enumerate(self.available_sources):
            self.source_combo.addItem(f"Entrée : {src.params['name']}", src)
            if self.node.input_node == src:
                selected_idx = idx + 1

        self.source_combo.setCurrentIndex(selected_idx)
        self.source_combo.blockSignals(False)

    def on_source_changed(self):
        selected_src = self.source_combo.currentData()
        if self.on_connect_cb:
            self.on_connect_cb(selected_src, self.node)
        self.on_param_modified()

    def update_status_label(self):
        if self.node.is_dirty:
            self.status_label.setText("⚠️ Données non à jour (Paramètres modifiés)")
            self.status_label.setStyleSheet("color: #FF9800; font-weight: bold;")
        else:
            self.status_label.setText("✅ Dérivée à jour")
            self.status_label.setStyleSheet("color: #4CAF50; font-weight: bold;")

    def on_param_modified(self):
        self.node.params["name"] = self.name_edit.text()
        self.node.mark_dirty()
        self.update_status_label()
        if self.on_recalculate_cb:
            self.on_recalculate_cb(self.node, executed=False)

    def on_recalc_clicked(self):
        self.node.recalculate()
        self.update_status_label()
        if self.on_recalculate_cb:
            self.on_recalculate_cb(self.node, executed=True)


class IntegratorParamWidget(QWidget):
    """Formulaire de réglage des paramètres de l'Intégrateur."""
    def __init__(self, node: IntegratorNode, available_sources=None, on_recalculate_cb=None, on_connect_cb=None, on_view_graph_cb=None, on_view_table_cb=None, on_export_csv_cb=None, on_delete_cb=None):
        super().__init__()
        self.node = node
        self.available_sources = available_sources or []
        self.on_recalculate_cb = on_recalculate_cb
        self.on_connect_cb = on_connect_cb
        self.on_view_graph_cb = on_view_graph_cb
        self.on_view_table_cb = on_view_table_cb
        self.on_export_csv_cb = on_export_csv_cb
        self.on_delete_cb = on_delete_cb

        layout = QVBoxLayout(self)

        form_group = QGroupBox("Paramètres de l'Intégrateur")
        form_layout = QFormLayout(form_group)

        self.name_edit = QLineEdit(node.params["name"])
        self.name_edit.textChanged.connect(self.on_param_modified)
        form_layout.addRow("Nom :", self.name_edit)

        self.source_combo = QComboBox()
        self.update_source_combo()
        self.source_combo.currentIndexChanged.connect(self.on_source_changed)
        form_layout.addRow("Signal d'entrée :", self.source_combo)

        self.init_val_spin = QDoubleSpinBox()
        self.init_val_spin.setRange(-100000.0, 100000.0)
        self.init_val_spin.setValue(node.params.get("initial_val", 0.0))
        self.init_val_spin.valueChanged.connect(self.on_param_modified)
        form_layout.addRow("Valeur initiale y(0) :", self.init_val_spin)

        layout.addWidget(form_group)

        status_group = QGroupBox("État du Nœud")
        status_layout = QVBoxLayout(status_group)
        self.status_label = QLabel()
        self.update_status_label()
        status_layout.addWidget(self.status_label)

        self.btn_recalc = QPushButton("🔄 Recalculer l'intégrateur")
        self.btn_recalc.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; padding: 6px;")
        self.btn_recalc.clicked.connect(self.on_recalc_clicked)
        status_layout.addWidget(self.btn_recalc)

        layout.addWidget(status_group)

        view_group = QGroupBox("Visualisation du Pipeline")
        view_layout = QVBoxLayout(view_group)

        self.btn_graph = QPushButton("📈 Voir le graphique (Entrée vs Intégrée)")
        self.btn_graph.setStyleSheet("padding: 5px;")
        self.btn_graph.clicked.connect(lambda: self.on_view_graph_cb(self.node) if self.on_view_graph_cb else None)
        view_layout.addWidget(self.btn_graph)

        self.btn_table = QPushButton("📊 Voir le tableau pipeline (NumPy)")
        self.btn_table.setStyleSheet("padding: 5px;")
        self.btn_table.clicked.connect(lambda: self.on_view_table_cb(self.node) if self.on_view_table_cb else None)
        view_layout.addWidget(self.btn_table)

        self.btn_export_csv = QPushButton("💾 Exporter les données (CSV)...")
        self.btn_export_csv.setStyleSheet("padding: 5px; font-weight: bold;")
        self.btn_export_csv.clicked.connect(lambda: self.on_export_csv_cb(self.node) if self.on_export_csv_cb else None)
        view_layout.addWidget(self.btn_export_csv)

        layout.addWidget(view_group)

        self.btn_delete = QPushButton("🗑️ Supprimer ce nœud")
        self.btn_delete.setStyleSheet("background-color: #D32F2F; color: white; font-weight: bold; padding: 6px; margin-top: 10px;")
        self.btn_delete.clicked.connect(lambda: self.on_delete_cb(self.node) if self.on_delete_cb else None)
        layout.addWidget(self.btn_delete)

        layout.addStretch()

    def update_source_combo(self):
        self.source_combo.blockSignals(True)
        self.source_combo.clear()
        self.source_combo.addItem("Aucune connexion", None)

        selected_idx = 0
        for idx, src in enumerate(self.available_sources):
            self.source_combo.addItem(f"Entrée : {src.params['name']}", src)
            if self.node.input_node == src:
                selected_idx = idx + 1

        self.source_combo.setCurrentIndex(selected_idx)
        self.source_combo.blockSignals(False)

    def on_source_changed(self):
        selected_src = self.source_combo.currentData()
        if self.on_connect_cb:
            self.on_connect_cb(selected_src, self.node)
        self.on_param_modified()

    def update_status_label(self):
        if self.node.is_dirty:
            self.status_label.setText("⚠️ Données non à jour (Paramètres modifiés)")
            self.status_label.setStyleSheet("color: #FF9800; font-weight: bold;")
        else:
            self.status_label.setText("✅ Intégrale à jour")
            self.status_label.setStyleSheet("color: #4CAF50; font-weight: bold;")

    def on_param_modified(self):
        self.node.params["name"] = self.name_edit.text()
        self.node.params["initial_val"] = self.init_val_spin.value()
        self.node.mark_dirty()
        self.update_status_label()
        if self.on_recalculate_cb:
            self.on_recalculate_cb(self.node, executed=False)

    def on_recalc_clicked(self):
        self.node.recalculate()
        self.update_status_label()
        if self.on_recalculate_cb:
            self.on_recalculate_cb(self.node, executed=True)


class GainParamWidget(QWidget):
    """Formulaire de réglage des paramètres de Gain & Offset."""
    def __init__(self, node: GainNode, available_sources=None, on_recalculate_cb=None, on_connect_cb=None, on_view_graph_cb=None, on_view_table_cb=None, on_export_csv_cb=None, on_delete_cb=None):
        super().__init__()
        self.node = node
        self.available_sources = available_sources or []
        self.on_recalculate_cb = on_recalculate_cb
        self.on_connect_cb = on_connect_cb
        self.on_view_graph_cb = on_view_graph_cb
        self.on_view_table_cb = on_view_table_cb
        self.on_export_csv_cb = on_export_csv_cb
        self.on_delete_cb = on_delete_cb

        layout = QVBoxLayout(self)

        form_group = QGroupBox("Paramètres de Gain & Offset")
        form_layout = QFormLayout(form_group)

        self.name_edit = QLineEdit(node.params["name"])
        self.name_edit.textChanged.connect(self.on_param_modified)
        form_layout.addRow("Nom :", self.name_edit)

        self.source_combo = QComboBox()
        self.update_source_combo()
        self.source_combo.currentIndexChanged.connect(self.on_source_changed)
        form_layout.addRow("Signal d'entrée :", self.source_combo)

        self.gain_spin = QDoubleSpinBox()
        self.gain_spin.setRange(-100000.0, 100000.0)
        self.gain_spin.setValue(node.params.get("gain", 1.0))
        self.gain_spin.valueChanged.connect(self.on_param_modified)
        form_layout.addRow("Gain k :", self.gain_spin)

        self.offset_spin = QDoubleSpinBox()
        self.offset_spin.setRange(-100000.0, 100000.0)
        self.offset_spin.setValue(node.params.get("offset", 0.0))
        self.offset_spin.setSuffix(" V")
        self.offset_spin.valueChanged.connect(self.on_param_modified)
        form_layout.addRow("Offset V :", self.offset_spin)

        layout.addWidget(form_group)

        status_group = QGroupBox("État du Nœud")
        status_layout = QVBoxLayout(status_group)
        self.status_label = QLabel()
        self.update_status_label()
        status_layout.addWidget(self.status_label)

        self.btn_recalc = QPushButton("🔄 Recalculer le gain")
        self.btn_recalc.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; padding: 6px;")
        self.btn_recalc.clicked.connect(self.on_recalc_clicked)
        status_layout.addWidget(self.btn_recalc)

        layout.addWidget(status_group)

        view_group = QGroupBox("Visualisation du Pipeline")
        view_layout = QVBoxLayout(view_group)

        self.btn_graph = QPushButton("📈 Voir le graphique (Entrée vs Amplifié)")
        self.btn_graph.setStyleSheet("padding: 5px;")
        self.btn_graph.clicked.connect(lambda: self.on_view_graph_cb(self.node) if self.on_view_graph_cb else None)
        view_layout.addWidget(self.btn_graph)

        self.btn_table = QPushButton("📊 Voir le tableau pipeline (NumPy)")
        self.btn_table.setStyleSheet("padding: 5px;")
        self.btn_table.clicked.connect(lambda: self.on_view_table_cb(self.node) if self.on_view_table_cb else None)
        view_layout.addWidget(self.btn_table)

        self.btn_export_csv = QPushButton("💾 Exporter les données (CSV)...")
        self.btn_export_csv.setStyleSheet("padding: 5px; font-weight: bold;")
        self.btn_export_csv.clicked.connect(lambda: self.on_export_csv_cb(self.node) if self.on_export_csv_cb else None)
        view_layout.addWidget(self.btn_export_csv)

        layout.addWidget(view_group)

        self.btn_delete = QPushButton("🗑️ Supprimer ce nœud")
        self.btn_delete.setStyleSheet("background-color: #D32F2F; color: white; font-weight: bold; padding: 6px; margin-top: 10px;")
        self.btn_delete.clicked.connect(lambda: self.on_delete_cb(self.node) if self.on_delete_cb else None)
        layout.addWidget(self.btn_delete)

        layout.addStretch()

    def update_source_combo(self):
        self.source_combo.blockSignals(True)
        self.source_combo.clear()
        self.source_combo.addItem("Aucune connexion", None)

        selected_idx = 0
        for idx, src in enumerate(self.available_sources):
            self.source_combo.addItem(f"Entrée : {src.params['name']}", src)
            if self.node.input_node == src:
                selected_idx = idx + 1

        self.source_combo.setCurrentIndex(selected_idx)
        self.source_combo.blockSignals(False)

    def on_source_changed(self):
        selected_src = self.source_combo.currentData()
        if self.on_connect_cb:
            self.on_connect_cb(selected_src, self.node)
        self.on_param_modified()

    def update_status_label(self):
        if self.node.is_dirty:
            self.status_label.setText("⚠️ Données non à jour (Paramètres modifiés)")
            self.status_label.setStyleSheet("color: #FF9800; font-weight: bold;")
        else:
            self.status_label.setText("✅ Signal amplifié à jour")
            self.status_label.setStyleSheet("color: #4CAF50; font-weight: bold;")

    def on_param_modified(self):
        self.node.params["name"] = self.name_edit.text()
        self.node.params["gain"] = self.gain_spin.value()
        self.node.params["offset"] = self.offset_spin.value()
        self.node.mark_dirty()
        self.update_status_label()
        if self.on_recalculate_cb:
            self.on_recalculate_cb(self.node, executed=False)

    def on_recalc_clicked(self):
        self.node.recalculate()
        self.update_status_label()
        if self.on_recalculate_cb:
            self.on_recalculate_cb(self.node, executed=True)




class InversionParamWidget(QWidget):
    """Formulaire de réglage des paramètres de l'Inversion (1/x)."""
    def __init__(self, node: InversionNode, available_sources=None, on_recalculate_cb=None, on_connect_cb=None, on_view_graph_cb=None, on_view_table_cb=None, on_export_csv_cb=None, on_delete_cb=None):
        super().__init__()
        self.node = node
        self.available_sources = available_sources or []
        self.on_recalculate_cb = on_recalculate_cb
        self.on_connect_cb = on_connect_cb
        self.on_view_graph_cb = on_view_graph_cb
        self.on_view_table_cb = on_view_table_cb
        self.on_export_csv_cb = on_export_csv_cb
        self.on_delete_cb = on_delete_cb

        layout = QVBoxLayout(self)

        form_group = QGroupBox("Paramètres d'Inversion (1/x)")
        form_layout = QFormLayout(form_group)

        self.name_edit = QLineEdit(node.params["name"])
        self.name_edit.textChanged.connect(self.on_param_modified)
        form_layout.addRow("Nom :", self.name_edit)

        self.source_combo = QComboBox()
        self.update_source_combo()
        self.source_combo.currentIndexChanged.connect(self.on_source_changed)
        form_layout.addRow("Signal d'entrée :", self.source_combo)

        layout.addWidget(form_group)

        status_group = QGroupBox("État du Nœud")
        status_layout = QVBoxLayout(status_group)
        self.status_label = QLabel()
        self.update_status_label()
        status_layout.addWidget(self.status_label)

        self.btn_recalc = QPushButton("🔄 Recalculer l'inversion")
        self.btn_recalc.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; padding: 6px;")
        self.btn_recalc.clicked.connect(self.on_recalc_clicked)
        status_layout.addWidget(self.btn_recalc)

        layout.addWidget(status_group)

        view_group = QGroupBox("Visualisation du Pipeline")
        view_layout = QVBoxLayout(view_group)

        self.btn_graph = QPushButton("📈 Voir le graphique (Entrée vs Inversé)")
        self.btn_graph.setStyleSheet("padding: 5px;")
        self.btn_graph.clicked.connect(lambda: self.on_view_graph_cb(self.node) if self.on_view_graph_cb else None)
        view_layout.addWidget(self.btn_graph)

        self.btn_table = QPushButton("📊 Voir le tableau pipeline (NumPy)")
        self.btn_table.setStyleSheet("padding: 5px;")
        self.btn_table.clicked.connect(lambda: self.on_view_table_cb(self.node) if self.on_view_table_cb else None)
        view_layout.addWidget(self.btn_table)

        self.btn_export_csv = QPushButton("💾 Exporter les données (CSV)...")
        self.btn_export_csv.setStyleSheet("padding: 5px; font-weight: bold;")
        self.btn_export_csv.clicked.connect(lambda: self.on_export_csv_cb(self.node) if self.on_export_csv_cb else None)
        view_layout.addWidget(self.btn_export_csv)

        layout.addWidget(view_group)

        self.btn_delete = QPushButton("🗑️ Supprimer ce nœud")
        self.btn_delete.setStyleSheet("background-color: #D32F2F; color: white; font-weight: bold; padding: 6px; margin-top: 10px;")
        self.btn_delete.clicked.connect(lambda: self.on_delete_cb(self.node) if self.on_delete_cb else None)
        layout.addWidget(self.btn_delete)

        layout.addStretch()

    def update_source_combo(self):
        self.source_combo.blockSignals(True)
        self.source_combo.clear()
        self.source_combo.addItem("Aucune connexion", None)

        selected_idx = 0
        for idx, src in enumerate(self.available_sources):
            self.source_combo.addItem(f"Entrée : {src.params['name']}", src)
            if self.node.input_node == src:
                selected_idx = idx + 1

        self.source_combo.setCurrentIndex(selected_idx)
        self.source_combo.blockSignals(False)

    def on_source_changed(self):
        selected_src = self.source_combo.currentData()
        if self.on_connect_cb:
            self.on_connect_cb(selected_src, self.node)
        self.on_param_modified()

    def update_status_label(self):
        if self.node.is_dirty:
            self.status_label.setText("⚠️ Données non à jour (Paramètres modifiés)")
            self.status_label.setStyleSheet("color: #FF9800; font-weight: bold;")
        else:
            self.status_label.setText("✅ Inversion à jour")
            self.status_label.setStyleSheet("color: #4CAF50; font-weight: bold;")

    def on_param_modified(self):
        self.node.params["name"] = self.name_edit.text()
        self.node.mark_dirty()
        self.update_status_label()
        if self.on_recalculate_cb:
            self.on_recalculate_cb(self.node, executed=False)

    def on_recalc_clicked(self):
        self.node.recalculate()
        self.update_status_label()
        if self.on_recalculate_cb:
            self.on_recalculate_cb(self.node, executed=True)


class AbsParamWidget(QWidget):
    """Formulaire de réglage des paramètres de la Valeur Absolue (|x|)."""
    def __init__(self, node: AbsNode, available_sources=None, on_recalculate_cb=None, on_connect_cb=None, on_view_graph_cb=None, on_view_table_cb=None, on_export_csv_cb=None, on_delete_cb=None):
        super().__init__()
        self.node = node
        self.available_sources = available_sources or []
        self.on_recalculate_cb = on_recalculate_cb
        self.on_connect_cb = on_connect_cb
        self.on_view_graph_cb = on_view_graph_cb
        self.on_view_table_cb = on_view_table_cb
        self.on_export_csv_cb = on_export_csv_cb
        self.on_delete_cb = on_delete_cb

        layout = QVBoxLayout(self)

        form_group = QGroupBox("Paramètres de la Valeur Absolue (|x|)")
        form_layout = QFormLayout(form_group)

        self.name_edit = QLineEdit(node.params["name"])
        self.name_edit.textChanged.connect(self.on_param_modified)
        form_layout.addRow("Nom :", self.name_edit)

        self.source_combo = QComboBox()
        self.update_source_combo()
        self.source_combo.currentIndexChanged.connect(self.on_source_changed)
        form_layout.addRow("Signal d'entrée :", self.source_combo)

        layout.addWidget(form_group)

        status_group = QGroupBox("État du Nœud")
        status_layout = QVBoxLayout(status_group)
        self.status_label = QLabel()
        self.update_status_label()
        status_layout.addWidget(self.status_label)

        self.btn_recalc = QPushButton("🔄 Recalculer la valeur absolue")
        self.btn_recalc.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; padding: 6px;")
        self.btn_recalc.clicked.connect(self.on_recalc_clicked)
        status_layout.addWidget(self.btn_recalc)

        layout.addWidget(status_group)

        view_group = QGroupBox("Visualisation du Pipeline")
        view_layout = QVBoxLayout(view_group)

        self.btn_graph = QPushButton("📈 Voir le graphique (Entrée vs Absolue)")
        self.btn_graph.setStyleSheet("padding: 5px;")
        self.btn_graph.clicked.connect(lambda: self.on_view_graph_cb(self.node) if self.on_view_graph_cb else None)
        view_layout.addWidget(self.btn_graph)

        self.btn_table = QPushButton("📊 Voir le tableau pipeline (NumPy)")
        self.btn_table.setStyleSheet("padding: 5px;")
        self.btn_table.clicked.connect(lambda: self.on_view_table_cb(self.node) if self.on_view_table_cb else None)
        view_layout.addWidget(self.btn_table)

        self.btn_export_csv = QPushButton("💾 Exporter les données (CSV)...")
        self.btn_export_csv.setStyleSheet("padding: 5px; font-weight: bold;")
        self.btn_export_csv.clicked.connect(lambda: self.on_export_csv_cb(self.node) if self.on_export_csv_cb else None)
        view_layout.addWidget(self.btn_export_csv)

        layout.addWidget(view_group)

        self.btn_delete = QPushButton("🗑️ Supprimer ce nœud")
        self.btn_delete.setStyleSheet("background-color: #D32F2F; color: white; font-weight: bold; padding: 6px; margin-top: 10px;")
        self.btn_delete.clicked.connect(lambda: self.on_delete_cb(self.node) if self.on_delete_cb else None)
        layout.addWidget(self.btn_delete)

        layout.addStretch()

    def update_source_combo(self):
        self.source_combo.blockSignals(True)
        self.source_combo.clear()
        self.source_combo.addItem("Aucune connexion", None)

        selected_idx = 0
        for idx, src in enumerate(self.available_sources):
            self.source_combo.addItem(f"Entrée : {src.params['name']}", src)
            if self.node.input_node == src:
                selected_idx = idx + 1

        self.source_combo.setCurrentIndex(selected_idx)
        self.source_combo.blockSignals(False)

    def on_source_changed(self):
        selected_src = self.source_combo.currentData()
        if self.on_connect_cb:
            self.on_connect_cb(selected_src, self.node)
        self.on_param_modified()

    def update_status_label(self):
        if self.node.is_dirty:
            self.status_label.setText("⚠️ Données non à jour (Paramètres modifiés)")
            self.status_label.setStyleSheet("color: #FF9800; font-weight: bold;")
        else:
            self.status_label.setText("✅ Valeur absolue à jour")
            self.status_label.setStyleSheet("color: #4CAF50; font-weight: bold;")

    def on_param_modified(self):
        self.node.params["name"] = self.name_edit.text()
        self.node.mark_dirty()
        self.update_status_label()
        if self.on_recalculate_cb:
            self.on_recalculate_cb(self.node, executed=False)

    def on_recalc_clicked(self):
        self.node.recalculate()
        self.update_status_label()
        if self.on_recalculate_cb:
            self.on_recalculate_cb(self.node, executed=True)


class LogParamWidget(QWidget):
    """Formulaire de réglage des paramètres du Logarithme."""
    def __init__(self, node: LogNode, available_sources=None, on_recalculate_cb=None, on_connect_cb=None, on_view_graph_cb=None, on_view_table_cb=None, on_export_csv_cb=None, on_delete_cb=None):
        super().__init__()
        self.node = node
        self.available_sources = available_sources or []
        self.on_recalculate_cb = on_recalculate_cb
        self.on_connect_cb = on_connect_cb
        self.on_view_graph_cb = on_view_graph_cb
        self.on_view_table_cb = on_view_table_cb
        self.on_export_csv_cb = on_export_csv_cb
        self.on_delete_cb = on_delete_cb

        layout = QVBoxLayout(self)

        form_group = QGroupBox("Paramètres du Logarithme")
        form_layout = QFormLayout(form_group)

        self.name_edit = QLineEdit(node.params["name"])
        self.name_edit.textChanged.connect(self.on_param_modified)
        form_layout.addRow("Nom :", self.name_edit)

        self.source_combo = QComboBox()
        self.update_source_combo()
        self.source_combo.currentIndexChanged.connect(self.on_source_changed)
        form_layout.addRow("Signal d'entrée :", self.source_combo)

        self.base_combo = QComboBox()
        self.base_combo.addItems(MathOperatorsEngine.LOG_BASES)
        self.base_combo.setCurrentText(node.params.get("base", "log10 (base 10)"))
        self.base_combo.currentTextChanged.connect(self.on_param_modified)
        form_layout.addRow("Base logarithme :", self.base_combo)

        layout.addWidget(form_group)

        status_group = QGroupBox("État du Nœud")
        status_layout = QVBoxLayout(status_group)
        self.status_label = QLabel()
        self.update_status_label()
        status_layout.addWidget(self.status_label)

        self.btn_recalc = QPushButton("🔄 Recalculer le logarithme")
        self.btn_recalc.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; padding: 6px;")
        self.btn_recalc.clicked.connect(self.on_recalc_clicked)
        status_layout.addWidget(self.btn_recalc)

        layout.addWidget(status_group)

        view_group = QGroupBox("Visualisation du Pipeline")
        view_layout = QVBoxLayout(view_group)

        self.btn_graph = QPushButton("📈 Voir le graphique (Entrée vs Logarithme)")
        self.btn_graph.setStyleSheet("padding: 5px;")
        self.btn_graph.clicked.connect(lambda: self.on_view_graph_cb(self.node) if self.on_view_graph_cb else None)
        view_layout.addWidget(self.btn_graph)

        self.btn_table = QPushButton("📊 Voir le tableau pipeline (NumPy)")
        self.btn_table.setStyleSheet("padding: 5px;")
        self.btn_table.clicked.connect(lambda: self.on_view_table_cb(self.node) if self.on_view_table_cb else None)
        view_layout.addWidget(self.btn_table)

        self.btn_export_csv = QPushButton("💾 Exporter les données (CSV)...")
        self.btn_export_csv.setStyleSheet("padding: 5px; font-weight: bold;")
        self.btn_export_csv.clicked.connect(lambda: self.on_export_csv_cb(self.node) if self.on_export_csv_cb else None)
        view_layout.addWidget(self.btn_export_csv)

        layout.addWidget(view_group)

        self.btn_delete = QPushButton("🗑️ Supprimer ce nœud")
        self.btn_delete.setStyleSheet("background-color: #D32F2F; color: white; font-weight: bold; padding: 6px; margin-top: 10px;")
        self.btn_delete.clicked.connect(lambda: self.on_delete_cb(self.node) if self.on_delete_cb else None)
        layout.addWidget(self.btn_delete)

        layout.addStretch()

    def update_source_combo(self):
        self.source_combo.blockSignals(True)
        self.source_combo.clear()
        self.source_combo.addItem("Aucune connexion", None)

        selected_idx = 0
        for idx, src in enumerate(self.available_sources):
            self.source_combo.addItem(f"Entrée : {src.params['name']}", src)
            if self.node.input_node == src:
                selected_idx = idx + 1

        self.source_combo.setCurrentIndex(selected_idx)
        self.source_combo.blockSignals(False)

    def on_source_changed(self):
        selected_src = self.source_combo.currentData()
        if self.on_connect_cb:
            self.on_connect_cb(selected_src, self.node)
        self.on_param_modified()

    def update_status_label(self):
        if self.node.is_dirty:
            self.status_label.setText("⚠️ Données non à jour (Paramètres modifiés)")
            self.status_label.setStyleSheet("color: #FF9800; font-weight: bold;")
        else:
            self.status_label.setText("✅ Logarithme à jour")
            self.status_label.setStyleSheet("color: #4CAF50; font-weight: bold;")

    def on_param_modified(self):
        self.node.params["name"] = self.name_edit.text()
        self.node.params["base"] = self.base_combo.currentText()
        self.node.mark_dirty()
        self.update_status_label()
        if self.on_recalculate_cb:
            self.on_recalculate_cb(self.node, executed=False)

    def on_recalc_clicked(self):
        self.node.recalculate()
        self.update_status_label()
        if self.on_recalculate_cb:
            self.on_recalculate_cb(self.node, executed=True)


class ExpParamWidget(QWidget):
    """Formulaire de réglage des paramètres de l'Exponentielle."""
    def __init__(self, node: ExpNode, available_sources=None, on_recalculate_cb=None, on_connect_cb=None, on_view_graph_cb=None, on_view_table_cb=None, on_export_csv_cb=None, on_delete_cb=None):
        super().__init__()
        self.node = node
        self.available_sources = available_sources or []
        self.on_recalculate_cb = on_recalculate_cb
        self.on_connect_cb = on_connect_cb
        self.on_view_graph_cb = on_view_graph_cb
        self.on_view_table_cb = on_view_table_cb
        self.on_export_csv_cb = on_export_csv_cb
        self.on_delete_cb = on_delete_cb

        layout = QVBoxLayout(self)

        form_group = QGroupBox("Paramètres de l'Exponentielle")
        form_layout = QFormLayout(form_group)

        self.name_edit = QLineEdit(node.params["name"])
        self.name_edit.textChanged.connect(self.on_param_modified)
        form_layout.addRow("Nom :", self.name_edit)

        self.source_combo = QComboBox()
        self.update_source_combo()
        self.source_combo.currentIndexChanged.connect(self.on_source_changed)
        form_layout.addRow("Signal d'entrée :", self.source_combo)

        layout.addWidget(form_group)

        status_group = QGroupBox("État du Nœud")
        status_layout = QVBoxLayout(status_group)
        self.status_label = QLabel()
        self.update_status_label()
        status_layout.addWidget(self.status_label)

        self.btn_recalc = QPushButton("🔄 Recalculer l'exponentielle")
        self.btn_recalc.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; padding: 6px;")
        self.btn_recalc.clicked.connect(self.on_recalc_clicked)
        status_layout.addWidget(self.btn_recalc)

        layout.addWidget(status_group)

        view_group = QGroupBox("Visualisation du Pipeline")
        view_layout = QVBoxLayout(view_group)

        self.btn_graph = QPushButton("📈 Voir le graphique (Entrée vs Exponentielle)")
        self.btn_graph.setStyleSheet("padding: 5px;")
        self.btn_graph.clicked.connect(lambda: self.on_view_graph_cb(self.node) if self.on_view_graph_cb else None)
        view_layout.addWidget(self.btn_graph)

        self.btn_table = QPushButton("📊 Voir le tableau pipeline (NumPy)")
        self.btn_table.setStyleSheet("padding: 5px;")
        self.btn_table.clicked.connect(lambda: self.on_view_table_cb(self.node) if self.on_view_table_cb else None)
        view_layout.addWidget(self.btn_table)

        self.btn_export_csv = QPushButton("💾 Exporter les données (CSV)...")
        self.btn_export_csv.setStyleSheet("padding: 5px; font-weight: bold;")
        self.btn_export_csv.clicked.connect(lambda: self.on_export_csv_cb(self.node) if self.on_export_csv_cb else None)
        view_layout.addWidget(self.btn_export_csv)

        layout.addWidget(view_group)

        self.btn_delete = QPushButton("🗑️ Supprimer ce nœud")
        self.btn_delete.setStyleSheet("background-color: #D32F2F; color: white; font-weight: bold; padding: 6px; margin-top: 10px;")
        self.btn_delete.clicked.connect(lambda: self.on_delete_cb(self.node) if self.on_delete_cb else None)
        layout.addWidget(self.btn_delete)

        layout.addStretch()

    def update_source_combo(self):
        self.source_combo.blockSignals(True)
        self.source_combo.clear()
        self.source_combo.addItem("Aucune connexion", None)

        selected_idx = 0
        for idx, src in enumerate(self.available_sources):
            self.source_combo.addItem(f"Entrée : {src.params['name']}", src)
            if self.node.input_node == src:
                selected_idx = idx + 1

        self.source_combo.setCurrentIndex(selected_idx)
        self.source_combo.blockSignals(False)

    def on_source_changed(self):
        selected_src = self.source_combo.currentData()
        if self.on_connect_cb:
            self.on_connect_cb(selected_src, self.node)
        self.on_param_modified()

    def update_status_label(self):
        if self.node.is_dirty:
            self.status_label.setText("⚠️ Données non à jour (Paramètres modifiés)")
            self.status_label.setStyleSheet("color: #FF9800; font-weight: bold;")
        else:
            self.status_label.setText("✅ Exponentielle à jour")
            self.status_label.setStyleSheet("color: #4CAF50; font-weight: bold;")

    def on_param_modified(self):
        self.node.params["name"] = self.name_edit.text()
        self.node.mark_dirty()
        self.update_status_label()
        if self.on_recalculate_cb:
            self.on_recalculate_cb(self.node, executed=False)

    def on_recalc_clicked(self):
        self.node.recalculate()
        self.update_status_label()
        if self.on_recalculate_cb:
            self.on_recalculate_cb(self.node, executed=True)


class AdditionParamWidget(QWidget):
    """Formulaire de réglage des paramètres de l'Addition Multivariable (A + B)."""
    def __init__(self, node: AdditionNode, available_sources=None, on_recalculate_cb=None, on_connect_cb=None, on_view_graph_cb=None, on_view_table_cb=None, on_export_csv_cb=None, on_delete_cb=None):
        super().__init__()
        self.node = node
        self.available_sources = available_sources or []
        self.on_recalculate_cb = on_recalculate_cb
        self.on_connect_cb = on_connect_cb
        self.on_view_graph_cb = on_view_graph_cb
        self.on_view_table_cb = on_view_table_cb
        self.on_export_csv_cb = on_export_csv_cb
        self.on_delete_cb = on_delete_cb

        layout = QVBoxLayout(self)

        form_group = QGroupBox("Paramètres de l'Addition (A + B)")
        form_layout = QFormLayout(form_group)

        self.name_edit = QLineEdit(node.params["name"])
        self.name_edit.textChanged.connect(self.on_param_modified)
        form_layout.addRow("Nom :", self.name_edit)

        # Source A
        self.source_a_combo = QComboBox()
        form_layout.addRow("Signal A (Entrée 1) :", self.source_a_combo)

        # Coef A
        self.coef_a_spin = QDoubleSpinBox()
        self.coef_a_spin.setRange(-1000.0, 1000.0)
        self.coef_a_spin.setValue(float(node.params.get("coef_a", 1.0)))
        self.coef_a_spin.setSingleStep(0.1)
        self.coef_a_spin.valueChanged.connect(self.on_param_modified)
        form_layout.addRow("Gain k_A :", self.coef_a_spin)

        # Source B
        self.source_b_combo = QComboBox()
        form_layout.addRow("Signal B (Entrée 2) :", self.source_b_combo)

        # Coef B
        self.coef_b_spin = QDoubleSpinBox()
        self.coef_b_spin.setRange(-1000.0, 1000.0)
        self.coef_b_spin.setValue(float(node.params.get("coef_b", 1.0)))
        self.coef_b_spin.setSingleStep(0.1)
        self.coef_b_spin.valueChanged.connect(self.on_param_modified)
        form_layout.addRow("Gain k_B :", self.coef_b_spin)

        self.update_source_combos()
        self.source_a_combo.currentIndexChanged.connect(self.on_source_a_changed)
        self.source_b_combo.currentIndexChanged.connect(self.on_source_b_changed)

        layout.addWidget(form_group)

        status_group = QGroupBox("État du Nœud")
        status_layout = QVBoxLayout(status_group)
        self.status_label = QLabel()
        self.update_status_label()
        status_layout.addWidget(self.status_label)

        self.btn_recalc = QPushButton("🔄 Recalculer l'addition")
        self.btn_recalc.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; padding: 6px;")
        self.btn_recalc.clicked.connect(self.on_recalc_clicked)
        status_layout.addWidget(self.btn_recalc)

        layout.addWidget(status_group)

        view_group = QGroupBox("Visualisation du Pipeline")
        view_layout = QVBoxLayout(view_group)

        self.btn_graph = QPushButton("📈 Voir le graphique (A, B et Somme)")
        self.btn_graph.setStyleSheet("padding: 5px;")
        self.btn_graph.clicked.connect(lambda: self.on_view_graph_cb(self.node) if self.on_view_graph_cb else None)
        view_layout.addWidget(self.btn_graph)

        self.btn_table = QPushButton("📊 Voir le tableau pipeline (NumPy)")
        self.btn_table.setStyleSheet("padding: 5px;")
        self.btn_table.clicked.connect(lambda: self.on_view_table_cb(self.node) if self.on_view_table_cb else None)
        view_layout.addWidget(self.btn_table)

        self.btn_export_csv = QPushButton("💾 Exporter les données (CSV)...")
        self.btn_export_csv.setStyleSheet("padding: 5px; font-weight: bold;")
        self.btn_export_csv.clicked.connect(lambda: self.on_export_csv_cb(self.node) if self.on_export_csv_cb else None)
        view_layout.addWidget(self.btn_export_csv)

        layout.addWidget(view_group)

        self.btn_delete = QPushButton("🗑️ Supprimer ce nœud")
        self.btn_delete.setStyleSheet("background-color: #D32F2F; color: white; font-weight: bold; padding: 6px; margin-top: 10px;")
        self.btn_delete.clicked.connect(lambda: self.on_delete_cb(self.node) if self.on_delete_cb else None)
        layout.addWidget(self.btn_delete)

        layout.addStretch()

    def update_source_combos(self):
        self.source_a_combo.blockSignals(True)
        self.source_a_combo.clear()
        self.source_a_combo.addItem("Aucune connexion", None)

        idx_a = 0
        for idx, src in enumerate(self.available_sources):
            self.source_a_combo.addItem(f"Signal A : {src.params['name']}", src)
            if self.node.input_node_a == src:
                idx_a = idx + 1
        self.source_a_combo.setCurrentIndex(idx_a)
        self.source_a_combo.blockSignals(False)

        self.source_b_combo.blockSignals(True)
        self.source_b_combo.clear()
        self.source_b_combo.addItem("Aucune connexion", None)

        idx_b = 0
        for idx, src in enumerate(self.available_sources):
            self.source_b_combo.addItem(f"Signal B : {src.params['name']}", src)
            if self.node.input_node_b == src:
                idx_b = idx + 1
        self.source_b_combo.setCurrentIndex(idx_b)
        self.source_b_combo.blockSignals(False)

    def on_source_a_changed(self):
        selected_src = self.source_a_combo.currentData()
        if self.on_connect_cb:
            self.on_connect_cb(selected_src, self.node, target_port="a")
        self.on_param_modified()

    def on_source_b_changed(self):
        selected_src = self.source_b_combo.currentData()
        if self.on_connect_cb:
            self.on_connect_cb(selected_src, self.node, target_port="b")
        self.on_param_modified()

    def update_status_label(self):
        if self.node.is_dirty:
            self.status_label.setText("⚠️ Données non à jour (Paramètres modifiés)")
            self.status_label.setStyleSheet("color: #FF9800; font-weight: bold;")
        else:
            self.status_label.setText("✅ Addition à jour")
            self.status_label.setStyleSheet("color: #4CAF50; font-weight: bold;")

    def on_param_modified(self):
        self.node.params["name"] = self.name_edit.text()
        self.node.params["coef_a"] = self.coef_a_spin.value()
        self.node.params["coef_b"] = self.coef_b_spin.value()

        self.node.mark_dirty()
        self.update_status_label()

        if self.on_recalculate_cb:
            self.on_recalculate_cb(self.node, executed=False)

    def on_recalc_clicked(self):
        self.node.recalculate()
        if "auto" in str(self.node.params.get("fundamental_mode", "")).lower():
            self.f0_spin.blockSignals(True)
            self.f0_spin.setValue(float(self.node.f0_detected))
            self.f0_spin.blockSignals(False)
        self.update_status_label()

        if self.on_recalculate_cb:
            self.on_recalculate_cb(self.node, executed=True)



class PowerParamWidget(QWidget):
    """Formulaire de réglage des paramètres de Puissance / Racine."""
    def __init__(self, node: PowerNode, available_sources=None, on_recalculate_cb=None, on_connect_cb=None, on_view_graph_cb=None, on_view_table_cb=None, on_export_csv_cb=None, on_delete_cb=None):
        super().__init__()
        self.node = node
        self.available_sources = available_sources or []
        self.on_recalculate_cb = on_recalculate_cb
        self.on_connect_cb = on_connect_cb
        self.on_view_graph_cb = on_view_graph_cb
        self.on_view_table_cb = on_view_table_cb
        self.on_export_csv_cb = on_export_csv_cb
        self.on_delete_cb = on_delete_cb

        layout = QVBoxLayout(self)

        form_group = QGroupBox("Paramètres de Puissance / Racine")
        form_layout = QFormLayout(form_group)

        self.name_edit = QLineEdit(node.params["name"])
        self.name_edit.textChanged.connect(self.on_param_modified)
        form_layout.addRow("Nom :", self.name_edit)

        self.source_combo = QComboBox()
        self.update_source_combo()
        self.source_combo.currentIndexChanged.connect(self.on_source_changed)
        form_layout.addRow("Signal d'entrée :", self.source_combo)

        self.mode_combo = QComboBox()
        self.mode_combo.addItems(MathOperatorsEngine.POWER_MODES)
        self.mode_combo.setCurrentText(node.params.get("mode", "Puissance xⁿ"))
        self.mode_combo.currentTextChanged.connect(self.on_param_modified)
        form_layout.addRow("Mode :", self.mode_combo)

        self.exp_spin = QDoubleSpinBox()
        self.exp_spin.setRange(-10.0, 10.0)
        self.exp_spin.setValue(node.params.get("exponent", 2.0))
        self.exp_spin.setSingleStep(0.5)
        self.exp_spin.valueChanged.connect(self.on_param_modified)
        form_layout.addRow("Exposant n :", self.exp_spin)

        layout.addWidget(form_group)

        status_group = QGroupBox("État du Nœud")
        status_layout = QVBoxLayout(status_group)
        self.status_label = QLabel()
        self.update_status_label()
        status_layout.addWidget(self.status_label)

        self.btn_recalc = QPushButton("🔄 Recalculer la puissance")
        self.btn_recalc.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; padding: 6px;")
        self.btn_recalc.clicked.connect(self.on_recalc_clicked)
        status_layout.addWidget(self.btn_recalc)

        layout.addWidget(status_group)

        view_group = QGroupBox("Visualisation du Pipeline")
        view_layout = QVBoxLayout(view_group)

        self.btn_graph = QPushButton("📈 Voir le graphique (Entrée vs Puissance)")
        self.btn_graph.setStyleSheet("padding: 5px;")
        self.btn_graph.clicked.connect(lambda: self.on_view_graph_cb(self.node) if self.on_view_graph_cb else None)
        view_layout.addWidget(self.btn_graph)

        self.btn_table = QPushButton("📊 Voir le tableau pipeline (NumPy)")
        self.btn_table.setStyleSheet("padding: 5px;")
        self.btn_table.clicked.connect(lambda: self.on_view_table_cb(self.node) if self.on_view_table_cb else None)
        view_layout.addWidget(self.btn_table)

        self.btn_export_csv = QPushButton("💾 Exporter les données (CSV)...")
        self.btn_export_csv.setStyleSheet("padding: 5px; font-weight: bold;")
        self.btn_export_csv.clicked.connect(lambda: self.on_export_csv_cb(self.node) if self.on_export_csv_cb else None)
        view_layout.addWidget(self.btn_export_csv)

        layout.addWidget(view_group)

        self.btn_delete = QPushButton("🗑️ Supprimer ce nœud")
        self.btn_delete.setStyleSheet("background-color: #D32F2F; color: white; font-weight: bold; padding: 6px; margin-top: 10px;")
        self.btn_delete.clicked.connect(lambda: self.on_delete_cb(self.node) if self.on_delete_cb else None)
        layout.addWidget(self.btn_delete)

        layout.addStretch()

    def update_source_combo(self):
        self.source_combo.blockSignals(True)
        self.source_combo.clear()
        self.source_combo.addItem("Aucune connexion", None)

        selected_idx = 0
        for idx, src in enumerate(self.available_sources):
            self.source_combo.addItem(f"Entrée : {src.params['name']}", src)
            if self.node.input_node == src:
                selected_idx = idx + 1

        self.source_combo.setCurrentIndex(selected_idx)
        self.source_combo.blockSignals(False)

    def on_source_changed(self):
        selected_src = self.source_combo.currentData()
        if self.on_connect_cb:
            self.on_connect_cb(selected_src, self.node)
        self.on_param_modified()

    def update_status_label(self):
        if self.node.is_dirty:
            self.status_label.setText("⚠️ Données non à jour (Paramètres modifiés)")
            self.status_label.setStyleSheet("color: #FF9800; font-weight: bold;")
        else:
            self.status_label.setText("✅ Puissance à jour")
            self.status_label.setStyleSheet("color: #4CAF50; font-weight: bold;")

    def on_param_modified(self):
        self.node.params["name"] = self.name_edit.text()
        self.node.params["mode"] = self.mode_combo.currentText()
        self.node.params["exponent"] = self.exp_spin.value()
        self.exp_spin.setEnabled("Puissance" in self.mode_combo.currentText())
        self.node.mark_dirty()
        self.update_status_label()
        if self.on_recalculate_cb:
            self.on_recalculate_cb(self.node, executed=False)

    def on_recalc_clicked(self):
        self.node.recalculate()
        self.update_status_label()
        if self.on_recalculate_cb:
            self.on_recalculate_cb(self.node, executed=True)



class NoiseParamWidget(QWidget):
    """Formulaire de réglage des paramètres de l'Injecteur de Bruit."""
    def __init__(self, node: NoiseNode, available_sources=None, on_recalculate_cb=None, on_connect_cb=None, on_view_graph_cb=None, on_view_table_cb=None, on_export_csv_cb=None, on_delete_cb=None):
        super().__init__()
        self.node = node
        self.available_sources = available_sources or []
        self.on_recalculate_cb = on_recalculate_cb
        self.on_connect_cb = on_connect_cb
        self.on_view_graph_cb = on_view_graph_cb
        self.on_view_table_cb = on_view_table_cb
        self.on_export_csv_cb = on_export_csv_cb
        self.on_delete_cb = on_delete_cb

        layout = QVBoxLayout(self)

        form_group = QGroupBox("Paramètres de l'Injecteur de Bruit")
        form_layout = QFormLayout(form_group)

        self.name_edit = QLineEdit(node.params["name"])
        self.name_edit.textChanged.connect(self.on_param_modified)
        form_layout.addRow("Nom :", self.name_edit)

        self.source_combo = QComboBox()
        self.update_source_combo()
        self.source_combo.currentIndexChanged.connect(self.on_source_changed)
        form_layout.addRow("Signal d'entrée :", self.source_combo)

        self.type_combo = QComboBox()
        self.type_combo.addItems(NoiseEngine.NOISE_TYPES)
        self.type_combo.setCurrentText(node.params.get("noise_type", "Bruit blanc gaussien"))
        self.type_combo.currentTextChanged.connect(self.on_param_modified)
        form_layout.addRow("Type de bruit :", self.type_combo)

        self.std_spin = QDoubleSpinBox()
        self.std_spin.setRange(0.0001, 1000.0)
        self.std_spin.setValue(float(node.params.get("std_dev", 0.1)))
        self.std_spin.setSingleStep(0.05)
        self.std_spin.valueChanged.connect(self.on_param_modified)
        form_layout.addRow("Écart-type σ / Niveau :", self.std_spin)

        self.spike_prob_spin = QDoubleSpinBox()
        self.spike_prob_spin.setRange(0.001, 1.0)
        self.spike_prob_spin.setValue(float(node.params.get("spike_prob", 0.01)))
        self.spike_prob_spin.setSingleStep(0.01)
        self.spike_prob_spin.valueChanged.connect(self.on_param_modified)
        form_layout.addRow("Probabilité Spikes (0-1) :", self.spike_prob_spin)

        self.spike_amp_spin = QDoubleSpinBox()
        self.spike_amp_spin.setRange(0.0, 1000.0)
        self.spike_amp_spin.setValue(float(node.params.get("spike_amp", 1.0)))
        self.spike_amp_spin.setSuffix(" V")
        self.spike_amp_spin.valueChanged.connect(self.on_param_modified)
        form_layout.addRow("Amplitude Spikes :", self.spike_amp_spin)

        layout.addWidget(form_group)

        status_group = QGroupBox("État du Nœud")
        status_layout = QVBoxLayout(status_group)
        self.status_label = QLabel()
        self.update_status_label()
        status_layout.addWidget(self.status_label)

        self.btn_recalc = QPushButton("🔄 Recalculer le bruit")
        self.btn_recalc.setStyleSheet("background-color: #FF9800; color: white; font-weight: bold; padding: 6px;")
        self.btn_recalc.clicked.connect(self.on_recalc_clicked)
        status_layout.addWidget(self.btn_recalc)

        layout.addWidget(status_group)

        view_group = QGroupBox("Visualisation du Pipeline")
        view_layout = QVBoxLayout(view_group)

        self.btn_graph = QPushButton("📈 Voir le graphique (Entrée vs Bruité)")
        self.btn_graph.setStyleSheet("padding: 5px;")
        self.btn_graph.clicked.connect(lambda: self.on_view_graph_cb(self.node) if self.on_view_graph_cb else None)
        view_layout.addWidget(self.btn_graph)

        self.btn_table = QPushButton("📊 Voir le tableau pipeline (NumPy)")
        self.btn_table.setStyleSheet("padding: 5px;")
        self.btn_table.clicked.connect(lambda: self.on_view_table_cb(self.node) if self.on_view_table_cb else None)
        view_layout.addWidget(self.btn_table)

        self.btn_export_csv = QPushButton("💾 Exporter les données (CSV)...")
        self.btn_export_csv.setStyleSheet("padding: 5px; font-weight: bold;")
        self.btn_export_csv.clicked.connect(lambda: self.on_export_csv_cb(self.node) if self.on_export_csv_cb else None)
        view_layout.addWidget(self.btn_export_csv)

        layout.addWidget(view_group)

        self.btn_delete = QPushButton("🗑️ Supprimer ce nœud")
        self.btn_delete.setStyleSheet("background-color: #D32F2F; color: white; font-weight: bold; padding: 6px; margin-top: 10px;")
        self.btn_delete.clicked.connect(lambda: self.on_delete_cb(self.node) if self.on_delete_cb else None)
        layout.addWidget(self.btn_delete)

        layout.addStretch()

    def update_source_combo(self):
        self.source_combo.blockSignals(True)
        self.source_combo.clear()
        self.source_combo.addItem("Aucune connexion", None)

        selected_idx = 0
        for idx, src in enumerate(self.available_sources):
            self.source_combo.addItem(f"Entrée : {src.params['name']}", src)
            if self.node.input_node == src:
                selected_idx = idx + 1

        self.source_combo.setCurrentIndex(selected_idx)
        self.source_combo.blockSignals(False)

    def on_source_changed(self):
        selected_src = self.source_combo.currentData()
        if self.on_connect_cb:
            self.on_connect_cb(selected_src, self.node)
        self.on_param_modified()

    def update_status_label(self):
        if self.node.is_dirty:
            self.status_label.setText("⚠️ Données non à jour (Paramètres modifiés)")
            self.status_label.setStyleSheet("color: #FF9800; font-weight: bold;")
        else:
            self.status_label.setText("✅ Signal bruité à jour")
            self.status_label.setStyleSheet("color: #4CAF50; font-weight: bold;")

    def on_param_modified(self):
        self.node.params["name"] = self.name_edit.text()
        self.node.params["noise_type"] = self.type_combo.currentText()
        self.node.params["std_dev"] = self.std_spin.value()
        self.node.params["spike_prob"] = self.spike_prob_spin.value()
        self.node.params["spike_amp"] = self.spike_amp_spin.value()
        self.node.mark_dirty()
        self.update_status_label()
        if self.on_recalculate_cb:
            self.on_recalculate_cb(self.node, executed=False)

    def on_recalc_clicked(self):
        self.node.recalculate()
        self.update_status_label()
        if self.on_recalculate_cb:
            self.on_recalculate_cb(self.node, executed=True)


class ResampleParamWidget(QWidget):
    """Formulaire de réglage des paramètres du Rééchantillonnage."""
    def __init__(self, node: ResampleNode, available_sources=None, on_recalculate_cb=None, on_connect_cb=None, on_view_graph_cb=None, on_view_table_cb=None, on_export_csv_cb=None, on_delete_cb=None):
        super().__init__()
        self.node = node
        self.available_sources = available_sources or []
        self.on_recalculate_cb = on_recalculate_cb
        self.on_connect_cb = on_connect_cb
        self.on_view_graph_cb = on_view_graph_cb
        self.on_view_table_cb = on_view_table_cb
        self.on_export_csv_cb = on_export_csv_cb
        self.on_delete_cb = on_delete_cb

        layout = QVBoxLayout(self)

        form_group = QGroupBox("Paramètres du Rééchantillonnage")
        form_layout = QFormLayout(form_group)

        self.name_edit = QLineEdit(node.params["name"])
        self.name_edit.textChanged.connect(self.on_param_modified)
        form_layout.addRow("Nom :", self.name_edit)

        self.source_combo = QComboBox()
        self.update_source_combo()
        self.source_combo.currentIndexChanged.connect(self.on_source_changed)
        form_layout.addRow("Signal d'entrée :", self.source_combo)

        self.rate_spin = QDoubleSpinBox()
        self.rate_spin.setRange(0.1, 1000000.0)
        self.rate_spin.setValue(float(node.params.get("target_fs", 500.0)))
        self.rate_spin.setSuffix(" Hz")
        self.rate_spin.valueChanged.connect(self.on_param_modified)
        form_layout.addRow("Nouvelle Fréq. Échantillonage (Fs) :", self.rate_spin)

        self.aa_check = QCheckBox("Activer le filtre anti-repliement (Anti-Aliasing)")
        self.aa_check.setChecked(bool(node.params.get("anti_aliasing", True)))
        self.aa_check.stateChanged.connect(self.on_param_modified)
        form_layout.addRow("", self.aa_check)

        layout.addWidget(form_group)

        status_group = QGroupBox("État du Nœud")
        status_layout = QVBoxLayout(status_group)
        self.status_label = QLabel()
        self.update_status_label()
        status_layout.addWidget(self.status_label)

        self.btn_recalc = QPushButton("🔄 Recalculer le rééchantillonnage")
        self.btn_recalc.setStyleSheet("background-color: #0288D1; color: white; font-weight: bold; padding: 6px;")
        self.btn_recalc.clicked.connect(self.on_recalc_clicked)
        status_layout.addWidget(self.btn_recalc)

        layout.addWidget(status_group)

        view_group = QGroupBox("Visualisation du Pipeline")
        view_layout = QVBoxLayout(view_group)

        self.btn_graph = QPushButton("📈 Voir le graphique (Entrée vs Rééchantillonné)")
        self.btn_graph.setStyleSheet("padding: 5px;")
        self.btn_graph.clicked.connect(lambda: self.on_view_graph_cb(self.node) if self.on_view_graph_cb else None)
        view_layout.addWidget(self.btn_graph)

        self.btn_table = QPushButton("📊 Voir le tableau pipeline (NumPy)")
        self.btn_table.setStyleSheet("padding: 5px;")
        self.btn_table.clicked.connect(lambda: self.on_view_table_cb(self.node) if self.on_view_table_cb else None)
        view_layout.addWidget(self.btn_table)

        self.btn_export_csv = QPushButton("💾 Exporter les données (CSV)...")
        self.btn_export_csv.setStyleSheet("padding: 5px; font-weight: bold;")
        self.btn_export_csv.clicked.connect(lambda: self.on_export_csv_cb(self.node) if self.on_export_csv_cb else None)
        view_layout.addWidget(self.btn_export_csv)

        layout.addWidget(view_group)

        self.btn_delete = QPushButton("🗑️ Supprimer ce nœud")
        self.btn_delete.setStyleSheet("background-color: #D32F2F; color: white; font-weight: bold; padding: 6px; margin-top: 10px;")
        self.btn_delete.clicked.connect(lambda: self.on_delete_cb(self.node) if self.on_delete_cb else None)
        layout.addWidget(self.btn_delete)

        layout.addStretch()

    def update_source_combo(self):
        self.source_combo.blockSignals(True)
        self.source_combo.clear()
        self.source_combo.addItem("Aucune connexion", None)

        selected_idx = 0
        for idx, src in enumerate(self.available_sources):
            self.source_combo.addItem(f"Entrée : {src.params['name']}", src)
            if self.node.input_node == src:
                selected_idx = idx + 1

        self.source_combo.setCurrentIndex(selected_idx)
        self.source_combo.blockSignals(False)

    def on_source_changed(self):
        selected_src = self.source_combo.currentData()
        if self.on_connect_cb:
            self.on_connect_cb(selected_src, self.node)
        self.on_param_modified()

    def update_status_label(self):
        if self.node.is_dirty:
            self.status_label.setText("⚠️ Données non à jour (Paramètres modifiés)")
            self.status_label.setStyleSheet("color: #FF9800; font-weight: bold;")
        else:
            self.status_label.setText("✅ Signal rééchantillonné à jour")
            self.status_label.setStyleSheet("color: #4CAF50; font-weight: bold;")

    def on_param_modified(self):
        self.node.params["name"] = self.name_edit.text()
        self.node.params["target_fs"] = self.rate_spin.value()
        self.node.params["anti_aliasing"] = self.aa_check.isChecked()
        self.node.mark_dirty()
        self.update_status_label()
        if self.on_recalculate_cb:
            self.on_recalculate_cb(self.node, executed=False)

    def on_recalc_clicked(self):
        self.node.recalculate()
        self.update_status_label()
        if self.on_recalculate_cb:
            self.on_recalculate_cb(self.node, executed=True)


class InterpolationParamWidget(QWidget):
    """Formulaire de réglage des paramètres de l'Interpolation & Extrapolation."""
    def __init__(self, node: InterpolationNode, available_sources=None, on_recalculate_cb=None, on_connect_cb=None, on_view_graph_cb=None, on_view_table_cb=None, on_export_csv_cb=None, on_delete_cb=None):
        super().__init__()
        self.node = node
        self.available_sources = available_sources or []
        self.on_recalculate_cb = on_recalculate_cb
        self.on_connect_cb = on_connect_cb
        self.on_view_graph_cb = on_view_graph_cb
        self.on_view_table_cb = on_view_table_cb
        self.on_export_csv_cb = on_export_csv_cb
        self.on_delete_cb = on_delete_cb

        layout = QVBoxLayout(self)

        form_group = QGroupBox("Paramètres de l'Interpolation / Extrapolation")
        form_layout = QFormLayout(form_group)

        self.name_edit = QLineEdit(node.params["name"])
        self.name_edit.textChanged.connect(self.on_param_modified)
        form_layout.addRow("Nom :", self.name_edit)

        self.source_combo = QComboBox()
        self.update_source_combo()
        self.source_combo.currentIndexChanged.connect(self.on_source_changed)
        form_layout.addRow("Signal d'entrée :", self.source_combo)

        self.rate_spin = QDoubleSpinBox()
        self.rate_spin.setRange(0.1, 1000000.0)
        self.rate_spin.setValue(float(node.params.get("target_fs", 1000.0)))
        self.rate_spin.setSuffix(" Hz")
        self.rate_spin.valueChanged.connect(self.on_param_modified)
        form_layout.addRow("Fréquence de sortie (Fs) :", self.rate_spin)

        self.method_combo = QComboBox()
        self.method_combo.addItems(SamplingConversionEngine.INTERP_METHODS)
        self.method_combo.setCurrentText(node.params.get("interp_method", "Linéaire"))
        self.method_combo.currentTextChanged.connect(self.on_param_modified)
        form_layout.addRow("Méthode d'interpolation :", self.method_combo)

        self.extrap_combo = QComboBox()
        self.extrap_combo.addItems(SamplingConversionEngine.EXTRAP_MODES)
        self.extrap_combo.setCurrentText(node.params.get("extrap_mode", "Maintien (Hold)"))
        self.extrap_combo.currentTextChanged.connect(self.on_param_modified)
        form_layout.addRow("Mode d'extrapolation :", self.extrap_combo)

        layout.addWidget(form_group)

        status_group = QGroupBox("État du Nœud")
        status_layout = QVBoxLayout(status_group)
        self.status_label = QLabel()
        self.update_status_label()
        status_layout.addWidget(self.status_label)

        self.btn_recalc = QPushButton("🔄 Recalculer l'interpolation")
        self.btn_recalc.setStyleSheet("background-color: #0288D1; color: white; font-weight: bold; padding: 6px;")
        self.btn_recalc.clicked.connect(self.on_recalc_clicked)
        status_layout.addWidget(self.btn_recalc)

        layout.addWidget(status_group)

        view_group = QGroupBox("Visualisation du Pipeline")
        view_layout = QVBoxLayout(view_group)

        self.btn_graph = QPushButton("📈 Voir le graphique (Entrée vs Interpolé)")
        self.btn_graph.setStyleSheet("padding: 5px;")
        self.btn_graph.clicked.connect(lambda: self.on_view_graph_cb(self.node) if self.on_view_graph_cb else None)
        view_layout.addWidget(self.btn_graph)

        self.btn_table = QPushButton("📊 Voir le tableau pipeline (NumPy)")
        self.btn_table.setStyleSheet("padding: 5px;")
        self.btn_table.clicked.connect(lambda: self.on_view_table_cb(self.node) if self.on_view_table_cb else None)
        view_layout.addWidget(self.btn_table)

        self.btn_export_csv = QPushButton("💾 Exporter les données (CSV)...")
        self.btn_export_csv.setStyleSheet("padding: 5px; font-weight: bold;")
        self.btn_export_csv.clicked.connect(lambda: self.on_export_csv_cb(self.node) if self.on_export_csv_cb else None)
        view_layout.addWidget(self.btn_export_csv)

        layout.addWidget(view_group)

        self.btn_delete = QPushButton("🗑️ Supprimer ce nœud")
        self.btn_delete.setStyleSheet("background-color: #D32F2F; color: white; font-weight: bold; padding: 6px; margin-top: 10px;")
        self.btn_delete.clicked.connect(lambda: self.on_delete_cb(self.node) if self.on_delete_cb else None)
        layout.addWidget(self.btn_delete)

        layout.addStretch()

    def update_source_combo(self):
        self.source_combo.blockSignals(True)
        self.source_combo.clear()
        self.source_combo.addItem("Aucune connexion", None)

        selected_idx = 0
        for idx, src in enumerate(self.available_sources):
            self.source_combo.addItem(f"Entrée : {src.params['name']}", src)
            if self.node.input_node == src:
                selected_idx = idx + 1

        self.source_combo.setCurrentIndex(selected_idx)
        self.source_combo.blockSignals(False)

    def on_source_changed(self):
        selected_src = self.source_combo.currentData()
        if self.on_connect_cb:
            self.on_connect_cb(selected_src, self.node)
        self.on_param_modified()

    def update_status_label(self):
        if self.node.is_dirty:
            self.status_label.setText("⚠️ Données non à jour (Paramètres modifiés)")
            self.status_label.setStyleSheet("color: #FF9800; font-weight: bold;")
        else:
            self.status_label.setText("✅ Signal interpolé à jour")
            self.status_label.setStyleSheet("color: #4CAF50; font-weight: bold;")

    def on_param_modified(self):
        self.node.params["name"] = self.name_edit.text()
        self.node.params["target_fs"] = self.rate_spin.value()
        self.node.params["interp_method"] = self.method_combo.currentText()
        self.node.params["extrap_mode"] = self.extrap_combo.currentText()
        self.node.mark_dirty()
        self.update_status_label()
        if self.on_recalculate_cb:
            self.on_recalculate_cb(self.node, executed=False)

    def on_recalc_clicked(self):
        self.node.recalculate()
        self.update_status_label()
        if self.on_recalculate_cb:
            self.on_recalculate_cb(self.node, executed=True)


class DACParamWidget(QWidget):
    """Formulaire de réglage des paramètres de la Simulation DAC."""
    def __init__(self, node: DACNode, available_sources=None, on_recalculate_cb=None, on_connect_cb=None, on_view_graph_cb=None, on_view_table_cb=None, on_export_csv_cb=None, on_delete_cb=None):
        super().__init__()
        self.node = node
        self.available_sources = available_sources or []
        self.on_recalculate_cb = on_recalculate_cb
        self.on_connect_cb = on_connect_cb
        self.on_view_graph_cb = on_view_graph_cb
        self.on_view_table_cb = on_view_table_cb
        self.on_export_csv_cb = on_export_csv_cb
        self.on_delete_cb = on_delete_cb

        layout = QVBoxLayout(self)

        form_group = QGroupBox("Paramètres de la Simulation DAC")
        form_layout = QFormLayout(form_group)

        self.name_edit = QLineEdit(node.params["name"])
        self.name_edit.textChanged.connect(self.on_param_modified)
        form_layout.addRow("Nom :", self.name_edit)

        self.source_combo = QComboBox()
        self.update_source_combo()
        self.source_combo.currentIndexChanged.connect(self.on_source_changed)
        form_layout.addRow("Signal d'entrée :", self.source_combo)

        # Fréquence d'échantillonnage DAC f_s
        self.rate_spin = QDoubleSpinBox()
        self.rate_spin.setRange(0.1, 1000000.0)
        self.rate_spin.setValue(float(node.params.get("sampling_rate", 100.0)))
        self.rate_spin.setSuffix(" Hz")
        self.rate_spin.valueChanged.connect(self.on_param_modified)
        form_layout.addRow("Fréq. Échantillonnage (f_s) :", self.rate_spin)

        # Résolution N-bits
        self.bits_spin = QSpinBox()
        self.bits_spin.setRange(1, 32)
        self.bits_spin.setValue(int(node.params.get("resolution_bits", 8)))
        self.bits_spin.setSuffix(" bits")
        self.bits_spin.valueChanged.connect(self.on_param_modified)
        form_layout.addRow("Résolution :", self.bits_spin)

        # Tension de référence Vref (remplace Vref min / max)
        self.vref_spin = QDoubleSpinBox()
        self.vref_spin.setRange(0.1, 1000.0)
        self.vref_spin.setValue(float(node.params.get("vref", 5.0)))
        self.vref_spin.setSuffix(" V")
        self.vref_spin.valueChanged.connect(self.on_param_modified)
        form_layout.addRow("Tension Réf. (Vref Pleine Échelle) :", self.vref_spin)

        # Décalage DC d'entrée V_DC
        self.offset_spin = QDoubleSpinBox()
        self.offset_spin.setRange(-500.0, 500.0)
        self.offset_spin.setValue(float(node.params.get("offset_dc", 2.5)))
        self.offset_spin.setSuffix(" V")
        self.offset_spin.valueChanged.connect(self.on_param_modified)
        form_layout.addRow("Décalage DC d'entrée (V_DC) :", self.offset_spin)

        # Unité de sortie
        self.unit_combo = QComboBox()
        self.unit_combo.addItems(SamplingConversionEngine.DAC_OUTPUT_UNITS)
        self.unit_combo.setCurrentText(node.params.get("output_unit", "Code Numérique (LSB)"))
        self.unit_combo.currentTextChanged.connect(self.on_param_modified)
        form_layout.addRow("Unité de sortie :", self.unit_combo)

        # Mode de reconstruction
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(SamplingConversionEngine.DAC_RECONSTRUCTIONS)
        self.mode_combo.setCurrentText(node.params.get("reconstruction", "Bloqueur d'ordre zéro (ZOH)"))
        self.mode_combo.currentTextChanged.connect(self.on_param_modified)
        form_layout.addRow("Reconstruction :", self.mode_combo)

        layout.addWidget(form_group)

        status_group = QGroupBox("État du Nœud")
        status_layout = QVBoxLayout(status_group)
        self.status_label = QLabel()
        self.update_status_label()
        status_layout.addWidget(self.status_label)

        self.btn_recalc = QPushButton("🔄 Recalculer le DAC")
        self.btn_recalc.setStyleSheet("background-color: #1E88E5; color: white; font-weight: bold; padding: 6px;")
        self.btn_recalc.clicked.connect(self.on_recalc_clicked)
        status_layout.addWidget(self.btn_recalc)

        layout.addWidget(status_group)

        view_group = QGroupBox("Visualisation du Signal DAC")
        view_layout = QVBoxLayout(view_group)

        self.btn_graph = QPushButton("📈 Voir le graphique (Matplotlib)")
        self.btn_graph.setStyleSheet("padding: 5px;")
        self.btn_graph.clicked.connect(lambda: self.on_view_graph_cb(self.node) if self.on_view_graph_cb else None)
        view_layout.addWidget(self.btn_graph)

        self.btn_table = QPushButton("📊 Voir le tableau de données (NumPy)")
        self.btn_table.setStyleSheet("padding: 5px;")
        self.btn_table.clicked.connect(lambda: self.on_view_table_cb(self.node) if self.on_view_table_cb else None)
        view_layout.addWidget(self.btn_table)

        self.btn_export_csv = QPushButton("💾 Exporter les données (CSV)...")
        self.btn_export_csv.setStyleSheet("padding: 5px; font-weight: bold;")
        self.btn_export_csv.clicked.connect(lambda: self.on_export_csv_cb(self.node) if self.on_export_csv_cb else None)
        view_layout.addWidget(self.btn_export_csv)

        layout.addWidget(view_group)

        self.btn_delete = QPushButton("🗑️ Supprimer ce nœud")
        self.btn_delete.setStyleSheet("background-color: #D32F2F; color: white; font-weight: bold; padding: 6px; margin-top: 10px;")
        self.btn_delete.clicked.connect(lambda: self.on_delete_cb(self.node) if self.on_delete_cb else None)
        layout.addWidget(self.btn_delete)

        layout.addStretch()

    def update_source_combo(self):
        self.source_combo.blockSignals(True)
        self.source_combo.clear()
        self.source_combo.addItem("Aucune connexion", None)

        selected_idx = 0
        for idx, src in enumerate(self.available_sources):
            self.source_combo.addItem(f"Entrée : {src.params['name']}", src)
            if self.node.input_node == src:
                selected_idx = idx + 1

        self.source_combo.setCurrentIndex(selected_idx)
        self.source_combo.blockSignals(False)

    def on_source_changed(self):
        selected_src = self.source_combo.currentData()
        if self.on_connect_cb:
            self.on_connect_cb(selected_src, self.node)
        self.on_param_modified()

    def update_status_label(self):
        if self.node.is_dirty:
            self.status_label.setText("⚠️ Données non à jour (Paramètres modifiés)")
            self.status_label.setStyleSheet("color: #FF9800; font-weight: bold;")
        else:
            self.status_label.setText("✅ Signal DAC à jour")
            self.status_label.setStyleSheet("color: #4CAF50; font-weight: bold;")

    def on_param_modified(self):
        self.node.params["name"] = self.name_edit.text()
        self.node.params["sampling_rate"] = self.rate_spin.value()
        self.node.params["resolution_bits"] = self.bits_spin.value()
        self.node.params["vref"] = self.vref_spin.value()
        self.node.params["offset_dc"] = self.offset_spin.value()
        self.node.params["output_unit"] = self.unit_combo.currentText()
        self.node.params["reconstruction"] = self.mode_combo.currentText()

        self.node.mark_dirty()
        self.update_status_label()

        if self.on_recalculate_cb:
            self.on_recalculate_cb(self.node, executed=False)

    def on_recalc_clicked(self):
        self.node.recalculate()
        if "auto" in str(self.node.params.get("fundamental_mode", "")).lower():
            self.f0_spin.blockSignals(True)
            self.f0_spin.setValue(float(self.node.f0_detected))
            self.f0_spin.blockSignals(False)
        self.update_status_label()

        if self.on_recalculate_cb:
            self.on_recalculate_cb(self.node, executed=True)



class FixedAverageParamWidget(QWidget):
    """Formulaire de réglage des paramètres de la Moyenne Fixe (par Bloc)."""
    def __init__(self, node: FixedAverageNode, available_sources=None, on_recalculate_cb=None, on_connect_cb=None, on_view_graph_cb=None, on_view_table_cb=None, on_export_csv_cb=None, on_delete_cb=None):
        super().__init__()
        self.node = node
        self.available_sources = available_sources or []
        self.on_recalculate_cb = on_recalculate_cb
        self.on_connect_cb = on_connect_cb
        self.on_view_graph_cb = on_view_graph_cb
        self.on_view_table_cb = on_view_table_cb
        self.on_export_csv_cb = on_export_csv_cb
        self.on_delete_cb = on_delete_cb
        self.updating_sync = False

        layout = QVBoxLayout(self)

        form_group = QGroupBox("Paramètres de la Moyenne Fixe (par Bloc)")
        form_layout = QFormLayout(form_group)

        self.name_edit = QLineEdit(node.params["name"])
        self.name_edit.textChanged.connect(self.on_param_modified)
        form_layout.addRow("Nom :", self.name_edit)

        self.source_combo = QComboBox()
        self.update_source_combo()
        self.source_combo.currentIndexChanged.connect(self.on_source_changed)
        form_layout.addRow("Signal d'entrée :", self.source_combo)

        # Nombre d'échantillons (N = 2^n)
        self.size_combo = QComboBox()
        self.size_combo.addItems(DSPFilterEngine.SAMPLE_SIZES)
        self.size_combo.setCurrentText(str(node.params.get("sample_size", 16)))
        self.size_combo.currentTextChanged.connect(self.on_param_modified)
        form_layout.addRow("Échantillons (N = 2ⁿ) :", self.size_combo)

        # Mode de réglage Cadence (Fréquence vs Période)
        self.rate_mode_combo = QComboBox()
        self.rate_mode_combo.addItems(DSPFilterEngine.RATE_MODES)
        self.rate_mode_combo.setCurrentText(node.params.get("rate_mode", "Fréquence (Hz)"))
        self.rate_mode_combo.currentTextChanged.connect(self.on_rate_mode_changed)
        form_layout.addRow("Réglage Cadence :", self.rate_mode_combo)

        # Spinbox Fréquence fs
        self.freq_spin = QDoubleSpinBox()
        self.freq_spin.setRange(0.1, 1000000.0)
        self.freq_spin.setValue(float(node.params.get("sampling_rate", 1000.0)))
        self.freq_spin.setSuffix(" Hz")
        self.freq_spin.valueChanged.connect(self.on_freq_changed)
        form_layout.addRow("Fréquence (f_s) :", self.freq_spin)

        # Spinbox Période Ts (ms)
        self.period_spin = QDoubleSpinBox()
        self.period_spin.setRange(0.001, 100000.0)
        fs_init = float(node.params.get("sampling_rate", 1000.0))
        self.period_spin.setValue(1000.0 / fs_init if fs_init > 0 else 1.0)
        self.period_spin.setSuffix(" ms")
        self.period_spin.valueChanged.connect(self.on_period_changed)
        form_layout.addRow("Période (T_s) :", self.period_spin)

        # Décalage temporel asynchrone (tau en ms)
        self.offset_spin = QDoubleSpinBox()
        self.offset_spin.setRange(-50000.0, 50000.0)
        self.offset_spin.setValue(float(node.params.get("time_offset", 0.0)) * 1000.0)
        self.offset_spin.setSuffix(" ms")
        self.offset_spin.valueChanged.connect(self.on_param_modified)
        form_layout.addRow("Décalage asynchrone (τ) :", self.offset_spin)

        # Type de Fenêtrage
        self.win_combo = QComboBox()
        self.win_combo.addItems(DSPFilterEngine.WINDOWS)
        self.win_combo.setCurrentText(node.params.get("window_type", "Rectangulaire (Uniforme)"))
        self.win_combo.currentTextChanged.connect(self.on_param_modified)
        form_layout.addRow("Fenêtrage :", self.win_combo)

        # Mode de Restitution
        self.out_combo = QComboBox()
        self.out_combo.addItems(DSPFilterEngine.OUTPUT_MODES_FIXED)
        self.out_combo.setCurrentText(node.params.get("output_mode", "Signal Décimé (1 point/bloc)"))
        self.out_combo.currentTextChanged.connect(self.on_param_modified)
        form_layout.addRow("Restitution :", self.out_combo)

        layout.addWidget(form_group)

        status_group = QGroupBox("État du Nœud")
        status_layout = QVBoxLayout(status_group)
        self.status_label = QLabel()
        self.update_status_label()
        status_layout.addWidget(self.status_label)

        self.btn_recalc = QPushButton("🔄 Recalculer la Moyenne Fixe")
        self.btn_recalc.setStyleSheet("background-color: #00897B; color: white; font-weight: bold; padding: 6px;")
        self.btn_recalc.clicked.connect(self.on_recalc_clicked)
        status_layout.addWidget(self.btn_recalc)

        layout.addWidget(status_group)

        view_group = QGroupBox("Visualisation du Pipeline")
        view_layout = QVBoxLayout(view_group)

        self.btn_graph = QPushButton("📈 Voir le graphique (Matplotlib)")
        self.btn_graph.setStyleSheet("padding: 5px;")
        self.btn_graph.clicked.connect(lambda: self.on_view_graph_cb(self.node) if self.on_view_graph_cb else None)
        view_layout.addWidget(self.btn_graph)

        self.btn_table = QPushButton("📊 Voir le tableau de données (NumPy)")
        self.btn_table.setStyleSheet("padding: 5px;")
        self.btn_table.clicked.connect(lambda: self.on_view_table_cb(self.node) if self.on_view_table_cb else None)
        view_layout.addWidget(self.btn_table)

        self.btn_export_csv = QPushButton("💾 Exporter les données (CSV)...")
        self.btn_export_csv.setStyleSheet("padding: 5px; font-weight: bold;")
        self.btn_export_csv.clicked.connect(lambda: self.on_export_csv_cb(self.node) if self.on_export_csv_cb else None)
        view_layout.addWidget(self.btn_export_csv)

        layout.addWidget(view_group)

        self.btn_delete = QPushButton("🗑️ Supprimer ce nœud")
        self.btn_delete.setStyleSheet("background-color: #D32F2F; color: white; font-weight: bold; padding: 6px; margin-top: 10px;")
        self.btn_delete.clicked.connect(lambda: self.on_delete_cb(self.node) if self.on_delete_cb else None)
        layout.addWidget(self.btn_delete)

        layout.addStretch()

    def update_source_combo(self):
        self.source_combo.blockSignals(True)
        self.source_combo.clear()
        self.source_combo.addItem("Aucune connexion", None)

        selected_idx = 0
        for idx, src in enumerate(self.available_sources):
            self.source_combo.addItem(f"Entrée : {src.params['name']}", src)
            if self.node.input_node == src:
                selected_idx = idx + 1

        self.source_combo.setCurrentIndex(selected_idx)
        self.source_combo.blockSignals(False)

    def on_source_changed(self):
        selected_src = self.source_combo.currentData()
        if self.on_connect_cb:
            self.on_connect_cb(selected_src, self.node)
        self.on_param_modified()

    def on_rate_mode_changed(self, mode_str):
        self.freq_spin.setVisible("Fréquence" in mode_str)
        self.period_spin.setVisible("Période" in mode_str)
        self.on_param_modified()

    def on_freq_changed(self, val):
        if self.updating_sync:
            return
        self.updating_sync = True
        if val > 0:
            self.period_spin.setValue(1000.0 / val)
        self.updating_sync = False
        self.on_param_modified()

    def on_period_changed(self, val):
        if self.updating_sync:
            return
        self.updating_sync = True
        if val > 0:
            self.freq_spin.setValue(1000.0 / val)
        self.updating_sync = False
        self.on_param_modified()

    def update_status_label(self):
        if self.node.is_dirty:
            self.status_label.setText("⚠️ Données non à jour (Paramètres modifiés)")
            self.status_label.setStyleSheet("color: #FF9800; font-weight: bold;")
        else:
            self.status_label.setText("✅ Moyenne Fixe à jour")
            self.status_label.setStyleSheet("color: #4CAF50; font-weight: bold;")

    def on_param_modified(self):
        self.node.params["name"] = self.name_edit.text()
        try:
            self.node.params["sample_size"] = int(self.size_combo.currentText())
        except ValueError:
            self.node.params["sample_size"] = 16
        self.node.params["rate_mode"] = self.rate_mode_combo.currentText()
        self.node.params["sampling_rate"] = self.freq_spin.value()
        self.node.params["time_offset"] = self.offset_spin.value() / 1000.0
        self.node.params["window_type"] = self.win_combo.currentText()
        self.node.params["output_mode"] = self.out_combo.currentText()

        self.node.mark_dirty()
        self.update_status_label()

        if self.on_recalculate_cb:
            self.on_recalculate_cb(self.node, executed=False)

    def on_recalc_clicked(self):
        self.node.recalculate()
        if "auto" in str(self.node.params.get("fundamental_mode", "")).lower():
            self.f0_spin.blockSignals(True)
            self.f0_spin.setValue(float(self.node.f0_detected))
            self.f0_spin.blockSignals(False)
        self.update_status_label()

        if self.on_recalculate_cb:
            self.on_recalculate_cb(self.node, executed=True)


class MovingAverageParamWidget(QWidget):
    """Formulaire de réglage des paramètres de la Moyenne Glissante (FIR)."""
    def __init__(self, node: MovingAverageNode, available_sources=None, on_recalculate_cb=None, on_connect_cb=None, on_view_graph_cb=None, on_view_table_cb=None, on_export_csv_cb=None, on_delete_cb=None):
        super().__init__()
        self.node = node
        self.available_sources = available_sources or []
        self.on_recalculate_cb = on_recalculate_cb
        self.on_connect_cb = on_connect_cb
        self.on_view_graph_cb = on_view_graph_cb
        self.on_view_table_cb = on_view_table_cb
        self.on_export_csv_cb = on_export_csv_cb
        self.on_delete_cb = on_delete_cb
        self.updating_sync = False

        layout = QVBoxLayout(self)

        form_group = QGroupBox("Paramètres de la Moyenne Glissante (FIR)")
        form_layout = QFormLayout(form_group)

        self.name_edit = QLineEdit(node.params["name"])
        self.name_edit.textChanged.connect(self.on_param_modified)
        form_layout.addRow("Nom :", self.name_edit)

        self.source_combo = QComboBox()
        self.update_source_combo()
        self.source_combo.currentIndexChanged.connect(self.on_source_changed)
        form_layout.addRow("Signal d'entrée :", self.source_combo)

        # Taille de fenêtre (N = 2^n)
        self.size_combo = QComboBox()
        self.size_combo.addItems(DSPFilterEngine.SAMPLE_SIZES)
        self.size_combo.setCurrentText(str(node.params.get("sample_size", 16)))
        self.size_combo.currentTextChanged.connect(self.on_param_modified)
        form_layout.addRow("Fenêtre (N = 2ⁿ) :", self.size_combo)

        # Mode de réglage Cadence
        self.rate_mode_combo = QComboBox()
        self.rate_mode_combo.addItems(DSPFilterEngine.RATE_MODES)
        self.rate_mode_combo.setCurrentText(node.params.get("rate_mode", "Fréquence (Hz)"))
        self.rate_mode_combo.currentTextChanged.connect(self.on_rate_mode_changed)
        form_layout.addRow("Réglage Cadence :", self.rate_mode_combo)

        # Spinbox Fréquence fs
        self.freq_spin = QDoubleSpinBox()
        self.freq_spin.setRange(0.1, 1000000.0)
        self.freq_spin.setValue(float(node.params.get("sampling_rate", 1000.0)))
        self.freq_spin.setSuffix(" Hz")
        self.freq_spin.valueChanged.connect(self.on_freq_changed)
        form_layout.addRow("Fréquence (f_s) :", self.freq_spin)

        # Spinbox Période Ts (ms)
        self.period_spin = QDoubleSpinBox()
        self.period_spin.setRange(0.001, 100000.0)
        fs_init = float(node.params.get("sampling_rate", 1000.0))
        self.period_spin.setValue(1000.0 / fs_init if fs_init > 0 else 1.0)
        self.period_spin.setSuffix(" ms")
        self.period_spin.valueChanged.connect(self.on_period_changed)
        form_layout.addRow("Période (T_s) :", self.period_spin)

        # Décalage temporel asynchrone (tau en ms)
        self.offset_spin = QDoubleSpinBox()
        self.offset_spin.setRange(-50000.0, 50000.0)
        self.offset_spin.setValue(float(node.params.get("time_offset", 0.0)) * 1000.0)
        self.offset_spin.setSuffix(" ms")
        self.offset_spin.valueChanged.connect(self.on_param_modified)
        form_layout.addRow("Décalage asynchrone (τ) :", self.offset_spin)

        # Type de Fenêtrage
        self.win_combo = QComboBox()
        self.win_combo.addItems(DSPFilterEngine.WINDOWS)
        self.win_combo.setCurrentText(node.params.get("window_type", "Rectangulaire (Uniforme)"))
        self.win_combo.currentTextChanged.connect(self.on_param_modified)
        form_layout.addRow("Fenêtrage :", self.win_combo)

        layout.addWidget(form_group)

        status_group = QGroupBox("État du Nœud")
        status_layout = QVBoxLayout(status_group)
        self.status_label = QLabel()
        self.update_status_label()
        status_layout.addWidget(self.status_label)

        self.btn_recalc = QPushButton("🔄 Recalculer la Moyenne Glissante")
        self.btn_recalc.setStyleSheet("background-color: #00796B; color: white; font-weight: bold; padding: 6px;")
        self.btn_recalc.clicked.connect(self.on_recalc_clicked)
        status_layout.addWidget(self.btn_recalc)

        layout.addWidget(status_group)

        view_group = QGroupBox("Visualisation du Pipeline")
        view_layout = QVBoxLayout(view_group)

        self.btn_graph = QPushButton("📈 Voir le graphique (Matplotlib)")
        self.btn_graph.setStyleSheet("padding: 5px;")
        self.btn_graph.clicked.connect(lambda: self.on_view_graph_cb(self.node) if self.on_view_graph_cb else None)
        view_layout.addWidget(self.btn_graph)

        self.btn_table = QPushButton("📊 Voir le tableau de données (NumPy)")
        self.btn_table.setStyleSheet("padding: 5px;")
        self.btn_table.clicked.connect(lambda: self.on_view_table_cb(self.node) if self.on_view_table_cb else None)
        view_layout.addWidget(self.btn_table)

        self.btn_export_csv = QPushButton("💾 Exporter les données (CSV)...")
        self.btn_export_csv.setStyleSheet("padding: 5px; font-weight: bold;")
        self.btn_export_csv.clicked.connect(lambda: self.on_export_csv_cb(self.node) if self.on_export_csv_cb else None)
        view_layout.addWidget(self.btn_export_csv)

        layout.addWidget(view_group)

        self.btn_delete = QPushButton("🗑️ Supprimer ce nœud")
        self.btn_delete.setStyleSheet("background-color: #D32F2F; color: white; font-weight: bold; padding: 6px; margin-top: 10px;")
        self.btn_delete.clicked.connect(lambda: self.on_delete_cb(self.node) if self.on_delete_cb else None)
        layout.addWidget(self.btn_delete)

        layout.addStretch()

    def update_source_combo(self):
        self.source_combo.blockSignals(True)
        self.source_combo.clear()
        self.source_combo.addItem("Aucune connexion", None)

        selected_idx = 0
        for idx, src in enumerate(self.available_sources):
            self.source_combo.addItem(f"Entrée : {src.params['name']}", src)
            if self.node.input_node == src:
                selected_idx = idx + 1

        self.source_combo.setCurrentIndex(selected_idx)
        self.source_combo.blockSignals(False)

    def on_source_changed(self):
        selected_src = self.source_combo.currentData()
        if self.on_connect_cb:
            self.on_connect_cb(selected_src, self.node)
        self.on_param_modified()

    def on_rate_mode_changed(self, mode_str):
        self.freq_spin.setVisible("Fréquence" in mode_str)
        self.period_spin.setVisible("Période" in mode_str)
        self.on_param_modified()

    def on_freq_changed(self, val):
        if self.updating_sync:
            return
        self.updating_sync = True
        if val > 0:
            self.period_spin.setValue(1000.0 / val)
        self.updating_sync = False
        self.on_param_modified()

    def on_period_changed(self, val):
        if self.updating_sync:
            return
        self.updating_sync = True
        if val > 0:
            self.freq_spin.setValue(1000.0 / val)
        self.updating_sync = False
        self.on_param_modified()

    def update_status_label(self):
        if self.node.is_dirty:
            self.status_label.setText("⚠️ Données non à jour (Paramètres modifiés)")
            self.status_label.setStyleSheet("color: #FF9800; font-weight: bold;")
        else:
            self.status_label.setText("✅ Moyenne Glissante à jour")
            self.status_label.setStyleSheet("color: #4CAF50; font-weight: bold;")

    def on_param_modified(self):
        self.node.params["name"] = self.name_edit.text()
        try:
            self.node.params["sample_size"] = int(self.size_combo.currentText())
        except ValueError:
            self.node.params["sample_size"] = 16
        self.node.params["rate_mode"] = self.rate_mode_combo.currentText()
        self.node.params["sampling_rate"] = self.freq_spin.value()
        self.node.params["time_offset"] = self.offset_spin.value() / 1000.0
        self.node.params["window_type"] = self.win_combo.currentText()

        self.node.mark_dirty()
        self.update_status_label()

        if self.on_recalculate_cb:
            self.on_recalculate_cb(self.node, executed=False)

    def on_recalc_clicked(self):
        self.node.recalculate()
        if "auto" in str(self.node.params.get("fundamental_mode", "")).lower():
            self.f0_spin.blockSignals(True)
            self.f0_spin.setValue(float(self.node.f0_detected))
            self.f0_spin.blockSignals(False)
        self.update_status_label()

        if self.on_recalculate_cb:
            self.on_recalculate_cb(self.node, executed=True)


from PySide6.QtWidgets import QTextBrowser


class THDAnalysisParamWidget(QWidget):
    """Formulaire de réglage des paramètres de l'Analyse THD & Harmoniques."""
    def __init__(self, node: THDAnalysisNode, available_inputs=None, on_recalculate_cb=None, on_connect_cb=None, on_view_graph_cb=None, on_view_table_cb=None, on_export_csv_cb=None, on_delete_cb=None):
        super().__init__()
        self.node = node
        self.available_inputs = available_inputs or []
        self.on_recalculate_cb = on_recalculate_cb
        self.on_connect_cb = on_connect_cb
        self.on_view_graph_cb = on_view_graph_cb
        self.on_view_table_cb = on_view_table_cb
        self.on_delete_cb = on_delete_cb
        self.on_export_csv_cb = on_export_csv_cb

        layout = QVBoxLayout(self)

        form_group = QGroupBox("Paramètres de l'Analyse THD")
        form_layout = QFormLayout(form_group)

        self.name_edit = QLineEdit(node.params["name"])
        self.name_edit.textChanged.connect(self.on_param_modified)
        form_layout.addRow("Nom :", self.name_edit)

        self.source_combo = QComboBox()
        self.update_source_combo()
        self.source_combo.currentIndexChanged.connect(self.on_source_changed)
        form_layout.addRow("Signal d'entrée :", self.source_combo)

        self.f0_mode_combo = QComboBox()
        self.f0_mode_combo.addItems(THDAnalysisEngine.FUNDAMENTAL_MODES)
        self.f0_mode_combo.setCurrentText(node.params.get("fundamental_mode", "Saisie Manuelle"))
        self.f0_mode_combo.currentTextChanged.connect(self.on_f0_mode_changed)
        form_layout.addRow("Mode Fondamentale :", self.f0_mode_combo)

        self.f0_spin = QDoubleSpinBox()
        self.f0_spin.setRange(0.1, 1000000.0)
        self.f0_spin.setValue(float(node.params.get("fundamental_freq", 50.0)))
        self.f0_spin.setSuffix(" Hz")
        self.f0_spin.valueChanged.connect(self.on_param_modified)
        self.f0_spin.setEnabled("Saisie" in node.params.get("fundamental_mode", ""))
        form_layout.addRow("Fréquence (f_0) :", self.f0_spin)

        self.harm_spin = QSpinBox()
        self.harm_spin.setRange(2, 50)
        self.harm_spin.setValue(int(node.params.get("max_harmonics", 10)))
        self.harm_spin.setSuffix(" harmoniques")
        self.harm_spin.valueChanged.connect(self.on_param_modified)
        form_layout.addRow("Nombre d'harmoniques :", self.harm_spin)

        self.unit_combo = QComboBox()
        self.unit_combo.addItems(THDAnalysisEngine.DISPLAY_UNITS)
        self.unit_combo.setCurrentText(node.params.get("display_unit", "% de la Fondamentale"))
        self.unit_combo.currentTextChanged.connect(self.on_param_modified)
        form_layout.addRow("Unité d'affichage :", self.unit_combo)

        self.win_combo = QComboBox()
        self.win_combo.addItems(THDAnalysisEngine.WINDOW_TYPES)
        self.win_combo.setCurrentText(node.params.get("window_type", "Rectangulaire"))
        self.win_combo.currentTextChanged.connect(self.on_param_modified)
        form_layout.addRow("Fenêtrage :", self.win_combo)

        layout.addWidget(form_group)

        status_group = QGroupBox("État du Nœud")
        status_layout = QVBoxLayout(status_group)
        
        self.status_label = QLabel()
        self.update_status_label()
        status_layout.addWidget(self.status_label)

        self.btn_recalc = QPushButton("🔄 Recalculer l'Analyse THD")
        self.btn_recalc.setStyleSheet("background-color: #9C27B0; color: white; font-weight: bold; padding: 6px;")
        self.btn_recalc.clicked.connect(self.on_recalc_clicked)
        status_layout.addWidget(self.btn_recalc)

        layout.addWidget(status_group)

        view_group = QGroupBox("Visualisation THD & Harmoniques")
        view_layout = QVBoxLayout(view_group)

        self.btn_graph = QPushButton("📊 Voir l'histogramme des harmoniques (Matplotlib)")
        self.btn_graph.setStyleSheet("padding: 5px;")
        self.btn_graph.clicked.connect(lambda: self.on_view_graph_cb(self.node) if self.on_view_graph_cb else None)
        view_layout.addWidget(self.btn_graph)

        self.btn_table = QPushButton("📋 Voir le tableau des harmoniques (NumPy)")
        self.btn_table.setStyleSheet("padding: 5px;")
        self.btn_table.clicked.connect(lambda: self.on_view_table_cb(self.node) if self.on_view_table_cb else None)
        view_layout.addWidget(self.btn_table)

        self.btn_export_csv = QPushButton("💾 Exporter les harmoniques (CSV)...")
        self.btn_export_csv.setStyleSheet("padding: 5px; font-weight: bold;")
        self.btn_export_csv.clicked.connect(lambda: self.on_export_csv_cb(self.node) if self.on_export_csv_cb else None)
        view_layout.addWidget(self.btn_export_csv)

        layout.addWidget(view_group)

        self.btn_delete = QPushButton("🗑️ Supprimer ce nœud")
        self.btn_delete.setStyleSheet("background-color: #D32F2F; color: white; font-weight: bold; padding: 6px; margin-top: 10px;")
        self.btn_delete.clicked.connect(lambda: self.on_delete_cb(self.node) if self.on_delete_cb else None)
        layout.addWidget(self.btn_delete)

        layout.addStretch()

    def update_source_combo(self):
        self.source_combo.blockSignals(True)
        self.source_combo.clear()
        self.source_combo.addItem("Aucune connexion", None)

        selected_idx = 0
        for idx, src in enumerate(self.available_inputs):
            self.source_combo.addItem(f"Entrée : {src.params['name']}", src)
            if self.node.input_node == src:
                selected_idx = idx + 1

        self.source_combo.setCurrentIndex(selected_idx)
        self.source_combo.blockSignals(False)

    def on_source_changed(self):
        selected_src = self.source_combo.currentData()
        if self.on_connect_cb:
            self.on_connect_cb(selected_src, self.node)
        self.on_param_modified()

    def on_f0_mode_changed(self, mode_str):
        self.f0_spin.setEnabled("Saisie" in mode_str)
        self.on_param_modified()

    def update_status_label(self):
        if self.node.is_dirty:
            self.status_label.setText("⚠️ Données non à jour (Paramètres modifiés)")
            self.status_label.setStyleSheet("color: #FF9800; font-weight: bold;")
        else:
            thd_str = f"{self.node.thd_percent:.2f}%"
            self.status_label.setText(f"✅ Analyse THD à jour | THD = {thd_str}")
            self.status_label.setStyleSheet("color: #4CAF50; font-weight: bold;")

    def on_param_modified(self):
        self.node.params["name"] = self.name_edit.text()
        self.node.params["fundamental_mode"] = self.f0_mode_combo.currentText()
        self.node.params["fundamental_freq"] = self.f0_spin.value()
        self.node.params["max_harmonics"] = self.harm_spin.value()
        self.node.params["display_unit"] = self.unit_combo.currentText()
        self.node.params["window_type"] = self.win_combo.currentText()

        self.node.mark_dirty()
        self.update_status_label()

        if self.on_recalculate_cb:
            self.on_recalculate_cb(self.node, executed=False)

    def on_recalc_clicked(self):
        self.node.recalculate()
        if "auto" in str(self.node.params.get("fundamental_mode", "")).lower():
            self.f0_spin.blockSignals(True)
            self.f0_spin.setValue(float(self.node.f0_detected))
            self.f0_spin.blockSignals(False)
        self.update_status_label()

        if self.on_recalculate_cb:
            self.on_recalculate_cb(self.node, executed=True)


class NodeDocWidget(QWidget):
    """Widget d'affichage de la documentation technique et des résultats théoriques pour l'onglet 'Fonctionnement & Théorie'."""
    def __init__(self, node):
        super().__init__()
        self.node = node

        layout = QVBoxLayout(self)
        layout.setContentsMargins(2, 2, 2, 2)

        self.browser = QTextBrowser()
        self.browser.setOpenExternalLinks(True)
        self.browser.setStyleSheet("background-color: #1E212B; color: #EEEEEE; border: none; font-size: 13px;")
        layout.addWidget(self.browser)

        self.update_doc()

    def update_doc(self):
        html_content = self.generate_html_for_node(self.node)
        self.browser.setHtml(html_content)

    def generate_html_for_node(self, node) -> str:
        ntype = getattr(node, "node_type", "")
        params = getattr(node, "params", {})
        name = params.get("name", "Nœud")

        if ntype == "fixed_average":
            N = int(params.get("sample_size", 16))
            n_pow = int(np.round(np.log2(N))) if N > 0 else 4
            fs = float(params.get("sampling_rate", 1000.0))
            offset_ms = float(params.get("time_offset", 0.0)) * 1000.0
            w_type = params.get("window_type", "Rectangulaire (Uniforme)")
            out_mode = params.get("output_mode", "Signal Décimé (1 point/bloc)")

            snr_gain = 10.0 * np.log10(N) if N > 0 else 0.0
            noise_red = np.sqrt(N) if N > 0 else 1.0
            fc_3db = (0.443 * fs) / N if N > 0 else 0.0
            shift_samples = int(np.round((offset_ms / 1000.0) * fs))

            return f"""
            <div style="font-family: sans-serif; padding: 10px; line-height: 1.5; color: #EEEEEE;">
              <h2 style="color: #00897B; margin-top:0;">📊 {name} : Moyenne Fixe (par Bloc)</h2>
              <p><b>Catégorie :</b> Filtres Numériques (DSP)</p>
              <hr style="border: 1px solid #333333;">

              <h3 style="color: #00ADB5;">1. Principe de Fonctionnement</h3>
              <p>Le nœud découpe le signal d'entrée en blocs disjoints de <b>N = {N}</b> échantillons. Pour chaque bloc, il calcule la moyenne pondérée selon la fenêtre <b>{w_type}</b> :</p>
              <p style="background-color: #2B2E3A; padding: 8px; border-radius: 4px; font-family: monospace; color: #80CBC4;">
              y_bloc[k] = (1 / N) * Σ (x[k·N + m] · w[m])
              </p>
              <p>Restitution actuelle : <b>{out_mode}</b>.</p>

              <h3 style="color: #00ADB5;">2. Implémentation Physique (MCU / FPGA)</h3>
              <p>Comme la taille du bloc est restreinte aux puissances de 2 (<b>N = 2<sup>{n_pow}</sup></b>), la division arithmétique est remplacée par un <b>décalage logique vers la droite (Bit-Shift)</b> sans instruction de division matérielle :</p>
              <pre style="background-color: #121212; padding: 10px; border-radius: 5px; color: #81C784; font-family: monospace; font-size: 12px;">
// Accumulation DMA sur N = {N} échantillons
int32_t accumulator = 0;
for (int i = 0; i &lt; {N}; i++) {{
    accumulator += buffer_dma[i];
}}
// Division ultra-rapide par décalage logique (Bit-Shift) :
int32_t moyenne = accumulator >> {n_pow}; // >> {n_pow} équivaut à / {N}
              </pre>

              <h3 style="color: #00ADB5;">3. Résultats Théoriques Attendus</h3>
              <table style="width: 100%; border-collapse: collapse; margin-top: 5px; color: #EEEEEE;">
                <tr style="background-color: #2B2E3A;">
                  <td style="padding: 6px; border: 1px solid #444;"><b>Amélioration du SNR (Bruit Gaussien)</b></td>
                  <td style="padding: 6px; border: 1px solid #444; color: #4CAF50;"><b>+{snr_gain:.2f} dB</b> (Bruit ÷ {noise_red:.2f})</td>
                </tr>
                <tr>
                  <td style="padding: 6px; border: 1px solid #444;"><b>Fréquence de Coupure (-3 dB)</b></td>
                  <td style="padding: 6px; border: 1px solid #444; color: #2196F3;"><b>{fc_3db:.2f} Hz</b> (pour f_s = {fs:.1f} Hz)</td>
                </tr>
                <tr style="background-color: #2B2E3A;">
                  <td style="padding: 6px; border: 1px solid #444;"><b>Décalage Asynchrone (τ)</b></td>
                  <td style="padding: 6px; border: 1px solid #444; color: #FF9800;"><b>{offset_ms:.2f} ms</b> (≈ {shift_samples} échantillons)</td>
                </tr>
              </table>
            </div>
            """

        elif ntype == "moving_average":
            N = int(params.get("sample_size", 16))
            n_pow = int(np.round(np.log2(N))) if N > 0 else 4
            fs = float(params.get("sampling_rate", 1000.0))
            offset_ms = float(params.get("time_offset", 0.0)) * 1000.0
            w_type = params.get("window_type", "Rectangulaire (Uniforme)")

            snr_gain = 10.0 * np.log10(N) if N > 0 else 0.0
            noise_red = np.sqrt(N) if N > 0 else 1.0
            group_delay_samples = (N - 1) / 2.0
            group_delay_time_ms = (group_delay_samples / fs) * 1000.0 if fs > 0 else 0.0
            f_notch = fs / N if N > 0 else 0.0

            return f"""
            <div style="font-family: sans-serif; padding: 10px; line-height: 1.5; color: #EEEEEE;">
              <h2 style="color: #00796B; margin-top:0;">📈 {name} : Moyenne Glissante (FIR)</h2>
              <p><b>Catégorie :</b> Filtres Numériques (DSP)</p>
              <hr style="border: 1px solid #333333;">

              <h3 style="color: #00ADB5;">1. Principe de Fonctionnement</h3>
              <p>Filtre passe-bas à réponse impulsionnelle finie (RIF / FIR) calculant la moyenne pondérée d'une fenêtre glissante de <b>N = {N}</b> échantillons (fenêtre {w_type}).</p>
              <p style="background-color: #2B2E3A; padding: 8px; border-radius: 4px; font-family: monospace; color: #80CBC4;">
              y[n] = (1 / N) * Σ (x[n - k] · w[k])
              </p>

              <h3 style="color: #00ADB5;">2. Implémentation Physique (Buffer Circulaire O(1))</h3>
              <p>Grâce au masque binaire <code>({N} - 1)</code> offert par la puissance de 2, la mise à jour s'exécute en <b>temps constant O(1)</b> par échantillon :</p>
              <pre style="background-color: #121212; padding: 10px; border-radius: 5px; color: #81C784; font-family: monospace; font-size: 12px;">
// Algorithme glissant O(1) : 1 add + 1 sub + 1 shift
sum = sum + new_sample - fifo_buffer[tail_ptr];
fifo_buffer[tail_ptr] = new_sample;
tail_ptr = (tail_ptr + 1) & ({N} - 1); // Incrément circulaire
int32_t output = sum >> {n_pow};
              </pre>

              <h3 style="color: #00ADB5;">3. Résultats Théoriques Attendus</h3>
              <table style="width: 100%; border-collapse: collapse; margin-top: 5px; color: #EEEEEE;">
                <tr style="background-color: #2B2E3A;">
                  <td style="padding: 6px; border: 1px solid #444;"><b>Gain SNR (Bruit Gaussien)</b></td>
                  <td style="padding: 6px; border: 1px solid #444; color: #4CAF50;"><b>+{snr_gain:.2f} dB</b> (Bruit ÷ {noise_red:.2f})</td>
                </tr>
                <tr>
                  <td style="padding: 6px; border: 1px solid #444;"><b>Retard de Groupe (Group Delay)</b></td>
                  <td style="padding: 6px; border: 1px solid #444; color: #FF9800;"><b>{group_delay_samples:.1f} pts</b> ({group_delay_time_ms:.2f} ms)</td>
                </tr>
                <tr style="background-color: #2B2E3A;">
                  <td style="padding: 6px; border: 1px solid #444;"><b>Encoche Principale (Notch Filter)</b></td>
                  <td style="padding: 6px; border: 1px solid #444; color: #2196F3;"><b>{f_notch:.2f} Hz</b> (et multiples)</td>
                </tr>
              </table>
            </div>
            """

        elif ntype == "median_filter":
            N = int(params.get("kernel_size", 5))
            fs = float(params.get("sampling_rate", 1000.0))
            offset_ms = float(params.get("time_offset", 0.0)) * 1000.0

            group_delay_samples = (N - 1) / 2.0
            group_delay_ms = (group_delay_samples / fs) * 1000.0 if fs > 0 else 0.0

            return f"""
            <div style="font-family: sans-serif; padding: 10px; line-height: 1.5; color: #EEEEEE;">
              <h2 style="color: #00695C; margin-top:0;">🧹 {name} : Filtre Médian Glissant (Non-Linéaire)</h2>
              <p><b>Catégorie :</b> Filtres Numériques (DSP)</p>
              <hr style="border: 1px solid #333333;">

              <h3 style="color: #00ADB5;">1. Principe de Fonctionnement</h3>
              <p>Le filtre médian glissant remplace chaque échantillon par la <b>médiane</b> (valeur centrale) des <b>N = {N}</b> échantillons environnants :</p>
              <p style="background-color: #2B2E3A; padding: 8px; border-radius: 4px; font-family: monospace; color: #80CBC4;">
              y[n] = Médiane({{ x[n - k], ..., x[n], ..., x[n + k] }})   avec k = {int((N-1)/2)}
              </p>
              <p>Étant non-linéaire, il élimine à 100% les <b>bruits impulsionnels (Spikes)</b> de largeur inférieure à <b>{int(N/2)} échantillons</b> sans flouter les transitions abruptes.</p>

              <h3 style="color: #00ADB5;">2. Implémentation Physique (FPGA / C embarqué)</h3>
              <p>Pour les fenêtres réduites (<b>N = {N}</b>), l'algorithme est câblé sous forme de <b>Réseau de Tri (Sorting Network)</b> sans boucle conditionnelle ni saut de branchement :</p>
              <pre style="background-color: #121212; padding: 10px; border-radius: 5px; color: #81C784; font-family: monospace; font-size: 12px;">
// Exemple de réseau de tri C (Window N = 3) :
#define MIN(a,b) ((a) < (b) ? (a) : (b))
#define MAX(a,b) ((a) > (b) ? (a) : (b))

float median3(float a, float b, float c) {{
    return MAX(MIN(a, b), MIN(MAX(a, b), c));
}}
              </pre>

              <h3 style="color: #00ADB5;">3. Résultats Théoriques Attendus</h3>
              <table style="width: 100%; border-collapse: collapse; margin-top: 5px; color: #EEEEEE;">
                <tr style="background-color: #2B2E3A;">
                  <td style="padding: 6px; border: 1px solid #444;"><b>Suppression des Pics Parasites (Spikes)</b></td>
                  <td style="padding: 6px; border: 1px solid #444; color: #4CAF50;"><b>Pleine efficacité</b> (Largeur &lt; {int(N/2)} pts)</td>
                </tr>
                <tr>
                  <td style="padding: 6px; border: 1px solid #444;"><b>Conservation des Fronts (Edges)</b></td>
                  <td style="padding: 6px; border: 1px solid #444; color: #81C784;"><b>Parfaite</b> (0 flou / pas d'adoucissement)</td>
                </tr>
                <tr style="background-color: #2B2E3A;">
                  <td style="padding: 6px; border: 1px solid #444;"><b>Retard de Phase / Groupe</b></td>
                  <td style="padding: 6px; border: 1px solid #444; color: #FF9800;"><b>{group_delay_samples:.1f} pts</b> ({group_delay_ms:.2f} ms)</td>
                </tr>
              </table>
            </div>
            """

        elif ntype == "dac_simulation":
            bits = int(params.get("resolution_bits", 8))
            vref = float(params.get("vref", 5.0))
            offset_dc = float(params.get("offset_dc", 2.5))
            unit_str = params.get("output_unit", "Code Numérique (LSB)")
            mode_str = params.get("reconstruction", "ZOH")
            lsb_mv = (vref / ((1 << bits) - 1)) * 1000.0 if bits > 0 else 0.0

            return f"""
            <div style="font-family: sans-serif; padding: 10px; line-height: 1.5; color: #EEEEEE;">
              <h2 style="color: #1E88E5; margin-top:0;">⚡ {name} : Simulation CAN / CNA Unipolaire</h2>
              <p><b>Catégorie :</b> Échantillonnage & Conversion</p>
              <hr style="border: 1px solid #333333;">

              <h3 style="color: #00ADB5;">1. Principe & Modélisation Unipolaire</h3>
              <p>Conversion analogique-numérique-analogique d'un signal d'entrée avec décalage continue V_DC = <b>{offset_dc:.2f} V</b> et tension de référence pleine échelle V_ref = <b>{vref:.2f} V</b>.</p>
              <p>Tout signal résultant négatif (V_in &lt; 0V) est saturé à <b>0 LSB</b>.</p>

              <h3 style="color: #00ADB5;">2. Caractéristiques Matérielles</h3>
              <ul>
                <li><b>Résolution :</b> {bits} bits ({1 << bits} niveaux quantifiés)</li>
                <li><b>Poids de 1 LSB :</b> <b>{lsb_mv:.3f} mV</b></li>
                <li><b>Unité de sortie actuelle :</b> {unit_str}</li>
                <li><b>Mode de reconstruction :</b> {mode_str}</li>
              </ul>
            </div>
            """

        else:
            return f"""
            <div style="font-family: sans-serif; padding: 10px; line-height: 1.5; color: #EEEEEE;">
              <h2 style="color: #00ADB5; margin-top:0;">📘 {name}</h2>
              <p><b>Type :</b> {ntype}</p>
              <hr style="border: 1px solid #333333;">
              <p>Consultez l'onglet <b>Paramètres</b> pour modifier la configuration du nœud et recalculez pour visualiser les résultats.</p>
            </div>
            """





class MedianFilterParamWidget(QWidget):
    """Formulaire de réglage des paramètres du Filtre Médian."""
    def __init__(self, node: MedianFilterNode, available_sources=None, on_recalculate_cb=None, on_connect_cb=None, on_view_graph_cb=None, on_view_table_cb=None, on_export_csv_cb=None, on_delete_cb=None):
        super().__init__()
        self.node = node
        self.available_sources = available_sources or []
        self.on_recalculate_cb = on_recalculate_cb
        self.on_connect_cb = on_connect_cb
        self.on_view_graph_cb = on_view_graph_cb
        self.on_view_table_cb = on_view_table_cb
        self.on_export_csv_cb = on_export_csv_cb
        self.on_delete_cb = on_delete_cb
        self.updating_sync = False

        layout = QVBoxLayout(self)

        form_group = QGroupBox("Paramètres du Filtre Médian")
        form_layout = QFormLayout(form_group)

        self.name_edit = QLineEdit(node.params["name"])
        self.name_edit.textChanged.connect(self.on_param_modified)
        form_layout.addRow("Nom :", self.name_edit)

        self.source_combo = QComboBox()
        self.update_source_combo()
        self.source_combo.currentIndexChanged.connect(self.on_source_changed)
        form_layout.addRow("Signal d'entrée :", self.source_combo)

        # Taille de fenêtre (N impair)
        self.size_combo = QComboBox()
        self.size_combo.addItems(DSPFilterEngine.KERNEL_SIZES_MEDIAN)
        self.size_combo.setCurrentText(str(node.params.get("kernel_size", 5)))
        self.size_combo.currentTextChanged.connect(self.on_param_modified)
        form_layout.addRow("Taille de fenêtre (N) :", self.size_combo)

        # Mode Cadence
        self.rate_mode_combo = QComboBox()
        self.rate_mode_combo.addItems(DSPFilterEngine.RATE_MODES)
        self.rate_mode_combo.setCurrentText(node.params.get("rate_mode", "Fréquence (Hz)"))
        self.rate_mode_combo.currentTextChanged.connect(self.on_rate_mode_changed)
        form_layout.addRow("Réglage Cadence :", self.rate_mode_combo)

        # Spinbox Fréquence fs
        self.freq_spin = QDoubleSpinBox()
        self.freq_spin.setRange(0.1, 1000000.0)
        self.freq_spin.setValue(float(node.params.get("sampling_rate", 1000.0)))
        self.freq_spin.setSuffix(" Hz")
        self.freq_spin.valueChanged.connect(self.on_freq_changed)
        form_layout.addRow("Fréquence (f_s) :", self.freq_spin)

        # Spinbox Période Ts (ms)
        self.period_spin = QDoubleSpinBox()
        self.period_spin.setRange(0.001, 100000.0)
        fs_init = float(node.params.get("sampling_rate", 1000.0))
        self.period_spin.setValue(1000.0 / fs_init if fs_init > 0 else 1.0)
        self.period_spin.setSuffix(" ms")
        self.period_spin.valueChanged.connect(self.on_period_changed)
        form_layout.addRow("Période (T_s) :", self.period_spin)

        # Décalage asynchrone
        self.offset_spin = QDoubleSpinBox()
        self.offset_spin.setRange(-50000.0, 50000.0)
        self.offset_spin.setValue(float(node.params.get("time_offset", 0.0)) * 1000.0)
        self.offset_spin.setSuffix(" ms")
        self.offset_spin.valueChanged.connect(self.on_param_modified)
        form_layout.addRow("Décalage asynchrone (τ) :", self.offset_spin)

        layout.addWidget(form_group)

        # Status Group
        status_group = QGroupBox("État du Nœud")
        status_layout = QVBoxLayout(status_group)
        self.status_label = QLabel()
        self.update_status_label()
        status_layout.addWidget(self.status_label)

        self.btn_recalc = QPushButton("🔄 Recalculer le Filtre Médian")
        self.btn_recalc.setStyleSheet("background-color: #00695C; color: white; font-weight: bold; padding: 6px;")
        self.btn_recalc.clicked.connect(self.on_recalc_clicked)
        status_layout.addWidget(self.btn_recalc)

        layout.addWidget(status_group)

        # View Group
        view_group = QGroupBox("Visualisation du Pipeline")
        view_layout = QVBoxLayout(view_group)

        self.btn_graph = QPushButton("📈 Voir le graphique (Matplotlib)")
        self.btn_graph.setStyleSheet("padding: 5px;")
        self.btn_graph.clicked.connect(lambda: self.on_view_graph_cb(self.node) if self.on_view_graph_cb else None)
        view_layout.addWidget(self.btn_graph)

        self.btn_table = QPushButton("📊 Voir le tableau de données (NumPy)")
        self.btn_table.setStyleSheet("padding: 5px;")
        self.btn_table.clicked.connect(lambda: self.on_view_table_cb(self.node) if self.on_view_table_cb else None)
        view_layout.addWidget(self.btn_table)

        self.btn_export_csv = QPushButton("💾 Exporter les données (CSV)...")
        self.btn_export_csv.setStyleSheet("padding: 5px; font-weight: bold;")
        self.btn_export_csv.clicked.connect(lambda: self.on_export_csv_cb(self.node) if self.on_export_csv_cb else None)
        view_layout.addWidget(self.btn_export_csv)

        layout.addWidget(view_group)

        self.btn_delete = QPushButton("🗑️ Supprimer ce nœud")
        self.btn_delete.setStyleSheet("background-color: #D32F2F; color: white; font-weight: bold; padding: 6px; margin-top: 10px;")
        self.btn_delete.clicked.connect(lambda: self.on_delete_cb(self.node) if self.on_delete_cb else None)
        layout.addWidget(self.btn_delete)

        layout.addStretch()

    def update_source_combo(self):
        self.source_combo.blockSignals(True)
        self.source_combo.clear()
        self.source_combo.addItem("Aucune connexion", None)

        selected_idx = 0
        for idx, src in enumerate(self.available_sources):
            self.source_combo.addItem(f"Entrée : {src.params['name']}", src)
            if self.node.input_node == src:
                selected_idx = idx + 1

        self.source_combo.setCurrentIndex(selected_idx)
        self.source_combo.blockSignals(False)

    def on_source_changed(self):
        selected_src = self.source_combo.currentData()
        if self.on_connect_cb:
            self.on_connect_cb(selected_src, self.node)
        self.on_param_modified()

    def on_rate_mode_changed(self, mode_str):
        self.freq_spin.setVisible("Fréquence" in mode_str)
        self.period_spin.setVisible("Période" in mode_str)
        self.on_param_modified()

    def on_freq_changed(self, val):
        if self.updating_sync:
            return
        self.updating_sync = True
        if val > 0:
            self.period_spin.setValue(1000.0 / val)
        self.updating_sync = False
        self.on_param_modified()

    def on_period_changed(self, val):
        if self.updating_sync:
            return
        self.updating_sync = True
        if val > 0:
            self.freq_spin.setValue(1000.0 / val)
        self.updating_sync = False
        self.on_param_modified()

    def update_status_label(self):
        if self.node.is_dirty:
            self.status_label.setText("⚠️ Données non à jour (Paramètres modifiés)")
            self.status_label.setStyleSheet("color: #FF9800; font-weight: bold;")
        else:
            self.status_label.setText("✅ Filtre Médian à jour")
            self.status_label.setStyleSheet("color: #4CAF50; font-weight: bold;")

    def on_param_modified(self):
        self.node.params["name"] = self.name_edit.text()
        try:
            self.node.params["kernel_size"] = int(self.size_combo.currentText())
        except ValueError:
            self.node.params["kernel_size"] = 5
        self.node.params["rate_mode"] = self.rate_mode_combo.currentText()
        self.node.params["sampling_rate"] = self.freq_spin.value()
        self.node.params["time_offset"] = self.offset_spin.value() / 1000.0

        self.node.mark_dirty()
        self.update_status_label()

        if self.on_recalculate_cb:
            self.on_recalculate_cb(self.node, executed=False)

    def on_recalc_clicked(self):
        self.node.recalculate()
        if "auto" in str(self.node.params.get("fundamental_mode", "")).lower():
            self.f0_spin.blockSignals(True)
            self.f0_spin.setValue(float(self.node.f0_detected))
            self.f0_spin.blockSignals(False)
        self.update_status_label()

        if self.on_recalculate_cb:
            self.on_recalculate_cb(self.node, executed=True)



class DO160DoubleExpParamWidget(QWidget):
    """Formulaire de réglage des paramètres du Générateur Impulsion Double Exponentielle DO-160 Section 22."""
    def __init__(self, node: DO160DoubleExpNode, on_recalculate_cb=None, on_view_graph_cb=None, on_view_table_cb=None, on_export_csv_cb=None, on_delete_cb=None):
        super().__init__()
        self.node = node
        self.on_recalculate_cb = on_recalculate_cb
        self.on_view_graph_cb = on_view_graph_cb
        self.on_view_table_cb = on_view_table_cb
        self.on_delete_cb = on_delete_cb
        self.on_export_csv_cb = on_export_csv_cb

        layout = QVBoxLayout(self)

        form_group = QGroupBox("Paramètres Impulsion Double Exponentielle DO-160")
        form_layout = QFormLayout(form_group)

        self.name_edit = QLineEdit(node.params["name"])
        self.name_edit.textChanged.connect(self.on_param_modified)
        form_layout.addRow("Nom :", self.name_edit)

        # Preset Forme d'Onde
        self.preset_combo = QComboBox()
        self.preset_combo.addItems(DO160Engine.DOUBLE_EXP_PRESETS)
        self.preset_combo.setCurrentText(node.params.get("preset", "WF4 (6.4 µs / 69 µs - Tension)"))
        self.preset_combo.currentTextChanged.connect(self.on_preset_changed)
        form_layout.addRow("Preset Forme d'Onde :", self.preset_combo)

        # Niveau Normatif DO-160 (1 à 5)
        self.level_combo = QComboBox()
        self.level_combo.addItems(DO160Engine.LEVELS_DO160)
        self.level_combo.setCurrentText(node.params.get("level", "Niveau 3 (300V / 600A)"))
        self.level_combo.currentTextChanged.connect(self.on_level_changed)
        form_layout.addRow("Niveau DO-160 :", self.level_combo)

        # Amplitude Crête V0 (V ou A)
        self.vpeak_spin = QDoubleSpinBox()
        self.vpeak_spin.setRange(1.0, 100000.0)
        self.vpeak_spin.setValue(float(node.params.get("v_peak", 300.0)))
        self.vpeak_spin.setSuffix(" V / A")
        self.vpeak_spin.valueChanged.connect(self.on_param_modified)
        form_layout.addRow("Amplitude Crête (V_peak) :", self.vpeak_spin)

        # Temps de montée T1 (µs)
        self.t1_spin = QDoubleSpinBox()
        self.t1_spin.setRange(0.001, 10000.0)
        self.t1_spin.setDecimals(3)
        self.t1_spin.setValue(float(node.params.get("t1_us", 6.4)))
        self.t1_spin.setSuffix(" µs")
        self.t1_spin.valueChanged.connect(self.on_param_modified)
        form_layout.addRow("Temps de montée (T1) :", self.t1_spin)

        # Temps de mi-amplitude / zéro T2 (µs)
        self.t2_spin = QDoubleSpinBox()
        self.t2_spin.setRange(0.01, 100000.0)
        self.t2_spin.setDecimals(2)
        self.t2_spin.setValue(float(node.params.get("t2_us", 69.0)))
        self.t2_spin.setSuffix(" µs")
        self.t2_spin.valueChanged.connect(self.on_param_modified)
        form_layout.addRow("Durée T2 :", self.t2_spin)

        # Mode de définition de T2 (50% vs 0% / Zero)
        self.t2_mode_combo = QComboBox()
        self.t2_mode_combo.addItems(DO160Engine.T2_MODES)
        self.t2_mode_combo.setCurrentText(node.params.get("t2_mode", "50% Amplitude (Standard)"))
        self.t2_mode_combo.currentTextChanged.connect(self.on_param_modified)
        form_layout.addRow("Définition de T2 :", self.t2_mode_combo)

        # Retard t0 (µs)
        self.offset_spin = QDoubleSpinBox()
        self.offset_spin.setRange(0.0, 100000.0)
        self.offset_spin.setValue(float(node.params.get("t_offset_us", 1.0)))
        self.offset_spin.setSuffix(" µs")
        self.offset_spin.valueChanged.connect(self.on_param_modified)
        form_layout.addRow("Retard de déclenchement (t0) :", self.offset_spin)

        # Fréquence d'échantillonnage fs (MHz)
        self.fs_spin = QDoubleSpinBox()
        self.fs_spin.setRange(0.1, 10000.0)
        self.fs_spin.setValue(float(node.params.get("sampling_rate_mhz", 50.0)))
        self.fs_spin.setSuffix(" MHz")
        self.fs_spin.valueChanged.connect(self.on_param_modified)
        form_layout.addRow("Échantillonnage (f_s) :", self.fs_spin)

        # Durée totale (µs)
        self.dur_spin = QDoubleSpinBox()
        self.dur_spin.setRange(1.0, 1000000.0)
        self.dur_spin.setValue(float(node.params.get("duration_us", 200.0)))
        self.dur_spin.setSuffix(" µs")
        self.dur_spin.valueChanged.connect(self.on_param_modified)
        form_layout.addRow("Durée totale :", self.dur_spin)

        layout.addWidget(form_group)

        status_group = QGroupBox("État du Nœud")
        status_layout = QVBoxLayout(status_group)
        self.status_label = QLabel()
        self.update_status_label()
        status_layout.addWidget(self.status_label)

        self.btn_recalc = QPushButton("🔄 Recalculer l'Impulsion")
        self.btn_recalc.setStyleSheet("background-color: #D81B60; color: white; font-weight: bold; padding: 6px;")
        self.btn_recalc.clicked.connect(self.on_recalc_clicked)
        status_layout.addWidget(self.btn_recalc)

        layout.addWidget(status_group)

        view_group = QGroupBox("Visualisation du Signal")
        view_layout = QVBoxLayout(view_group)

        self.btn_graph = QPushButton("📈 Voir le graphique (Matplotlib)")
        self.btn_graph.setStyleSheet("padding: 5px;")
        self.btn_graph.clicked.connect(lambda: self.on_view_graph_cb(self.node) if self.on_view_graph_cb else None)
        view_layout.addWidget(self.btn_graph)

        self.btn_table = QPushButton("📊 Voir le tableau de données (NumPy)")
        self.btn_table.setStyleSheet("padding: 5px;")
        self.btn_table.clicked.connect(lambda: self.on_view_table_cb(self.node) if self.on_view_table_cb else None)
        view_layout.addWidget(self.btn_table)

        self.btn_export_csv = QPushButton("💾 Exporter les données (CSV)...")
        self.btn_export_csv.setStyleSheet("padding: 5px; font-weight: bold;")
        self.btn_export_csv.clicked.connect(lambda: self.on_export_csv_cb(self.node) if self.on_export_csv_cb else None)
        view_layout.addWidget(self.btn_export_csv)

        layout.addWidget(view_group)

        self.btn_delete = QPushButton("🗑️ Supprimer ce nœud")
        self.btn_delete.setStyleSheet("background-color: #D32F2F; color: white; font-weight: bold; padding: 6px; margin-top: 10px;")
        self.btn_delete.clicked.connect(lambda: self.on_delete_cb(self.node) if self.on_delete_cb else None)
        layout.addWidget(self.btn_delete)

        layout.addStretch()

    def on_preset_changed(self, preset_str):
        self.t1_spin.blockSignals(True)
        self.t2_spin.blockSignals(True)
        self.t2_mode_combo.blockSignals(True)

        if "WF1" in preset_str:
            self.t1_spin.setValue(6.4)
            self.t2_spin.setValue(69.0)
            self.t2_mode_combo.setCurrentText("50% Amplitude (Standard)")
        elif "WF2" in preset_str:
            self.t1_spin.setValue(0.1)
            self.t2_spin.setValue(6.4)
            self.t2_mode_combo.setCurrentText("0% Amplitude / Zero (WF2)")
        elif "WF4" in preset_str:
            self.t1_spin.setValue(6.4)
            self.t2_spin.setValue(69.0)
            self.t2_mode_combo.setCurrentText("50% Amplitude (Standard)")
        elif "WF5A" in preset_str:
            self.t1_spin.setValue(40.0)
            self.t2_spin.setValue(120.0)
            self.t2_mode_combo.setCurrentText("50% Amplitude (Standard)")
        elif "WF5B" in preset_str:
            self.t1_spin.setValue(50.0)
            self.t2_spin.setValue(500.0)
            self.t2_mode_combo.setCurrentText("50% Amplitude (Standard)")

        self.t1_spin.blockSignals(False)
        self.t2_spin.blockSignals(False)
        self.t2_mode_combo.blockSignals(False)
        self.on_param_modified()

    def on_level_changed(self, level_str):
        if level_str in DO160Engine.LEVEL_PEAKS_V:
            self.vpeak_spin.blockSignals(True)
            self.vpeak_spin.setValue(DO160Engine.LEVEL_PEAKS_V[level_str])
            self.vpeak_spin.blockSignals(False)
        self.on_param_modified()

    def update_status_label(self):
        if self.node.is_dirty:
            self.status_label.setText("⚠️ Données non à jour (Paramètres modifiés)")
            self.status_label.setStyleSheet("color: #FF9800; font-weight: bold;")
        else:
            self.status_label.setText("✅ Signal DO-160 à jour")
            self.status_label.setStyleSheet("color: #4CAF50; font-weight: bold;")

    def on_param_modified(self):
        self.node.params["name"] = self.name_edit.text()
        self.node.params["preset"] = self.preset_combo.currentText()
        self.node.params["level"] = self.level_combo.currentText()
        self.node.params["v_peak"] = self.vpeak_spin.value()
        self.node.params["t1_us"] = self.t1_spin.value()
        self.node.params["t2_us"] = self.t2_spin.value()
        self.node.params["t2_mode"] = self.t2_mode_combo.currentText()
        self.node.params["t_offset_us"] = self.offset_spin.value()
        self.node.params["sampling_rate_mhz"] = self.fs_spin.value()
        self.node.params["duration_us"] = self.dur_spin.value()

        self.node.mark_dirty()
        self.update_status_label()

        if self.on_recalculate_cb:
            self.on_recalculate_cb(self.node, executed=False)

    def on_recalc_clicked(self):
        self.node.recalculate()
        if "auto" in str(self.node.params.get("fundamental_mode", "")).lower():
            self.f0_spin.blockSignals(True)
            self.f0_spin.setValue(float(self.node.f0_detected))
            self.f0_spin.blockSignals(False)
        self.update_status_label()

        if self.on_recalculate_cb:
            self.on_recalculate_cb(self.node, executed=True)


class DO160DampedSineParamWidget(QWidget):
    """Formulaire de réglage des paramètres du Générateur Sinus Amorti WF3 DO-160 Section 22."""
    def __init__(self, node: DO160DampedSineNode, available_sources=None, on_recalculate_cb=None, on_view_graph_cb=None, on_view_table_cb=None, on_export_csv_cb=None, on_delete_cb=None):
        super().__init__()
        self.node = node
        self.on_recalculate_cb = on_recalculate_cb
        self.on_view_graph_cb = on_view_graph_cb
        self.on_view_table_cb = on_view_table_cb
        self.on_delete_cb = on_delete_cb
        self.on_export_csv_cb = on_export_csv_cb

        layout = QVBoxLayout(self)

        form_group = QGroupBox("Paramètres Sinus Amorti WF3 DO-160")
        form_layout = QFormLayout(form_group)

        self.name_edit = QLineEdit(node.params["name"])
        self.name_edit.textChanged.connect(self.on_param_modified)
        form_layout.addRow("Nom :", self.name_edit)

        # Preset
        self.preset_combo = QComboBox()
        self.preset_combo.addItems(DO160Engine.DAMPED_SINE_PRESETS)
        self.preset_combo.setCurrentText(node.params.get("preset", "WF3 - 1 MHz (Sinus Amorti)"))
        self.preset_combo.currentTextChanged.connect(self.on_preset_changed)
        form_layout.addRow("Preset :", self.preset_combo)

        # Niveau Normatif
        self.level_combo = QComboBox()
        self.level_combo.addItems(DO160Engine.LEVELS_DO160)
        self.level_combo.setCurrentText(node.params.get("level", "Niveau 3 (300V / 600A)"))
        self.level_combo.currentTextChanged.connect(self.on_level_changed)
        form_layout.addRow("Niveau DO-160 :", self.level_combo)

        # Amplitude Crête V0 (V)
        self.vpeak_spin = QDoubleSpinBox()
        self.vpeak_spin.setRange(1.0, 100000.0)
        self.vpeak_spin.setValue(float(node.params.get("v_peak", 600.0)))
        self.vpeak_spin.setSuffix(" V")
        self.vpeak_spin.valueChanged.connect(self.on_param_modified)
        form_layout.addRow("Amplitude Crête (V_peak) :", self.vpeak_spin)

        # Fréquence f (MHz)
        self.freq_spin = QDoubleSpinBox()
        self.freq_spin.setRange(0.001, 1000.0)
        self.freq_spin.setDecimals(3)
        self.freq_spin.setValue(float(node.params.get("freq_mhz", 1.0)))
        self.freq_spin.setSuffix(" MHz")
        self.freq_spin.valueChanged.connect(self.on_param_modified)
        form_layout.addRow("Fréquence (f) :", self.freq_spin)

        # Amortissement de la 5ème crête r5 (%)
        self.r5_spin = QDoubleSpinBox()
        self.r5_spin.setRange(1.0, 99.0)
        self.r5_spin.setValue(float(node.params.get("r5_percent", 50.0)))
        self.r5_spin.setSuffix(" % (V5/V1)")
        self.r5_spin.valueChanged.connect(self.on_param_modified)
        form_layout.addRow("Amortissement (5ème crête) :", self.r5_spin)

        # Phase phi (deg)
        self.phase_spin = QDoubleSpinBox()
        self.phase_spin.setRange(-360.0, 360.0)
        self.phase_spin.setValue(float(node.params.get("phase_deg", 0.0)))
        self.phase_spin.setSuffix(" °")
        self.phase_spin.valueChanged.connect(self.on_param_modified)
        form_layout.addRow("Phase initiale (φ) :", self.phase_spin)

        # Retard t0 (µs)
        self.offset_spin = QDoubleSpinBox()
        self.offset_spin.setRange(0.0, 100000.0)
        self.offset_spin.setValue(float(node.params.get("t_offset_us", 1.0)))
        self.offset_spin.setSuffix(" µs")
        self.offset_spin.valueChanged.connect(self.on_param_modified)
        form_layout.addRow("Retard de déclenchement (t0) :", self.offset_spin)

        # Échantillonnage fs (MHz)
        self.fs_spin = QDoubleSpinBox()
        self.fs_spin.setRange(0.1, 10000.0)
        self.fs_spin.setValue(float(node.params.get("sampling_rate_mhz", 100.0)))
        self.fs_spin.setSuffix(" MHz")
        self.fs_spin.valueChanged.connect(self.on_param_modified)
        form_layout.addRow("Échantillonnage (f_s) :", self.fs_spin)

        # Durée (µs)
        self.dur_spin = QDoubleSpinBox()
        self.dur_spin.setRange(0.1, 100000.0)
        self.dur_spin.setValue(float(node.params.get("duration_us", 10.0)))
        self.dur_spin.setSuffix(" µs")
        self.dur_spin.valueChanged.connect(self.on_param_modified)
        form_layout.addRow("Durée totale :", self.dur_spin)

        layout.addWidget(form_group)

        status_group = QGroupBox("État du Nœud")
        status_layout = QVBoxLayout(status_group)
        self.status_label = QLabel()
        self.update_status_label()
        status_layout.addWidget(self.status_label)

        self.btn_recalc = QPushButton("🔄 Recalculer le Sinus Amorti")
        self.btn_recalc.setStyleSheet("background-color: #C2185B; color: white; font-weight: bold; padding: 6px;")
        self.btn_recalc.clicked.connect(self.on_recalc_clicked)
        status_layout.addWidget(self.btn_recalc)

        layout.addWidget(status_group)

        view_group = QGroupBox("Visualisation du Signal")
        view_layout = QVBoxLayout(view_group)

        self.btn_graph = QPushButton("📈 Voir le graphique (Matplotlib)")
        self.btn_graph.setStyleSheet("padding: 5px;")
        self.btn_graph.clicked.connect(lambda: self.on_view_graph_cb(self.node) if self.on_view_graph_cb else None)
        view_layout.addWidget(self.btn_graph)

        self.btn_table = QPushButton("📊 Voir le tableau de données (NumPy)")
        self.btn_table.setStyleSheet("padding: 5px;")
        self.btn_table.clicked.connect(lambda: self.on_view_table_cb(self.node) if self.on_view_table_cb else None)
        view_layout.addWidget(self.btn_table)

        self.btn_export_csv = QPushButton("💾 Exporter les données (CSV)...")
        self.btn_export_csv.setStyleSheet("padding: 5px; font-weight: bold;")
        self.btn_export_csv.clicked.connect(lambda: self.on_export_csv_cb(self.node) if self.on_export_csv_cb else None)
        view_layout.addWidget(self.btn_export_csv)

        layout.addWidget(view_group)

        self.btn_delete = QPushButton("🗑️ Supprimer ce nœud")
        self.btn_delete.setStyleSheet("background-color: #D32F2F; color: white; font-weight: bold; padding: 6px; margin-top: 10px;")
        self.btn_delete.clicked.connect(lambda: self.on_delete_cb(self.node) if self.on_delete_cb else None)
        layout.addWidget(self.btn_delete)

        layout.addStretch()

    def on_preset_changed(self, preset_str):
        self.freq_spin.blockSignals(True)
        if "1 MHz" in preset_str:
            self.freq_spin.setValue(1.0)
        elif "10 MHz" in preset_str:
            self.freq_spin.setValue(10.0)
        self.freq_spin.blockSignals(False)
        self.on_param_modified()

    def on_level_changed(self, level_str):
        if level_str in DO160Engine.LEVEL_PEAKS_WF3_V:
            self.vpeak_spin.blockSignals(True)
            self.vpeak_spin.setValue(DO160Engine.LEVEL_PEAKS_WF3_V[level_str])
            self.vpeak_spin.blockSignals(False)
        self.on_param_modified()

    def update_status_label(self):
        if self.node.is_dirty:
            self.status_label.setText("⚠️ Données non à jour (Paramètres modifiés)")
            self.status_label.setStyleSheet("color: #FF9800; font-weight: bold;")
        else:
            self.status_label.setText("✅ Signal WF3 à jour")
            self.status_label.setStyleSheet("color: #4CAF50; font-weight: bold;")

    def on_param_modified(self):
        self.node.params["name"] = self.name_edit.text()
        self.node.params["preset"] = self.preset_combo.currentText()
        self.node.params["level"] = self.level_combo.currentText()
        self.node.params["v_peak"] = self.vpeak_spin.value()
        self.node.params["freq_mhz"] = self.freq_spin.value()
        self.node.params["r5_percent"] = self.r5_spin.value()
        self.node.params["phase_deg"] = self.phase_spin.value()
        self.node.params["t_offset_us"] = self.offset_spin.value()
        self.node.params["sampling_rate_mhz"] = self.fs_spin.value()
        self.node.params["duration_us"] = self.dur_spin.value()

        self.node.mark_dirty()
        self.update_status_label()

        if self.on_recalculate_cb:
            self.on_recalculate_cb(self.node, executed=False)

    def on_recalc_clicked(self):
        self.node.recalculate()
        if "auto" in str(self.node.params.get("fundamental_mode", "")).lower():
            self.f0_spin.blockSignals(True)
            self.f0_spin.setValue(float(self.node.f0_detected))
            self.f0_spin.blockSignals(False)
        self.update_status_label()

        if self.on_recalculate_cb:
            self.on_recalculate_cb(self.node, executed=True)


class FFTAnalysisParamWidget(QWidget):
    """Formulaire de réglage des paramètres de l'Analyse FFT."""
    def __init__(self, node: FFTAnalysisNode, available_inputs=None, on_recalculate_cb=None, on_connect_cb=None, on_view_graph_cb=None, on_view_table_cb=None, on_export_csv_cb=None, on_delete_cb=None):
        super().__init__()
        self.node = node
        self.available_inputs = available_inputs or []
        self.on_recalculate_cb = on_recalculate_cb
        self.on_connect_cb = on_connect_cb
        self.on_view_graph_cb = on_view_graph_cb
        self.on_view_table_cb = on_view_table_cb
        self.on_delete_cb = on_delete_cb
        self.on_export_csv_cb = on_export_csv_cb

        layout = QVBoxLayout(self)

        form_group = QGroupBox("Paramètres de l'Analyse FFT")
        form_layout = QFormLayout(form_group)

        # Nom
        self.name_edit = QLineEdit(node.params["name"])
        self.name_edit.textChanged.connect(self.on_param_modified)
        form_layout.addRow("Nom :", self.name_edit)

        # Signal d'entrée connecté
        self.source_combo = QComboBox()
        self.update_source_combo()
        self.source_combo.currentIndexChanged.connect(self.on_source_changed)
        form_layout.addRow("Signal d'entrée :", self.source_combo)

        # Type de fenêtre
        self.win_combo = QComboBox()
        self.win_combo.addItems(FFTAnalysisEngine.WINDOW_TYPES)
        self.win_combo.setCurrentText(node.params.get("window_type", "Rectangulaire"))
        self.win_combo.currentTextChanged.connect(self.on_param_modified)
        form_layout.addRow("Type de fenêtre :", self.win_combo)

        # Largeur / Taille FFT
        self.nfft_combo = QComboBox()
        self.nfft_combo.addItems(FFTAnalysisEngine.FFT_SIZES)
        self.nfft_combo.setCurrentText(str(node.params.get("n_fft", "1024")))
        self.nfft_combo.currentTextChanged.connect(self.on_param_modified)
        form_layout.addRow("Largeur / Taille FFT :", self.nfft_combo)

        # Unité du spectre
        self.unit_combo = QComboBox()
        self.unit_combo.addItems(FFTAnalysisEngine.SPECTRUM_UNITS)
        self.unit_combo.setCurrentText(node.params.get("unit", "Amplitude (V)"))
        self.unit_combo.currentTextChanged.connect(self.on_param_modified)
        form_layout.addRow("Unité du spectre :", self.unit_combo)

        layout.addWidget(form_group)

        # État + Recalculer
        status_group = QGroupBox("État du Nœud")
        status_layout = QVBoxLayout(status_group)
        
        self.status_label = QLabel()
        self.update_status_label()
        status_layout.addWidget(self.status_label)

        self.btn_recalc = QPushButton("🔄 Recalculer la FFT")
        self.btn_recalc.setStyleSheet("background-color: #E91E63; color: white; font-weight: bold; padding: 6px;")
        self.btn_recalc.clicked.connect(self.on_recalc_clicked)
        status_layout.addWidget(self.btn_recalc)

        layout.addWidget(status_group)

        # Actions de Visualisation
        view_group = QGroupBox("Visualisation du Spectre")
        view_layout = QVBoxLayout(view_group)

        self.btn_graph = QPushButton("📈 Voir le spectre fréquentiel (Matplotlib)")
        self.btn_graph.setStyleSheet("padding: 5px;")
        self.btn_graph.clicked.connect(lambda: self.on_view_graph_cb(self.node) if self.on_view_graph_cb else None)
        view_layout.addWidget(self.btn_graph)

        self.btn_table = QPushButton("📊 Voir la table spectrale (NumPy)")
        self.btn_table.setStyleSheet("padding: 5px;")
        self.btn_table.clicked.connect(lambda: self.on_view_table_cb(self.node) if self.on_view_table_cb else None)
        view_layout.addWidget(self.btn_table)

        layout.addWidget(view_group)

        # Supprimer Nœud
        self.btn_delete = QPushButton("🗑️ Supprimer ce nœud")
        self.btn_delete.setStyleSheet("background-color: #D32F2F; color: white; font-weight: bold; padding: 6px; margin-top: 10px;")
        self.btn_delete.clicked.connect(lambda: self.on_delete_cb(self.node) if self.on_delete_cb else None)
        layout.addWidget(self.btn_delete)

        layout.addStretch()

    def update_source_combo(self):
        self.source_combo.blockSignals(True)
        self.source_combo.clear()
        self.source_combo.addItem("Aucune connexion", None)

        selected_idx = 0
        for idx, src in enumerate(self.available_inputs):
            self.source_combo.addItem(f"Entrée : {src.params['name']}", src)
            if self.node.input_node == src:
                selected_idx = idx + 1

        self.source_combo.setCurrentIndex(selected_idx)
        self.source_combo.blockSignals(False)

    def on_source_changed(self):
        selected_src = self.source_combo.currentData()
        if self.on_connect_cb:
            self.on_connect_cb(selected_src, self.node)
        self.on_param_modified()

    def update_status_label(self):
        if self.node.is_dirty:
            self.status_label.setText("⚠️ Calcul nécessaire (Paramètres modifiés)")
            self.status_label.setStyleSheet("color: #FF9800; font-weight: bold;")
        else:
            self.status_label.setText("✅ Spectre FFT à jour")
            self.status_label.setStyleSheet("color: #4CAF50; font-weight: bold;")

    def on_param_modified(self):
        self.node.params["name"] = self.name_edit.text()
        self.node.params["window_type"] = self.win_combo.currentText()
        self.node.params["n_fft"] = self.nfft_combo.currentText()
        self.node.params["unit"] = self.unit_combo.currentText()

        self.node.mark_dirty()
        self.update_status_label()

        if self.on_recalculate_cb:
            self.on_recalculate_cb(self.node, executed=False)

    def on_recalc_clicked(self):
        self.node.recalculate()
        if "auto" in str(self.node.params.get("fundamental_mode", "")).lower():
            self.f0_spin.blockSignals(True)
            self.f0_spin.setValue(float(self.node.f0_detected))
            self.f0_spin.blockSignals(False)
        self.update_status_label()

        if self.on_recalculate_cb:
            self.on_recalculate_cb(self.node, executed=True)


def format_si_unit(val: float, unit: str = "", precision: int = 3, show_sign: bool = False) -> str:
    """Formatte une valeur numérique avec le préfixe SI approprié (puissances de 10^3)."""
    if val is None or np.isnan(val) or np.isinf(val):
        return f"- {unit}".strip()

    non_si = ["dB", "dBm", "dBV", "%", "LSB", "bits", "code", "rad", "°", "deg"]
    if any(u.lower() in unit.lower() for u in non_si):
        sign_str = "+" if (show_sign and val > 0) else ""
        return f"{sign_str}{val:.{precision}f} {unit}".strip()

    if abs(val) < 1e-18:
        sign_str = "+" if show_sign else ""
        return f"{sign_str}0 {unit}".strip()

    prefixes = [
        (1e12, "T"),
        (1e9, "G"),
        (1e6, "M"),
        (1e3, "k"),
        (1e0, ""),
        (1e-3, "m"),
        (1e-6, "µ"),
        (1e-9, "n"),
        (1e-12, "p"),
        (1e-15, "f")
    ]
    abs_val = abs(val)
    sign_str = "+" if (show_sign and val > 0) else ""
    for scale, prefix in prefixes:
        if abs_val >= scale * 0.99999 or scale == 1e-15:
            scaled_val = val / scale
            return f"{sign_str}{scaled_val:.{precision}f} {prefix}{unit}".strip()
    return f"{sign_str}{val:.{precision}f} {unit}".strip()


class MplCanvasWidget(QWidget):
    """Widget d'affichage graphique Matplotlib interactif avec panneau latéral à onglets (Personnalisation, Données/Courbes, Curseurs)."""
    def __init__(self, associated_node=None, theme_name="dark"):
        super().__init__()
        self.associated_node = associated_node
        self.current_theme = theme_name
        self.signals_dict = {}
        self.default_title = ""
        self.default_x_label = "Temps (s)"
        self.default_y_label = "Amplitude (V)"

        # Surcharges personnalisées des titres
        self.custom_title = None
        self.custom_x_label = None
        self.custom_y_label = None

        # Style personnalisé par courbe: { label: {"color": "#...", "linestyle": "-", "linewidth": 2.0} }
        self.curve_styles = {}
        self.visible_curves = {}  # { label: bool }
        self.curve_checkboxes = {}  # { label: QCheckBox }
        self.default_colors = ["#00ADB5", "#FF5722", "#9C27B0", "#4CAF50", "#FFEB3B", "#00BCD4", "#E91E63"]

        # État des curseurs & Légende/Overlay déplaçables
        self.cursors_enabled = False
        self.cursor_a_x = None
        self.cursor_b_x = None
        self.dragging_cursor = None

        self.saved_legend_loc = "upper right"
        self.show_overlay_box = False
        self.saved_overlay_pos = (0.03, 0.95)
        self.overlay_ann = None

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Splitter principal horizontal
        self.splitter = QSplitter(Qt.Horizontal)

        # -------------------------------------------------------------
        # 1. PANNEAU LATÉRAL À ONGLETS (GAUCHE)
        # -------------------------------------------------------------
        self.left_panel = QWidget()
        left_layout = QVBoxLayout(self.left_panel)
        left_layout.setContentsMargins(2, 2, 2, 2)

        self.side_tabs = QTabWidget()

        # --- ONGLET 1 : Personnalisation ---
        tab_cust_content = QWidget()
        cust_layout = QVBoxLayout(tab_cust_content)

        # Groupe Titres & Axes
        grp_titles = QGroupBox("Titres & Axes")
        form_titles = QFormLayout(grp_titles)

        self.edit_title = QLineEdit()
        self.edit_title.setPlaceholderText("Titre personnalisé...")
        self.edit_title.textChanged.connect(self.on_titles_changed)
        form_titles.addRow(i18n.tr("graph_title"), self.edit_title)

        self.edit_x_label = QLineEdit()
        self.edit_x_label.setPlaceholderText("Axe X personnalisé...")
        self.edit_x_label.textChanged.connect(self.on_titles_changed)
        form_titles.addRow(i18n.tr("axis_x"), self.edit_x_label)

        self.edit_y_label = QLineEdit()
        self.edit_y_label.setPlaceholderText("Axe Y personnalisé...")
        self.edit_y_label.textChanged.connect(self.on_titles_changed)
        form_titles.addRow(i18n.tr("axis_y"), self.edit_y_label)

        cust_layout.addWidget(grp_titles)

        # Groupe Aspect des Courbes
        grp_curves = QGroupBox(i18n.tr("curve_aspect"))
        form_curves = QFormLayout(grp_curves)

        self.combo_curves = QComboBox()
        self.combo_curves.currentIndexChanged.connect(self.on_curve_selection_changed)
        form_curves.addRow(i18n.tr("select_curve"), self.combo_curves)

        self.btn_curve_color = QPushButton(i18n.tr("pick_color"))
        self.btn_curve_color.clicked.connect(self.pick_curve_color)
        form_curves.addRow(i18n.tr("curve_color"), self.btn_curve_color)

        self.combo_line_style = QComboBox()
        self.combo_line_style.addItems(["Continu (-)", "Pointillé (--)", "Points (:)", "Tiret-point (-.)"])
        self.combo_line_style.currentIndexChanged.connect(self.on_curve_style_modified)
        form_curves.addRow(i18n.tr("curve_style"), self.combo_line_style)

        self.spin_line_width = QDoubleSpinBox()
        self.spin_line_width.setRange(0.5, 10.0)
        self.spin_line_width.setSingleStep(0.5)
        self.spin_line_width.setValue(2.0)
        self.spin_line_width.valueChanged.connect(self.on_curve_style_modified)
        form_curves.addRow(i18n.tr("curve_width"), self.spin_line_width)

        cust_layout.addWidget(grp_curves)

        # Groupe Exportation
        grp_export = QGroupBox("Exportation")
        exp_layout = QVBoxLayout(grp_export)
        btn_export = QPushButton("💾 Exporter l'image...")
        btn_export.setStyleSheet("padding: 6px; font-weight: bold;")
        btn_export.clicked.connect(self.export_image)
        exp_layout.addWidget(btn_export)

        cust_layout.addWidget(grp_export)
        cust_layout.addStretch()

        # Wrap dans un QScrollArea
        scroll_cust = QScrollArea()
        scroll_cust.setWidgetResizable(True)
        scroll_cust.setFrameShape(QFrame.NoFrame)
        scroll_cust.setWidget(tab_cust_content)

        self.side_tabs.addTab(scroll_cust, i18n.tr("tab_customize"))

        # --- ONGLET 2 : Données & Visibilité des Courbes ---
        tab_data_content = QWidget()
        data_layout = QVBoxLayout(tab_data_content)

        grp_visibility = QGroupBox(i18n.tr("curves_visibility_group"))
        grp_vis_layout = QVBoxLayout(grp_visibility)

        btn_row = QHBoxLayout()
        btn_all = QPushButton(i18n.tr("select_all_curves"))
        btn_all.setStyleSheet("padding: 4px; font-size: 11px;")
        btn_all.clicked.connect(lambda: self.select_all_curves(True))

        btn_none = QPushButton(i18n.tr("deselect_all_curves"))
        btn_none.setStyleSheet("padding: 4px; font-size: 11px;")
        btn_none.clicked.connect(lambda: self.select_all_curves(False))

        btn_row.addWidget(btn_all)
        btn_row.addWidget(btn_none)
        grp_vis_layout.addLayout(btn_row)

        self.vbox_checkboxes = QVBoxLayout()
        grp_vis_layout.addLayout(self.vbox_checkboxes)

        data_layout.addWidget(grp_visibility)
        data_layout.addStretch()

        scroll_data = QScrollArea()
        scroll_data.setWidgetResizable(True)
        scroll_data.setFrameShape(QFrame.NoFrame)
        scroll_data.setWidget(tab_data_content)

        self.side_tabs.addTab(scroll_data, i18n.tr("tab_data"))

        # --- ONGLET 3 : Curseurs & Mesures ---
        tab_cur_content = QWidget()
        cur_layout = QVBoxLayout(tab_cur_content)

        grp_ctrl = QGroupBox("Activation & Accrochage")
        form_ctrl = QFormLayout(grp_ctrl)

        self.check_cursors = QCheckBox(i18n.tr("enable_cursors"))
        self.check_cursors.toggled.connect(self.on_cursors_toggled)
        form_ctrl.addRow("", self.check_cursors)

        self.check_show_overlay = QCheckBox(i18n.tr("show_overlay_box"))
        self.check_show_overlay.setChecked(False)
        self.check_show_overlay.toggled.connect(self.on_overlay_toggled)
        form_ctrl.addRow("", self.check_show_overlay)

        self.combo_sig_a = QComboBox()
        self.combo_sig_a.currentIndexChanged.connect(self.on_cursor_signal_changed)
        form_ctrl.addRow(i18n.tr("attach_a"), self.combo_sig_a)

        self.combo_sig_b = QComboBox()
        self.combo_sig_b.currentIndexChanged.connect(self.on_cursor_signal_changed)
        form_ctrl.addRow(i18n.tr("attach_b"), self.combo_sig_b)

        lbl_hint = QLabel("💡 Clic Gauche = Curseur A \n 💡 Clic Droit = Curseur B")
        lbl_hint.setStyleSheet("color: #888888; font-style: italic; font-size: 11px;")
        form_ctrl.addRow("", lbl_hint)

        cur_layout.addWidget(grp_ctrl)

        grp_measures = QGroupBox(i18n.tr("cursor_measures"))
        meas_layout = QVBoxLayout(grp_measures)

        self.lbl_pos_a = QLabel(i18n.tr("cursor_a_not_set"))
        self.lbl_pos_a.setWordWrap(True)
        self.lbl_pos_a.setStyleSheet("color: #00E5FF; font-weight: bold; font-size: 11px;")

        self.lbl_pos_b = QLabel(i18n.tr("cursor_b_not_set"))
        self.lbl_pos_b.setWordWrap(True)
        self.lbl_pos_b.setStyleSheet("color: #FF3D00; font-weight: bold; font-size: 11px;")

        self.lbl_delta_x = QLabel("ΔX = -")
        self.lbl_delta_x.setStyleSheet("color: #FFEB3B; font-weight: bold;")

        self.lbl_delta_y = QLabel("ΔY = -")
        self.lbl_delta_y.setStyleSheet("color: #FFEB3B; font-weight: bold;")

        self.lbl_inv_dx = QLabel("1/|ΔX| = -")
        self.lbl_inv_dx.setStyleSheet("color: #4CAF50; font-weight: bold;")

        meas_layout.addWidget(self.lbl_pos_a)
        meas_layout.addWidget(self.lbl_pos_b)
        meas_layout.addWidget(self.lbl_delta_x)
        meas_layout.addWidget(self.lbl_delta_y)
        meas_layout.addWidget(self.lbl_inv_dx)

        cur_layout.addWidget(grp_measures)

        # Groupe Analyses de Fenêtre / Span entre Curseurs (A ↔ B)
        grp_span = QGroupBox("Analyses de Fenêtre (A ↔ B)")
        span_layout = QVBoxLayout(grp_span)

        self.lbl_span_rms = QLabel("V_RMS = -")
        self.lbl_span_rms.setStyleSheet("color: #81C784; font-weight: bold; font-size: 11px;")

        self.lbl_span_dc = QLabel("V_DC (Moy) = -")
        self.lbl_span_dc.setStyleSheet("color: #80CBC4; font-size: 11px;")

        self.lbl_span_vpp = QLabel("V_pp (Crête-Crête) = -")
        self.lbl_span_vpp.setStyleSheet("color: #FFB74D; font-weight: bold; font-size: 11px;")

        self.lbl_span_minmax = QLabel("Min / Max = -")
        self.lbl_span_minmax.setStyleSheet("color: #B0BEC5; font-size: 11px;")

        self.lbl_span_crest = QLabel("Facteur de Crête = -")
        self.lbl_span_crest.setStyleSheet("color: #CE93D8; font-size: 11px;")

        self.lbl_span_energy = QLabel("Énergie du signal = -")
        self.lbl_span_energy.setStyleSheet("color: #FFF59D; font-weight: bold; font-size: 11px;")

        span_layout.addWidget(self.lbl_span_rms)
        span_layout.addWidget(self.lbl_span_dc)
        span_layout.addWidget(self.lbl_span_vpp)
        span_layout.addWidget(self.lbl_span_minmax)
        span_layout.addWidget(self.lbl_span_crest)
        span_layout.addWidget(self.lbl_span_energy)

        cur_layout.addWidget(grp_span)
        cur_layout.addStretch()

        # Wrap dans un QScrollArea
        scroll_cur = QScrollArea()
        scroll_cur.setWidgetResizable(True)
        scroll_cur.setFrameShape(QFrame.NoFrame)
        scroll_cur.setWidget(tab_cur_content)

        self.side_tabs.addTab(scroll_cur, i18n.tr("tab_cursors"))

        left_layout.addWidget(self.side_tabs)

        # -------------------------------------------------------------
        # 2. ZONE GRAPHIQUE MATPLOTLIB (DROITE)
        # -------------------------------------------------------------
        self.right_panel = QWidget()
        right_layout = QVBoxLayout(self.right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)

        top_graph_bar = QHBoxLayout()
        self.fig = Figure(figsize=(5, 3), dpi=100)
        self.canvas = FigureCanvasQTAgg(self.fig)
        self.toolbar = NavigationToolbar2QT(self.canvas, self)
        self.ax = self.fig.add_subplot(111)

        self.btn_toggle_side = QPushButton("◀ Panneau")
        self.btn_toggle_side.setCheckable(True)
        self.btn_toggle_side.setChecked(True)
        self.btn_toggle_side.setStyleSheet("padding: 3px 8px; font-weight: bold;")
        self.btn_toggle_side.toggled.connect(self.toggle_left_panel)

        top_graph_bar.addWidget(self.btn_toggle_side)
        top_graph_bar.addWidget(self.toolbar)

        right_layout.addLayout(top_graph_bar)
        right_layout.addWidget(self.canvas)

        self.splitter.addWidget(self.left_panel)
        self.splitter.addWidget(self.right_panel)
        self.splitter.setSizes([320, 880])

        main_layout.addWidget(self.splitter)

        # Événements souris Matplotlib
        self.canvas.mpl_connect("button_press_event", self.on_canvas_press)
        self.canvas.mpl_connect("motion_notify_event", self.on_canvas_move)
        self.canvas.mpl_connect("button_release_event", self.on_canvas_release)

        self.apply_theme(self.current_theme)

    def toggle_left_panel(self, checked: bool):
        self.left_panel.setVisible(checked)
        self.btn_toggle_side.setText("◀ Panneau" if checked else "▶ Panneau")

    def export_image(self):
        default_name = f"graph_{self.associated_node.params['name'] if self.associated_node else 'export'}.png"
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            i18n.tr("export_graph_img"),
            default_name,
            "Image PNG (*.png);;Document PDF (*.pdf);;Vectoriel SVG (*.svg);;Image JPEG (*.jpg)"
        )
        if file_path:
            self.fig.savefig(file_path, dpi=300, bbox_inches='tight')

    def apply_theme(self, theme_name: str):
        self.current_theme = theme_name
        self.redraw_plot()

    def clear_plot(self):
        self.ax.clear()
        self.redraw_plot()

    def on_titles_changed(self):
        self.custom_title = self.edit_title.text().strip() or None
        self.custom_x_label = self.edit_x_label.text().strip() or None
        self.custom_y_label = self.edit_y_label.text().strip() or None
        self.redraw_plot()

    def on_cursors_toggled(self, checked: bool):
        self.cursors_enabled = checked
        if checked:
            if self.cursor_a_x is None and self.signals_dict:
                first_sig = next(iter(self.signals_dict.values()))
                if first_sig[0] is not None and len(first_sig[0]) > 0:
                    t_vec = first_sig[0]
                    self.cursor_a_x = float(t_vec[len(t_vec) // 4])
                    self.cursor_b_x = float(t_vec[(3 * len(t_vec)) // 4])
        self.redraw_plot()

    def on_overlay_toggled(self, checked: bool):
        self.show_overlay_box = checked
        self.redraw_plot()

    def on_cursor_signal_changed(self):
        self.redraw_plot()

    def on_curve_selection_changed(self):
        self.update_curve_style_ui()

    def update_curve_style_ui(self):
        label = self.combo_curves.currentText()
        if not label or label not in self.curve_styles:
            return

        style = self.curve_styles[label]
        c = style["color"]
        ls = style["linestyle"]
        lw = style["linewidth"]

        qcolor = QColor(c)
        text_col = "#000000" if qcolor.lightness() > 128 else "#FFFFFF"
        self.btn_curve_color.setStyleSheet(
            f"background-color: {c}; color: {text_col}; font-weight: bold; border: 1px solid #666; padding: 4px;"
        )
        self.btn_curve_color.setText(f"Couleur : {c}")

        ls_map = {"-": 0, "--": 1, ":": 2, "-.": 3}
        self.combo_line_style.blockSignals(True)
        self.combo_line_style.setCurrentIndex(ls_map.get(ls, 0))
        self.combo_line_style.blockSignals(False)

        self.spin_line_width.blockSignals(True)
        self.spin_line_width.setValue(lw)
        self.spin_line_width.blockSignals(False)

    def pick_curve_color(self):
        label = self.combo_curves.currentText()
        if not label or label not in self.curve_styles:
            return

        curr_hex = self.curve_styles[label]["color"]
        color = QColorDialog.getColor(QColor(curr_hex), self, "Choisir la couleur de la courbe")
        if color.isValid():
            new_hex = color.name()
            self.curve_styles[label]["color"] = new_hex
            self.update_curve_style_ui()
            # Mettre à jour le style de la case à cocher correspondante
            if label in self.curve_checkboxes:
                self.curve_checkboxes[label].setStyleSheet(f"QCheckBox {{ color: {new_hex}; font-weight: bold; }}")
            self.redraw_plot()

    def on_curve_style_modified(self):
        label = self.combo_curves.currentText()
        if not label or label not in self.curve_styles:
            return

        ls_styles = ["-", "--", ":", "-."]
        idx = self.combo_line_style.currentIndex()
        new_ls = ls_styles[min(max(idx, 0), len(ls_styles) - 1)]
        new_lw = self.spin_line_width.value()

        self.curve_styles[label]["linestyle"] = new_ls
        self.curve_styles[label]["linewidth"] = new_lw
        self.redraw_plot()

    def on_curve_visibility_toggled(self, label: str, checked: bool):
        self.visible_curves[label] = checked
        self.populate_combos()
        self.redraw_plot()

    def select_all_curves(self, visible: bool):
        for label, chk in self.curve_checkboxes.items():
            chk.blockSignals(True)
            chk.setChecked(visible)
            chk.blockSignals(False)
            self.visible_curves[label] = visible
        self.populate_combos()
        self.redraw_plot()

    def populate_combos(self):
        current_a = self.combo_sig_a.currentText()
        current_b = self.combo_sig_b.currentText()
        current_curve = self.combo_curves.currentText()

        self.combo_sig_a.blockSignals(True)
        self.combo_sig_b.blockSignals(True)
        self.combo_curves.blockSignals(True)

        self.combo_sig_a.clear()
        self.combo_sig_b.clear()
        self.combo_curves.clear()

        # Nettoyage des cases à cocher de l'onglet Données
        while self.vbox_checkboxes.count():
            child = self.vbox_checkboxes.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        self.curve_checkboxes.clear()

        sig_labels = list(self.signals_dict.keys())
        color_idx = 0
        for label in sig_labels:
            if label not in self.visible_curves:
                self.visible_curves[label] = True

            if label not in self.curve_styles:
                default_c = self.default_colors[color_idx % len(self.default_colors)]
                default_ls = "--" if ("Brut" in label or "Entrée" in label) else "-"
                default_lw = 1.5 if ("Brut" in label or "Entrée" in label) else 2.2
                self.curve_styles[label] = {
                    "color": default_c,
                    "linestyle": default_ls,
                    "linewidth": default_lw
                }
            color_idx += 1

            self.combo_curves.addItem(label)

            # Ajoute aux combos de curseurs si la courbe est visible
            if self.visible_curves.get(label, True):
                self.combo_sig_a.addItem(label)
                self.combo_sig_b.addItem(label)

            # Création de la case à cocher dans l'onglet Données
            chk = QCheckBox(label)
            chk.setChecked(self.visible_curves.get(label, True))
            c_hex = self.curve_styles[label]["color"]
            chk.setStyleSheet(f"QCheckBox {{ color: {c_hex}; font-weight: bold; }}")
            chk.toggled.connect(lambda checked=False, l=label: self.on_curve_visibility_toggled(l, checked))
            self.curve_checkboxes[label] = chk
            self.vbox_checkboxes.addWidget(chk)

        visible_labels = [l for l in sig_labels if self.visible_curves.get(l, True)]

        if current_a in visible_labels:
            self.combo_sig_a.setCurrentText(current_a)
        elif visible_labels:
            self.combo_sig_a.setCurrentIndex(0)

        if current_b in visible_labels:
            self.combo_sig_b.setCurrentText(current_b)
        elif visible_labels:
            self.combo_sig_b.setCurrentIndex(min(1, len(visible_labels) - 1))

        if current_curve in sig_labels:
            self.combo_curves.setCurrentText(current_curve)
        elif sig_labels:
            self.combo_curves.setCurrentIndex(0)

        self.combo_sig_a.blockSignals(False)
        self.combo_sig_b.blockSignals(False)
        self.combo_curves.blockSignals(False)

        self.update_curve_style_ui()

    def update_multi_plot(self, signals_dict: dict, title: str = "", x_label: str = "Temps (s)", y_label: str = "Amplitude (V)"):
        self.signals_dict = signals_dict
        self.default_title = title
        self.default_x_label = x_label
        self.default_y_label = y_label

        self.populate_combos()
        self.redraw_plot()

    def redraw_plot(self):
        if self.ax.legend_ and hasattr(self.ax.legend_, '_loc'):
            self.saved_legend_loc = self.ax.legend_._loc

        if self.overlay_ann and hasattr(self.overlay_ann, 'get_position'):
            self.saved_overlay_pos = self.overlay_ann.get_position()

        self.ax.clear()

        if self.current_theme == "dark":
            fig_face = "#121212"
            ax_face = "#1A1C23"
            text_color = "#EEEEEE"
            grid_color = "#333333"
            leg_face = "#2B2E3A"
            leg_edge = "#444444"
        else:
            fig_face = "#F5F5F5"
            ax_face = "#FFFFFF"
            text_color = "#000000"
            grid_color = "#E0E0E0"
            leg_face = "#FFFFFF"
            leg_edge = "#CCCCCC"

        self.fig.patch.set_facecolor(fig_face)
        self.ax.set_facecolor(ax_face)
        self.ax.tick_params(colors=text_color, which='both')
        for spine in self.ax.spines.values():
            spine.set_color(text_color)
            spine.set_alpha(0.4)

        final_title = self.custom_title if self.custom_title else self.default_title
        final_x_label = self.custom_x_label if self.custom_x_label else self.default_x_label
        final_y_label = self.custom_y_label if self.custom_y_label else self.default_y_label

        is_thd_plot = getattr(self.associated_node, "node_type", "") == "thd_analysis" or "Ordre Harmonique" in final_x_label

        color_idx = 0
        if is_thd_plot:
            target_unit = getattr(self.associated_node, "params", {}).get("display_unit", "% de la Fondamentale") if self.associated_node else "%"
            selected_label = "Niveau (%)"
            if "dB" in target_unit or "dB" in final_y_label:
                selected_label = "Niveau (dB)"
            elif "V" in target_unit or "Amplitude" in target_unit or "V" in final_y_label:
                selected_label = "Amplitude (V)"
            elif "%" in target_unit or "%" in final_y_label:
                selected_label = "Niveau (%)"

            combo_choice = self.combo_curves.currentText()
            if combo_choice in self.signals_dict:
                selected_label = combo_choice

            for label, (t_orders, y_vals) in self.signals_dict.items():
                if not self.visible_curves.get(label, True):
                    continue
                if selected_label and label != selected_label and len(self.signals_dict) > 1:
                    continue

                if t_orders is not None and y_vals is not None and len(y_vals) > 0:
                    orders_arr = np.array(t_orders)
                    vals_arr = np.array(y_vals)
                    colors = ["#00E5FF" if int(np.round(k)) == 1 else "#FF9800" for k in orders_arr]

                    if "dB" in selected_label or "dB" in final_y_label:
                        bottom = -120.0
                        vals_clipped = np.maximum(vals_arr, bottom)
                        heights = vals_clipped - bottom
                        bars = self.ax.bar(orders_arr, heights, bottom=bottom, color=colors, width=0.65,
                                           edgecolor=grid_color, linewidth=0.8, alpha=0.9, label=label)
                        self.ax.set_ylim(-130.0, 10.0)
                    else:
                        bars = self.ax.bar(orders_arr, vals_arr, color=colors, width=0.65,
                                           edgecolor=grid_color, linewidth=0.8, alpha=0.9, label=label)
                        max_v = float(np.max(vals_arr)) if len(vals_arr) > 0 else 1.0
                        if "%" in selected_label or "%" in final_y_label:
                            self.ax.set_ylim(0.0, max(115.0, max_v * 1.15))
                        else:
                            self.ax.set_ylim(0.0, max(0.05, max_v * 1.18))

                    if len(orders_arr) <= 25:
                        self.ax.set_xticks(orders_arr)
                    else:
                        step = max(1, len(orders_arr) // 15)
                        self.ax.set_xticks(orders_arr[::step])

                    if len(orders_arr) <= 25:
                        for bar, val in zip(bars, vals_arr):
                            if "dB" in selected_label or "dB" in final_y_label:
                                y_pos = max(val, -120.0)
                                val_str = f"{val:+.1f} dB" if val > -110.0 else "-120 dB"
                                self.ax.annotate(val_str,
                                                 xy=(bar.get_x() + bar.get_width() / 2, y_pos),
                                                 xytext=(0, 3 if y_pos >= -115 else -10),
                                                 textcoords="offset points",
                                                 ha="center", va="bottom" if y_pos >= -115 else "top",
                                                 fontsize=7.5, color=text_color, fontweight="bold")
                            elif "%" in selected_label or "%" in final_y_label:
                                height = bar.get_height()
                                val_str = f"{val:.1f}%" if val >= 0.05 else "0%"
                                self.ax.annotate(val_str,
                                                 xy=(bar.get_x() + bar.get_width() / 2, height),
                                                 xytext=(0, 3),
                                                 textcoords="offset points",
                                                 ha="center", va="bottom",
                                                 fontsize=7.5, color=text_color, fontweight="bold")
                            else:
                                height = bar.get_height()
                                val_str = format_si_unit(val, "V") if abs(val) >= 1e-5 else "0 V"
                                self.ax.annotate(val_str,
                                                 xy=(bar.get_x() + bar.get_width() / 2, height),
                                                 xytext=(0, 3),
                                                 textcoords="offset points",
                                                 ha="center", va="bottom",
                                                 fontsize=7.5, color=text_color, fontweight="bold")

            if hasattr(self.associated_node, "thd_percent"):
                thd_pct = getattr(self.associated_node, "thd_percent", 0.0)
                f0_val = getattr(self.associated_node, "f0_detected", 50.0)
                v1_val = getattr(self.associated_node, "v1_amp", 0.0)

                f0_str = format_si_unit(f0_val, "Hz")
                v1_str = format_si_unit(v1_val, "V")

                box_txt = f"THD = {thd_pct:.2f} %\nf0 = {f0_str}\nV1 = {v1_str}"
                self.ax.annotate(
                    box_txt,
                    xy=(0.97, 0.95), xycoords="axes fraction",
                    ha="right", va="top",
                    bbox=dict(boxstyle="round,pad=0.5", fc=leg_face, ec="#9C27B0", lw=2.0, alpha=0.92),
                    color="#00E5FF" if self.current_theme == "dark" else "#673AB7",
                    fontsize=9.5, fontweight="bold", family="monospace"
                )
        else:
            for label, (t, y) in self.signals_dict.items():
                if not self.visible_curves.get(label, True):
                    color_idx += 1
                    continue

                if t is not None and y is not None and len(y) > 0:
                    style = self.curve_styles.get(label, {
                        "color": self.default_colors[color_idx % len(self.default_colors)],
                        "linestyle": "--" if ("Brut" in label or "Entrée" in label) else "-",
                        "linewidth": 1.5 if ("Brut" in label or "Entrée" in label) else 2.2
                    })
                    c = style["color"]
                    linestyle = style["linestyle"]
                    linewidth = style["linewidth"]
                    self.ax.plot(t, y, label=label, color=c, linestyle=linestyle, linewidth=linewidth)
                    color_idx += 1

        if final_title:
            self.ax.set_title(final_title, fontsize=11, fontweight="bold", color=text_color)

        self.ax.set_xlabel(final_x_label, color=text_color)
        self.ax.set_ylabel(final_y_label, color=text_color)
        self.ax.grid(True, linestyle="--", color=grid_color, alpha=0.6)

        handles, labels = self.ax.get_legend_handles_labels()
        if handles:
            leg = self.ax.legend(loc=self.saved_legend_loc, fontsize=9, facecolor=leg_face, edgecolor=leg_edge)
            leg.set_draggable(True)
            for txt in leg.get_texts():
                txt.set_color(text_color)

        visible_signals = {l: v for l, v in self.signals_dict.items() if self.visible_curves.get(l, True)}
        if self.cursors_enabled and visible_signals:
            self.draw_and_measure_cursors(final_x_label, final_y_label)
        else:
            self.lbl_pos_a.setText("Curseur A : Non activé")
            self.lbl_pos_b.setText("Curseur B : Non activé")
            self.lbl_delta_x.setText("ΔX = -")
            self.lbl_delta_y.setText("ΔY = -")
            self.lbl_inv_dx.setText("1/|ΔX| = -")
            self.overlay_ann = None

        self.canvas.draw()

    def draw_and_measure_cursors(self, x_unit_str, y_unit_str):
        xa_val, ya_val, label_a = self.get_snapped_coords("A")
        xb_val, yb_val, label_b = self.get_snapped_coords("B")

        x_unit = "Hz" if "Hz" in x_unit_str or "Fréquence" in x_unit_str else "s"
        y_unit = "dB" if "dB" in y_unit_str else ("LSB" if ("LSB" in y_unit_str or "Code" in y_unit_str) else "V")

        bg_color = "#2B2E3A" if self.current_theme == "dark" else "#FFFFFF"

        xa_str = format_si_unit(xa_val, x_unit) if xa_val is not None else "-"
        ya_str = format_si_unit(ya_val, y_unit) if ya_val is not None else "-"
        xb_str = format_si_unit(xb_val, x_unit) if xb_val is not None else "-"
        yb_str = format_si_unit(yb_val, y_unit) if yb_val is not None else "-"

        if xa_val is not None and ya_val is not None:
            self.ax.axvline(xa_val, color="#00E5FF", linestyle="--", linewidth=1.8, alpha=0.95)
            self.ax.plot(xa_val, ya_val, marker="o", markersize=8, color="#00E5FF", markeredgecolor="white", markeredgewidth=1.5)
            self.ax.annotate("A", (xa_val, ya_val), textcoords="offset points", xytext=(-12, 10),
                             color="#00E5FF", fontweight="bold", fontsize=10,
                             bbox=dict(boxstyle="round,pad=0.2", fc=bg_color, ec="#00E5FF", lw=1, alpha=0.85))
            self.lbl_pos_a.setText(f"A ({label_a}) :\nX = {xa_str}\nY = {ya_str}")
        else:
            self.lbl_pos_a.setText("Curseur A : Non placé")

        if xb_val is not None and yb_val is not None:
            self.ax.axvline(xb_val, color="#FF3D00", linestyle="--", linewidth=1.8, alpha=0.95)
            self.ax.plot(xb_val, yb_val, marker="o", markersize=8, color="#FF3D00", markeredgecolor="white", markeredgewidth=1.5)
            self.ax.annotate("B", (xb_val, yb_val), textcoords="offset points", xytext=(8, 10),
                             color="#FF3D00", fontweight="bold", fontsize=10,
                             bbox=dict(boxstyle="round,pad=0.2", fc=bg_color, ec="#FF3D00", lw=1, alpha=0.85))
            self.lbl_pos_b.setText(f"B ({label_b}) :\nX = {xb_str}\nY = {yb_str}")
        else:
            self.lbl_pos_b.setText("Curseur B : Non placé")

        dx = 0.0
        dy = 0.0
        abs_dx = 0.0
        inv_dx = 0.0

        v_rms = None
        v_dc = None
        v_ac_rms = None
        v_min = None
        v_max = None
        v_pp = None
        cf = None
        cf_db = None
        energy = None
        energy_unit = "V²s" if y_unit == "V" else f"{y_unit}²s"

        if xa_val is not None and xb_val is not None:
            t1 = min(xa_val, xb_val)
            t2 = max(xa_val, xb_val)
            self.ax.axvspan(t1, t2, color="#FFEB3B", alpha=0.08)

            dx = xb_val - xa_val
            dy = yb_val - ya_val if (ya_val is not None and yb_val is not None) else 0.0
            abs_dx = abs(dx)
            inv_dx = 1.0 / abs_dx if abs_dx > 1e-12 else 0.0

            dx_str = format_si_unit(dx, x_unit, show_sign=True)
            dy_str = format_si_unit(dy, y_unit, show_sign=True)
            inv_dx_str = format_si_unit(inv_dx, "Hz") if (x_unit == "s" and abs_dx > 1e-12) else ""

            self.lbl_delta_x.setText(f"ΔX = {dx_str}")
            self.lbl_delta_y.setText(f"ΔY = {dy_str}")
            self.lbl_inv_dx.setText(f"1/|ΔX| = {inv_dx_str}" if inv_dx_str else "")

            # Calculations sur le signal A dans le span [t1, t2]
            t_sig, y_sig = self.signals_dict.get(label_a, (None, None))
            if t_sig is not None and y_sig is not None and len(t_sig) > 0:
                mask = (t_sig >= t1) & (t_sig <= t2)
                t_span = t_sig[mask]
                y_span = y_sig[mask]
                if len(y_span) > 0:
                    v_dc = float(np.mean(y_span))
                    v_rms = float(np.sqrt(np.mean(y_span**2)))
                    v_ac_rms = float(np.std(y_span))
                    v_min = float(np.min(y_span))
                    v_max = float(np.max(y_span))
                    v_pp = float(v_max - v_min)
                    v_peak = max(abs(v_min), abs(v_max))
                    cf = v_peak / max(v_rms, 1e-12)
                    cf_db = 20.0 * np.log10(cf) if cf > 0 else 0.0
                    
                    if len(t_span) >= 2:
                        energy = float(integrate.trapezoid(y_span**2, t_span))
                    else:
                        energy = float(v_rms**2 * abs_dx)

            if v_rms is not None:
                self.lbl_span_rms.setText(f"V_RMS = {format_si_unit(v_rms, y_unit)}")
                self.lbl_span_dc.setText(f"V_DC = {format_si_unit(v_dc, y_unit)} | V_AC = {format_si_unit(v_ac_rms, y_unit)}")
                self.lbl_span_vpp.setText(f"V_pp = {format_si_unit(v_pp, y_unit)}")
                self.lbl_span_minmax.setText(f"Min = {format_si_unit(v_min, y_unit)} | Max = {format_si_unit(v_max, y_unit)}")
                self.lbl_span_crest.setText(f"Crête = {cf:.2f} ({cf_db:.1f} dB)")
                self.lbl_span_energy.setText(f"Énergie = {format_si_unit(energy, energy_unit)}")
            else:
                self.lbl_span_rms.setText("V_RMS = -")
                self.lbl_span_dc.setText("V_DC (Moy) = -")
                self.lbl_span_vpp.setText("V_pp (Crête-Crête) = -")
                self.lbl_span_minmax.setText("Min / Max = -")
                self.lbl_span_crest.setText("Facteur de Crête = -")
                self.lbl_span_energy.setText("Énergie du signal = -")

        # Overlay Cadre de Mesures sur le graph
        if self.show_overlay_box:
            lines = ["--- MESURES CURSEURS ---"]
            if xa_val is not None and ya_val is not None:
                lines.append(f"A ({label_a}) : X = {xa_str} | Y = {ya_str}")
            else:
                lines.append("A : Non placé")

            if xb_val is not None and yb_val is not None:
                lines.append(f"B ({label_b}) : X = {xb_str} | Y = {yb_str}")
            else:
                lines.append("B : Non placé")

            if xa_val is not None and xb_val is not None:
                lines.append(f"ΔX = {format_si_unit(dx, x_unit, show_sign=True)} | ΔY = {format_si_unit(dy, y_unit, show_sign=True)}")
                if x_unit == "s" and abs_dx > 1e-12:
                    lines.append(f"1/|ΔX| = {format_si_unit(inv_dx, 'Hz')}")

                if v_rms is not None:
                    lines.append("--- SPAN A (t1 → t2) ---")
                    lines.append(f"V_RMS = {format_si_unit(v_rms, y_unit)} | V_DC = {format_si_unit(v_dc, y_unit)}")
                    lines.append(f"V_pp  = {format_si_unit(v_pp, y_unit)} | Énergie = {format_si_unit(energy, energy_unit)}")

            box_text = "\n".join(lines)
            ec_color = "#00E5FF" if self.current_theme == "dark" else "#008C9E"
            fc_color = "#1E1E1E" if self.current_theme == "dark" else "#FFFFFF"
            txt_color = "#EEEEEE" if self.current_theme == "dark" else "#000000"

            self.overlay_ann = self.ax.annotate(
                box_text,
                xy=self.saved_overlay_pos,
                xycoords="axes fraction",
                va="top",
                bbox=dict(boxstyle="round,pad=0.5", fc=fc_color, ec=ec_color, lw=1.5, alpha=0.9),
                color=txt_color,
                fontsize=8.5,
                family="monospace"
            )
            self.overlay_ann.draggable(True)
        else:
            self.overlay_ann = None

    def get_snapped_coords(self, cursor_name: str):
        combo = self.combo_sig_a if cursor_name == "A" else self.combo_sig_b
        raw_x = self.cursor_a_x if cursor_name == "A" else self.cursor_b_x

        if raw_x is None:
            return None, None, ""

        label = combo.currentText()
        visible_signals = {l: v for l, v in self.signals_dict.items() if self.visible_curves.get(l, True)}

        if label not in visible_signals:
            if visible_signals:
                label = next(iter(visible_signals.keys()))
            else:
                return None, None, ""

        t, y = visible_signals[label]
        if t is None or y is None or len(t) == 0:
            return None, None, label

        idx = np.argmin(np.abs(t - raw_x))
        if getattr(self.associated_node, "node_type", "") == "thd_analysis" or "Ordre Harmonique" in (self.custom_x_label or self.default_x_label):
            k_order = int(np.round(t[idx]))
            f_k = float(self.associated_node.harm_freqs[idx]) if (hasattr(self.associated_node, "harm_freqs") and self.associated_node.harm_freqs is not None and idx < len(self.associated_node.harm_freqs)) else k_order * 50.0
            label = f"{label} (H{k_order} @ {format_si_unit(f_k, 'Hz')})"
        return float(t[idx]), float(y[idx]), label

    def on_canvas_press(self, event):
        visible_signals = {l: v for l, v in self.signals_dict.items() if self.visible_curves.get(l, True)}
        if not self.cursors_enabled or not visible_signals or event.inaxes != self.ax or event.xdata is None:
            return

        if self.ax.legend_ and self.ax.legend_.contains(event)[0]:
            return
        if self.overlay_ann and self.overlay_ann.contains(event)[0]:
            return

        if event.button == 1:
            self.cursor_a_x = float(event.xdata)
            self.dragging_cursor = "A"
            self.redraw_plot()
        elif event.button == 3:
            self.cursor_b_x = float(event.xdata)
            self.dragging_cursor = "B"
            self.redraw_plot()

    def on_canvas_move(self, event):
        visible_signals = {l: v for l, v in self.signals_dict.items() if self.visible_curves.get(l, True)}
        if not self.cursors_enabled or not self.dragging_cursor or not visible_signals or event.inaxes != self.ax or event.xdata is None:
            return

        if self.dragging_cursor == "A":
            self.cursor_a_x = float(event.xdata)
            self.redraw_plot()
        elif self.dragging_cursor == "B":
            self.cursor_b_x = float(event.xdata)
            self.redraw_plot()

    def on_canvas_release(self, event):
        self.dragging_cursor = None

    def get_graph_config(self) -> dict:
        leg_loc = self.saved_legend_loc
        if isinstance(leg_loc, (tuple, list, np.ndarray)):
            leg_loc = [float(x) if isinstance(x, (int, float, np.number)) else str(x) for x in leg_loc]
        elif isinstance(leg_loc, (np.integer, np.floating)):
            leg_loc = float(leg_loc) if isinstance(leg_loc, np.floating) else int(leg_loc)

        ov_pos = self.saved_overlay_pos
        if isinstance(ov_pos, (tuple, list, np.ndarray)):
            ov_pos = [float(x) for x in ov_pos]

        clean_styles = {}
        for k, v in self.curve_styles.items():
            if isinstance(v, dict):
                clean_styles[str(k)] = {
                    "color": str(v.get("color", "#00ADB5")),
                    "linestyle": str(v.get("linestyle", "-")),
                    "linewidth": float(v.get("linewidth", 2.0))
                }

        clean_visible = {str(k): bool(v) for k, v in self.visible_curves.items()}

        return {
            "custom_title": str(self.custom_title) if self.custom_title else None,
            "custom_x_label": str(self.custom_x_label) if self.custom_x_label else None,
            "custom_y_label": str(self.custom_y_label) if self.custom_y_label else None,
            "curve_styles": clean_styles,
            "visible_curves": clean_visible,
            "cursors_enabled": bool(self.cursors_enabled),
            "show_overlay_box": bool(self.show_overlay_box),
            "cursor_a_x": float(self.cursor_a_x) if self.cursor_a_x is not None else None,
            "cursor_b_x": float(self.cursor_b_x) if self.cursor_b_x is not None else None,
            "attach_a": str(self.combo_sig_a.currentText()) if hasattr(self, "combo_sig_a") and self.combo_sig_a.currentText() else None,
            "attach_b": str(self.combo_sig_b.currentText()) if hasattr(self, "combo_sig_b") and self.combo_sig_b.currentText() else None,
            "saved_legend_loc": leg_loc,
            "saved_overlay_pos": ov_pos
        }

    def apply_graph_config(self, config: dict):
        if not config or not isinstance(config, dict):
            return

        self.custom_title = config.get("custom_title")
        self.custom_x_label = config.get("custom_x_label")
        self.custom_y_label = config.get("custom_y_label")

        if hasattr(self, "edit_title") and self.custom_title:
            self.edit_title.blockSignals(True)
            self.edit_title.setText(self.custom_title)
            self.edit_title.blockSignals(False)

        if hasattr(self, "edit_x_label") and self.custom_x_label:
            self.edit_x_label.blockSignals(True)
            self.edit_x_label.setText(self.custom_x_label)
            self.edit_x_label.blockSignals(False)

        if hasattr(self, "edit_y_label") and self.custom_y_label:
            self.edit_y_label.blockSignals(True)
            self.edit_y_label.setText(self.custom_y_label)
            self.edit_y_label.blockSignals(False)

        if "curve_styles" in config and isinstance(config["curve_styles"], dict):
            self.curve_styles.update(config["curve_styles"])

        if "visible_curves" in config and isinstance(config["visible_curves"], dict):
            self.visible_curves.update(config["visible_curves"])

        self.cursors_enabled = config.get("cursors_enabled", False)
        if hasattr(self, "check_cursors"):
            self.check_cursors.blockSignals(True)
            self.check_cursors.setChecked(self.cursors_enabled)
            self.check_cursors.blockSignals(False)

        self.show_overlay_box = config.get("show_overlay_box", False)
        if hasattr(self, "check_show_overlay"):
            self.check_show_overlay.blockSignals(True)
            self.check_show_overlay.setChecked(self.show_overlay_box)
            self.check_show_overlay.blockSignals(False)

        self.cursor_a_x = config.get("cursor_a_x")
        self.cursor_b_x = config.get("cursor_b_x")

        attach_a = config.get("attach_a")
        if attach_a and hasattr(self, "combo_sig_a") and self.combo_sig_a.findText(attach_a) >= 0:
            self.combo_sig_a.blockSignals(True)
            self.combo_sig_a.setCurrentText(attach_a)
            self.combo_sig_a.blockSignals(False)

        attach_b = config.get("attach_b")
        if attach_b and hasattr(self, "combo_sig_b") and self.combo_sig_b.findText(attach_b) >= 0:
            self.combo_sig_b.blockSignals(True)
            self.combo_sig_b.setCurrentText(attach_b)
            self.combo_sig_b.blockSignals(False)

        # Réinitialise les références Matplotlib existantes avant d'appliquer les positions restaurées
        self.ax.legend_ = None
        self.overlay_ann = None

        if "saved_legend_loc" in config and config["saved_legend_loc"] is not None:
            leg_loc = config["saved_legend_loc"]
            if isinstance(leg_loc, list):
                leg_loc = tuple(leg_loc)
            self.saved_legend_loc = leg_loc

        if "saved_overlay_pos" in config and config["saved_overlay_pos"] is not None:
            ov_pos = config["saved_overlay_pos"]
            if isinstance(ov_pos, list):
                ov_pos = tuple(ov_pos)
            self.saved_overlay_pos = ov_pos

        self.populate_combos()
        self.redraw_plot()



class NumPyArrayTableWidget(QWidget):
    """Widget de tableau de données NumPy avec bouton d'exportation CSV/Texte."""
    def __init__(self, associated_node=None):
        super().__init__()
        self.associated_node = associated_node
        self.current_t = None
        self.current_columns = {}
        self.x_label = "Temps (s)"

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        top_bar = QHBoxLayout()
        btn_export = QPushButton("💾 Exporter le tableau (CSV)...")
        btn_export.setStyleSheet("padding: 4px 10px; font-weight: bold;")
        btn_export.clicked.connect(self.export_csv)
        top_bar.addStretch()
        top_bar.addWidget(btn_export)

        layout.addLayout(top_bar)

        self.table = QTableWidget()
        layout.addWidget(self.table)

    def set_multi_signal_data(self, t: np.ndarray, columns_dict: dict, x_label: str = "Temps (s)"):
        self.current_t = t
        self.current_columns = columns_dict
        self.x_label = x_label

        if t is None or len(t) == 0 or not columns_dict:
            self.table.setRowCount(0)
            self.table.setColumnCount(0)
            return

        max_rows = max([len(t)] + [len(y) for (t_v, y) in columns_dict.values() if y is not None])
        cols = 1 + len(columns_dict)
        self.table.setRowCount(max_rows)
        self.table.setColumnCount(cols)

        headers = [x_label] + list(columns_dict.keys())
        self.table.setHorizontalHeaderLabels(headers)

        for r in range(max_rows):
            val_str = f"{t[r]:.6f}" if r < len(t) else "-"
            item_t = QTableWidgetItem(val_str)
            item_t.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(r, 0, item_t)

        c_idx = 1
        for col_name, (t_vec, y) in columns_dict.items():
            if y is not None:
                col_len = len(y)
                for r in range(max_rows):
                    val_str = f"{y[r]:.6f}" if r < col_len else ""
                    item_y = QTableWidgetItem(val_str)
                    item_y.setTextAlignment(Qt.AlignCenter)
                    self.table.setItem(r, c_idx, item_y)
            c_idx += 1

    def export_csv(self):
        if self.current_t is None or not self.current_columns:
            return

        default_name = f"table_{self.associated_node.params['name'] if self.associated_node else 'export'}.csv"
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            i18n.tr("export_table_csv"),
            default_name,
            "Fichier CSV (*.csv);;Fichier Texte (*.txt);;Tous les fichiers (*)"
        )
        if not file_path:
            return

        delimiter = ";" if file_path.endswith(".csv") else "\t"
        headers = [self.x_label] + list(self.current_columns.keys())

        max_rows = max([len(self.current_t)] + [len(y) for (t_v, y) in self.current_columns.values() if y is not None])

        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(delimiter.join(headers) + "\n")
                for r in range(max_rows):
                    row_vals = []
                    row_vals.append(f"{self.current_t[r]:.6f}" if r < len(self.current_t) else "")
                    for col_name, (t_v, y) in self.current_columns.items():
                        row_vals.append(f"{y[r]:.6f}" if (y is not None and r < len(y)) else "")
                    f.write(delimiter.join(row_vals) + "\n")
        except Exception as e:
            print(f"Erreur lors de l'export du tableau: {e}")


class MainWindow(QMainWindow):
    """Fenêtre principale avec gestion des préférences et sauvegarde de projet."""
    def __init__(self):
        super().__init__()
        self.nodes_registry = []
        self.current_project_path = None

        # Chargement des préférences utilisateur
        self.settings = SettingsManager.load_settings()
        self.current_theme = self.settings.get("theme", "dark")
        self.current_font = QFont(
            self.settings.get("font_family", "Segoe UI"),
            self.settings.get("font_size", 10)
        )
        i18n.set_language(self.settings.get("language", "fr"))

        QApplication.setFont(self.current_font)
        self.resize(1280, 800)

        self.setup_menu_bar()
        self.setup_ui_layout()
        self.setup_initial_nodes()
        self.retranslate_ui()
        self.apply_theme(self.current_theme)
        self.update_recent_projects_menu()

    def showEvent(self, event):
        super().showEvent(event)
        geom_b64 = self.settings.get("window_geometry", "")
        if geom_b64:
            self.restoreGeometry(QByteArray.fromBase64(geom_b64.encode("utf-8")))

        dock_b64 = self.settings.get("dock_state", "")
        if dock_b64:
            self.restoreState(QByteArray.fromBase64(dock_b64.encode("utf-8")))

    def closeEvent(self, event):
        self.settings["window_geometry"] = self.saveGeometry().toBase64().data().decode("utf-8")
        self.settings["dock_state"] = self.saveState().toBase64().data().decode("utf-8")
        self.settings["theme"] = self.current_theme
        self.settings["font_family"] = self.current_font.family()
        self.settings["font_size"] = self.current_font.pointSize()
        self.settings["language"] = i18n.current_lang

        SettingsManager.save_settings(self.settings)
        super().closeEvent(event)

    def setup_menu_bar(self):
        self.menu_bar = self.menuBar()

        # Fichier
        self.file_menu = self.menu_bar.addMenu("")
        self.action_new = QAction(self)
        self.action_new.setShortcut(QKeySequence("Ctrl+N"))
        self.action_new.triggered.connect(self.new_project)

        self.action_open = QAction(self)
        self.action_open.setShortcut(QKeySequence("Ctrl+O"))
        self.action_open.triggered.connect(self.open_project_dialog)

        self.action_save = QAction(self)
        self.action_save.setShortcut(QKeySequence("Ctrl+S"))
        self.action_save.triggered.connect(self.save_project)

        self.action_save_as = QAction(self)
        self.action_save_as.setShortcut(QKeySequence("Ctrl+Shift+S"))
        self.action_save_as.triggered.connect(self.save_project_as_dialog)

        self.recent_menu = QMenu(self)

        self.action_exit = QAction(self)
        self.action_exit.triggered.connect(self.close)

        self.file_menu.addAction(self.action_new)
        self.file_menu.addAction(self.action_open)
        self.file_menu.addMenu(self.recent_menu)
        self.file_menu.addSeparator()
        self.file_menu.addAction(self.action_save)
        self.file_menu.addAction(self.action_save_as)
        self.file_menu.addSeparator()
        self.file_menu.addAction(self.action_exit)

        # Nœuds (Sous-menus par catégorie)
        self.nodes_menu = self.menu_bar.addMenu("")
        self.sources_submenu = self.nodes_menu.addMenu("")
        self.do160_submenu = self.nodes_menu.addMenu("")
        self.filters_submenu = self.nodes_menu.addMenu("")
        self.dsp_filters_submenu = self.nodes_menu.addMenu("")
        self.maths_submenu = self.nodes_menu.addMenu("")
        self.noise_submenu = self.nodes_menu.addMenu("")
        self.sampling_submenu = self.nodes_menu.addMenu("")
        self.analyses_submenu = self.nodes_menu.addMenu("")

        self.action_add_gen = QAction(self)
        self.action_add_gen.triggered.connect(self.add_new_generator)
        self.action_add_csv = QAction(self)
        self.action_add_csv.triggered.connect(self.add_new_csv_import)
        self.action_add_do160_double_exp = QAction(self)
        self.action_add_do160_double_exp.triggered.connect(self.add_new_do160_double_exp)
        self.action_add_do160_damped_sine = QAction(self)
        self.action_add_do160_damped_sine.triggered.connect(self.add_new_do160_damped_sine)
        self.action_add_lowpass = QAction(self)
        self.action_add_lowpass.triggered.connect(self.add_new_lowpass_filter)
        self.action_add_highpass = QAction(self)
        self.action_add_highpass.triggered.connect(self.add_new_highpass_filter)
        self.action_add_bandpass = QAction(self)
        self.action_add_bandpass.triggered.connect(self.add_new_bandpass_filter)
        self.action_add_bandstop = QAction(self)
        self.action_add_bandstop.triggered.connect(self.add_new_bandstop_filter)

        self.action_add_derivative = QAction(self)
        self.action_add_derivative.triggered.connect(self.add_new_derivative)
        self.action_add_integrator = QAction(self)
        self.action_add_integrator.triggered.connect(self.add_new_integrator)
        self.action_add_gain = QAction(self)
        self.action_add_gain.triggered.connect(self.add_new_gain)
        self.action_add_inversion = QAction(self)
        self.action_add_inversion.triggered.connect(self.add_new_inversion)
        self.action_add_abs = QAction(self)
        self.action_add_abs.triggered.connect(self.add_new_abs)
        self.action_add_log = QAction(self)
        self.action_add_log.triggered.connect(self.add_new_log)
        self.action_add_exp = QAction(self)
        self.action_add_exp.triggered.connect(self.add_new_exp)
        self.action_add_power = QAction(self)
        self.action_add_power.triggered.connect(self.add_new_power)
        self.action_add_addition = QAction(self)
        self.action_add_addition.triggered.connect(self.add_new_addition)

        self.action_add_noise = QAction(self)
        self.action_add_noise.triggered.connect(self.add_new_noise)
        self.action_add_resample = QAction(self)
        self.action_add_resample.triggered.connect(self.add_new_resample)
        self.action_add_interpolation = QAction(self)
        self.action_add_interpolation.triggered.connect(self.add_new_interpolation)
        self.action_add_dac = QAction(self)
        self.action_add_dac.triggered.connect(self.add_new_dac)

        self.action_add_fixed_avg = QAction(self)
        self.action_add_fixed_avg.triggered.connect(self.add_new_fixed_avg)
        self.action_add_moving_avg = QAction(self)
        self.action_add_moving_avg.triggered.connect(self.add_new_moving_avg)
        self.action_add_median_filter = QAction(self)
        self.action_add_median_filter.triggered.connect(self.add_new_median_filter)

        self.action_add_thd = QAction(self)
        self.action_add_thd.triggered.connect(self.add_new_thd_analysis)
        self.action_add_fft = QAction(self)
        self.action_add_fft.triggered.connect(self.add_new_fft_analysis)

        self.sources_submenu.addAction(self.action_add_gen)
        self.sources_submenu.addAction(self.action_add_csv)
        self.do160_submenu.addAction(self.action_add_do160_double_exp)
        self.do160_submenu.addAction(self.action_add_do160_damped_sine)
        self.filters_submenu.addAction(self.action_add_lowpass)
        self.filters_submenu.addAction(self.action_add_highpass)
        self.filters_submenu.addAction(self.action_add_bandpass)
        self.filters_submenu.addAction(self.action_add_bandstop)
        self.maths_submenu.addAction(self.action_add_derivative)
        self.maths_submenu.addAction(self.action_add_integrator)
        self.maths_submenu.addAction(self.action_add_gain)
        self.maths_submenu.addAction(self.action_add_inversion)
        self.maths_submenu.addAction(self.action_add_abs)
        self.maths_submenu.addAction(self.action_add_log)
        self.maths_submenu.addAction(self.action_add_exp)
        self.maths_submenu.addAction(self.action_add_power)
        self.maths_submenu.addAction(self.action_add_addition)
        self.noise_submenu.addAction(self.action_add_noise)
        self.sampling_submenu.addAction(self.action_add_resample)
        self.sampling_submenu.addAction(self.action_add_interpolation)
        self.sampling_submenu.addAction(self.action_add_dac)
        self.dsp_filters_submenu.addAction(self.action_add_fixed_avg)
        self.dsp_filters_submenu.addAction(self.action_add_moving_avg)
        self.dsp_filters_submenu.addAction(self.action_add_median_filter)
        self.analyses_submenu.addAction(self.action_add_thd)
        self.analyses_submenu.addAction(self.action_add_fft)

        # Édition
        self.edit_menu = self.menu_bar.addMenu("")

        # Calcul
        self.calc_menu = self.menu_bar.addMenu("")
        self.action_recalc_all = QAction(self)
        self.action_recalc_all.setShortcut(QKeySequence("F5"))
        self.action_recalc_all.triggered.connect(self.recalc_all_nodes)
        self.calc_menu.addAction(self.action_recalc_all)

        # Affichage
        self.view_menu = self.menu_bar.addMenu("")
        self.theme_menu = self.view_menu.addMenu("Thème")
        
        action_dark = QAction("Sombre", self)
        action_light = QAction("Clair", self)
        action_dark.triggered.connect(lambda: self.apply_theme("dark"))
        action_light.triggered.connect(lambda: self.apply_theme("light"))
        self.theme_menu.addAction(action_dark)
        self.theme_menu.addAction(action_light)

        # Sous-menu Police
        self.font_menu = self.view_menu.addMenu("Police")
        self.action_choose_font = QAction(self)
        self.action_choose_font.triggered.connect(self.choose_font_dialog)
        self.font_menu.addAction(self.action_choose_font)
        
        self.font_menu.addSeparator()
        self.size_menu = self.font_menu.addMenu("Taille de police")
        for sz in [8, 9, 10, 11, 12, 14, 16, 18]:
            act_sz = QAction(f"{sz} pt", self)
            act_sz.triggered.connect(lambda checked=False, s=sz: self.set_font_size(s))
            self.size_menu.addAction(act_sz)

        self.panels_menu = self.view_menu.addMenu("Panneaux")

        # Langue
        self.lang_menu = self.menu_bar.addMenu("")
        action_fr = QAction("Français", self)
        action_en = QAction("English", self)
        action_fr.triggered.connect(lambda: self.switch_language("fr"))
        action_en.triggered.connect(lambda: self.switch_language("en"))
        self.lang_menu.addAction(action_fr)
        self.lang_menu.addAction(action_en)

        self.help_menu = self.menu_bar.addMenu("")

    def setup_ui_layout(self):
        # Zone centrale : Canvas Nœuds
        self.node_editor = NodeEditorCanvas(
            selection_callback=self.on_node_selected,
            double_click_callback=self.on_node_double_clicked,
            view_graph_cb=self.open_graph_for_node,
            view_table_cb=self.open_table_for_node,
            export_csv_cb=self.export_csv_for_node,
            connect_cb=self.on_wire_connected,
            delete_node_cb=self.delete_node
        )
        self.setCentralWidget(self.node_editor)

        # Dock Gauche : Explorateur
        self.tree_dock = QDockWidget(self)
        self.tree_widget = QTreeWidget()
        self.tree_widget.setHeaderLabels(["Explorateur"])
        self.tree_widget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree_widget.customContextMenuRequested.connect(self.show_tree_context_menu)
        self.tree_widget.itemClicked.connect(self.on_tree_item_clicked)
        self.tree_widget.itemDoubleClicked.connect(self.on_tree_item_double_clicked)
        self.tree_dock.setWidget(self.tree_widget)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.tree_dock)

        # Dock Bas : Visualisation
        self.bottom_dock = QDockWidget(self)
        self.center_tabs = QTabWidget()
        self.center_tabs.setTabsClosable(True)
        self.center_tabs.tabCloseRequested.connect(self.close_center_tab)
        self.bottom_dock.setWidget(self.center_tabs)
        self.addDockWidget(Qt.BottomDockWidgetArea, self.bottom_dock)

        # Dock Droit : Inspecteur
        self.right_dock = QDockWidget(self)
        self.right_tabs = QTabWidget()
        self.right_dock.setWidget(self.right_tabs)
        self.addDockWidget(Qt.RightDockWidgetArea, self.right_dock)

        self.panels_menu.addAction(self.tree_dock.toggleViewAction())
        self.panels_menu.addAction(self.bottom_dock.toggleViewAction())
        self.panels_menu.addAction(self.right_dock.toggleViewAction())

    def setup_initial_nodes(self):
        """Crée un générateur et un filtre passe-bas connectés au démarrage tout à gauche de la zone."""
        gen = self.node_editor.add_generator_node("Générateur 1", x=-850, y=-50)
        flt = self.node_editor.add_filter_node("Filtre Passe-Bas 1", x=-580, y=-50)
        
        self.nodes_registry.extend([gen, flt])
        self.node_editor.create_connection(gen, flt)
        
        gen.recalculate()
        flt.recalculate()

        self.refresh_project_tree()
        self.node_editor.centerOn(-650, 0)

    # --- Gestion des Projets (.psa) ---
    def new_project(self):
        nodes_to_del = list(self.nodes_registry)
        for n in nodes_to_del:
            self.delete_node(n)

        self.current_project_path = None
        self.setup_initial_nodes()
        self.node_editor.centerOn(-650, 0)
        self.statusBar().showMessage(i18n.tr("new_project"))

    def open_project_dialog(self):
        last_dir = self.settings.get("last_open_dir", "")
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            i18n.tr("open"),
            last_dir,
            ProjectIOManager.FILE_FILTER
        )
        if file_path:
            self.load_project_file(file_path)

    def load_project_file(self, file_path: str):
        success = ProjectIOManager.load_project(file_path, self)
        if success:
            self.current_project_path = file_path
            self.settings["last_open_dir"] = os.path.dirname(file_path)
            self.add_recent_project(file_path)
            self.statusBar().showMessage(i18n.tr("project_loaded"))
            self.update_window_title()
        else:
            QMessageBox.critical(self, "Erreur", f"Impossible de charger le projet : {os.path.basename(file_path)}")

    def save_project(self):
        if not self.current_project_path:
            self.save_project_as_dialog()
        else:
            self.execute_save_project(self.current_project_path)

    def save_project_as_dialog(self):
        last_dir = self.settings.get("last_open_dir", "")
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            i18n.tr("save_as"),
            os.path.join(last_dir, "mon_projet.psa"),
            ProjectIOManager.FILE_FILTER
        )
        if file_path:
            if not file_path.endswith(".psa"):
                file_path += ".psa"
            self.execute_save_project(file_path)

    def execute_save_project(self, file_path: str):
        success = ProjectIOManager.save_project(file_path, self)
        if success:
            self.current_project_path = file_path
            self.settings["last_open_dir"] = os.path.dirname(file_path)
            self.add_recent_project(file_path)
            self.statusBar().showMessage(i18n.tr("project_saved"))
            self.update_window_title()
        else:
            QMessageBox.critical(self, "Erreur", f"Échec de la sauvegarde du projet : {os.path.basename(file_path)}")

    def update_window_title(self):
        title = i18n.tr("app_title")
        if self.current_project_path:
            title += f" - [{os.path.basename(self.current_project_path)}]"
        self.setWindowTitle(title)

    def add_recent_project(self, file_path: str):
        recents = self.settings.get("recent_projects", [])
        if file_path in recents:
            recents.remove(file_path)
        recents.insert(0, file_path)
        self.settings["recent_projects"] = recents[:5]
        self.update_recent_projects_menu()

    def update_recent_projects_menu(self):
        self.recent_menu.clear()
        self.recent_menu.setTitle(i18n.tr("recent_projects"))

        recents = self.settings.get("recent_projects", [])
        if not recents:
            act_none = QAction(i18n.tr("no_recent"), self)
            act_none.setEnabled(False)
            self.recent_menu.addAction(act_none)
        else:
            for path in recents:
                act = QAction(os.path.basename(path), self)
                act.setToolTip(path)
                act.triggered.connect(lambda checked=False, p=path: self.load_project_file(p))
                self.recent_menu.addAction(act)

            self.recent_menu.addSeparator()
            act_clear = QAction(i18n.tr("clear_recent"), self)
            act_clear.triggered.connect(self.clear_recent_projects)
            self.recent_menu.addAction(act_clear)

    def clear_recent_projects(self):
        self.settings["recent_projects"] = []
        self.update_recent_projects_menu()

    # --- Gestion des Nœuds ---
    def add_new_generator(self):
        count = sum(1 for n in self.nodes_registry if isinstance(n, SignalGeneratorNode)) + 1
        gen = self.node_editor.add_generator_node(f"Générateur {count}", x=-850, y=-50 + (count * 30))
        self.nodes_registry.append(gen)
        self.refresh_project_tree()

    
    def add_new_do160_double_exp(self):
        count = sum(1 for n in self.nodes_registry if isinstance(n, DO160DoubleExpNode)) + 1
        node = self.node_editor.add_do160_double_exp_node(f"Impulsion DO-160 {count}", x=-850, y=80 + (count * 30))
        self.nodes_registry.append(node)
        self.refresh_project_tree()

    def add_new_do160_damped_sine(self):
        count = sum(1 for n in self.nodes_registry if isinstance(n, DO160DampedSineNode)) + 1
        node = self.node_editor.add_do160_damped_sine_node(f"Sinus Amorti WF3 {count}", x=-850, y=200 + (count * 30))
        self.nodes_registry.append(node)
        self.refresh_project_tree()

    def add_new_csv_import(self):
        count = sum(1 for n in self.nodes_registry if isinstance(n, CSVImportNode)) + 1
        csv_node = self.node_editor.add_csv_node(f"Import CSV {count}", x=-850, y=320 + (count * 30))
        self.nodes_registry.append(csv_node)
        self.refresh_project_tree()

    def add_new_lowpass_filter(self):
        count = sum(1 for n in self.nodes_registry if isinstance(n, LowPassFilterNode)) + 1
        flt = self.node_editor.add_lowpass_node(f"Filtre Passe-Bas {count}", x=-580, y=-50 + (count * 30))
        self.nodes_registry.append(flt)
        sources = [n for n in self.nodes_registry if isinstance(n, (SignalGeneratorNode, CSVImportNode, DO160DoubleExpNode, DO160DampedSineNode))]
        if sources:
            self.node_editor.create_connection(sources[-1], flt)
        self.refresh_project_tree()

    def add_new_highpass_filter(self):
        count = sum(1 for n in self.nodes_registry if isinstance(n, HighPassFilterNode)) + 1
        flt = self.node_editor.add_highpass_node(f"Filtre Passe-Haut {count}", x=-580, y=10 + (count * 30))
        self.nodes_registry.append(flt)
        sources = [n for n in self.nodes_registry if isinstance(n, (SignalGeneratorNode, CSVImportNode, DO160DoubleExpNode, DO160DampedSineNode))]
        if sources:
            self.node_editor.create_connection(sources[-1], flt)
        self.refresh_project_tree()

    def add_new_bandpass_filter(self):
        count = sum(1 for n in self.nodes_registry if isinstance(n, BandPassFilterNode)) + 1
        flt = self.node_editor.add_bandpass_node(f"Filtre Passe-Bande {count}", x=-580, y=70 + (count * 30))
        self.nodes_registry.append(flt)
        sources = [n for n in self.nodes_registry if isinstance(n, (SignalGeneratorNode, CSVImportNode, DO160DoubleExpNode, DO160DampedSineNode))]
        if sources:
            self.node_editor.create_connection(sources[-1], flt)
        self.refresh_project_tree()

    def add_new_bandstop_filter(self):
        count = sum(1 for n in self.nodes_registry if isinstance(n, BandStopFilterNode)) + 1
        flt = self.node_editor.add_bandstop_node(f"Filtre Coupe-Bande {count}", x=-580, y=130 + (count * 30))
        self.nodes_registry.append(flt)
        sources = [n for n in self.nodes_registry if isinstance(n, (SignalGeneratorNode, CSVImportNode, DO160DoubleExpNode, DO160DampedSineNode))]
        if sources:
            self.node_editor.create_connection(sources[-1], flt)
        self.refresh_project_tree()


    def add_new_derivative(self):
        count = sum(1 for n in self.nodes_registry if isinstance(n, DerivativeNode)) + 1
        node = self.node_editor.add_derivative_node(f"Dérivateur {count}", x=-580, y=190 + (count * 30))
        self.nodes_registry.append(node)

        inputs = [n for n in self.nodes_registry if isinstance(n, PROCESSOR_INPUT_TYPES) and n != node]
        if inputs:
            self.node_editor.create_connection(inputs[-1], node)

        self.refresh_project_tree()

    def add_new_integrator(self):
        count = sum(1 for n in self.nodes_registry if isinstance(n, IntegratorNode)) + 1
        node = self.node_editor.add_integrator_node(f"Intégrateur {count}", x=-580, y=250 + (count * 30))
        self.nodes_registry.append(node)

        inputs = [n for n in self.nodes_registry if isinstance(n, PROCESSOR_INPUT_TYPES) and n != node]
        if inputs:
            self.node_editor.create_connection(inputs[-1], node)

        self.refresh_project_tree()

    def add_new_gain(self):
        count = sum(1 for n in self.nodes_registry if isinstance(n, GainNode)) + 1
        node = self.node_editor.add_gain_node(f"Gain {count}", x=-580, y=310 + (count * 30))
        self.nodes_registry.append(node)

        inputs = [n for n in self.nodes_registry if isinstance(n, PROCESSOR_INPUT_TYPES) and n != node]
        if inputs:
            self.node_editor.create_connection(inputs[-1], node)

        self.refresh_project_tree()

    def add_new_inversion(self):
        count = sum(1 for n in self.nodes_registry if isinstance(n, InversionNode)) + 1
        node = self.node_editor.add_inversion_node(f"Inversion {count}", x=-580, y=370 + (count * 30))
        self.nodes_registry.append(node)
        inputs = [n for n in self.nodes_registry if isinstance(n, PROCESSOR_INPUT_TYPES) and n != node]
        if inputs:
            self.node_editor.create_connection(inputs[-1], node)
        self.refresh_project_tree()

    def add_new_abs(self):
        count = sum(1 for n in self.nodes_registry if isinstance(n, AbsNode)) + 1
        node = self.node_editor.add_abs_node(f"Absolue {count}", x=-580, y=430 + (count * 30))
        self.nodes_registry.append(node)
        inputs = [n for n in self.nodes_registry if isinstance(n, PROCESSOR_INPUT_TYPES) and n != node]
        if inputs:
            self.node_editor.create_connection(inputs[-1], node)
        self.refresh_project_tree()

    def add_new_log(self):
        count = sum(1 for n in self.nodes_registry if isinstance(n, LogNode)) + 1
        node = self.node_editor.add_log_node(f"Logarithme {count}", x=-580, y=490 + (count * 30))
        self.nodes_registry.append(node)
        inputs = [n for n in self.nodes_registry if isinstance(n, PROCESSOR_INPUT_TYPES) and n != node]
        if inputs:
            self.node_editor.create_connection(inputs[-1], node)
        self.refresh_project_tree()

    def add_new_exp(self):
        count = sum(1 for n in self.nodes_registry if isinstance(n, ExpNode)) + 1
        node = self.node_editor.add_exp_node(f"Exponentielle {count}", x=-580, y=550 + (count * 30))
        self.nodes_registry.append(node)
        inputs = [n for n in self.nodes_registry if isinstance(n, PROCESSOR_INPUT_TYPES) and n != node]
        if inputs:
            self.node_editor.create_connection(inputs[-1], node)
        self.refresh_project_tree()

    def add_new_noise(self):
        count = sum(1 for n in self.nodes_registry if isinstance(n, NoiseNode)) + 1
        node = self.node_editor.add_noise_node(f"Injecteur de Bruit {count}", x=-580, y=610 + (count * 30))
        self.nodes_registry.append(node)
        inputs = [n for n in self.nodes_registry if isinstance(n, PROCESSOR_INPUT_TYPES) and n != node]
        if inputs:
            self.node_editor.create_connection(inputs[-1], node)
        self.refresh_project_tree()

    def add_new_resample(self):
        count = sum(1 for n in self.nodes_registry if isinstance(n, ResampleNode)) + 1
        node = self.node_editor.add_resample_node(f"Rééchantillonnage {count}", x=-580, y=670 + (count * 30))
        self.nodes_registry.append(node)
        inputs = [n for n in self.nodes_registry if isinstance(n, PROCESSOR_INPUT_TYPES) and n != node]
        if inputs:
            self.node_editor.create_connection(inputs[-1], node)
        self.refresh_project_tree()

    def add_new_interpolation(self):
        count = sum(1 for n in self.nodes_registry if isinstance(n, InterpolationNode)) + 1
        node = self.node_editor.add_interpolation_node(f"Interpolation {count}", x=-580, y=730 + (count * 30))
        self.nodes_registry.append(node)
        inputs = [n for n in self.nodes_registry if isinstance(n, PROCESSOR_INPUT_TYPES) and n != node]
        if inputs:
            self.node_editor.create_connection(inputs[-1], node)
        self.refresh_project_tree()

    def add_new_dac(self):
        count = sum(1 for n in self.nodes_registry if isinstance(n, DACNode)) + 1
        node = self.node_editor.add_dac_node(f"Simulation DAC {count}", x=-580, y=790 + (count * 30))
        self.nodes_registry.append(node)
        inputs = [n for n in self.nodes_registry if isinstance(n, PROCESSOR_INPUT_TYPES) and n != node]
        if inputs:
            self.node_editor.create_connection(inputs[-1], node)
        self.refresh_project_tree()

    def add_new_fixed_avg(self):
        count = sum(1 for n in self.nodes_registry if isinstance(n, FixedAverageNode)) + 1
        node = self.node_editor.add_fixed_average_node(f"Moyenne Fixe {count}", x=-580, y=850 + (count * 30))
        self.nodes_registry.append(node)
        inputs = [n for n in self.nodes_registry if isinstance(n, PROCESSOR_INPUT_TYPES) and n != node]
        if inputs:
            self.node_editor.create_connection(inputs[-1], node)
        self.refresh_project_tree()

    def add_new_moving_avg(self):
        count = sum(1 for n in self.nodes_registry if isinstance(n, MovingAverageNode)) + 1
        node = self.node_editor.add_moving_average_node(f"Moyenne Glissante {count}", x=-580, y=910 + (count * 30))
        self.nodes_registry.append(node)
        inputs = [n for n in self.nodes_registry if isinstance(n, PROCESSOR_INPUT_TYPES) and n != node]
        if inputs:
            self.node_editor.create_connection(inputs[-1], node)
        self.refresh_project_tree()

    def add_new_addition(self):
        count = sum(1 for n in self.nodes_registry if isinstance(n, AdditionNode)) + 1
        node = self.node_editor.add_addition_node(f"Addition {count}", x=-580, y=970 + (count * 30))
        self.nodes_registry.append(node)

        inputs = [n for n in self.nodes_registry if isinstance(n, PROCESSOR_INPUT_TYPES) and n != node]
        if len(inputs) >= 1:
            self.node_editor.create_connection(inputs[-1], node, target_port="a")
        if len(inputs) >= 2:
            self.node_editor.create_connection(inputs[-2], node, target_port="b")

        self.refresh_project_tree()

    def add_new_power(self):
        count = sum(1 for n in self.nodes_registry if isinstance(n, PowerNode)) + 1
        node = self.node_editor.add_power_node(f"Puissance {count}", x=-580, y=1030 + (count * 30))
        self.nodes_registry.append(node)
        inputs = [n for n in self.nodes_registry if isinstance(n, PROCESSOR_INPUT_TYPES) and n != node]
        if inputs:
            self.node_editor.create_connection(inputs[-1], node)
        self.refresh_project_tree()

    def add_new_thd_analysis(self):
        count = sum(1 for n in self.nodes_registry if isinstance(n, THDAnalysisNode)) + 1
        node = self.node_editor.add_thd_node(f"Analyse THD {count}", x=-310, y=-50 + (count * 30))
        self.nodes_registry.append(node)

        inputs = [n for n in self.nodes_registry if isinstance(n, PROCESSOR_INPUT_TYPES) and n != node]
        if inputs:
            self.node_editor.create_connection(inputs[-1], node)

        self.refresh_project_tree()

    def add_new_fft_analysis(self):
        count = sum(1 for n in self.nodes_registry if isinstance(n, FFTAnalysisNode)) + 1
        fft_node = self.node_editor.add_fft_node(f"Analyse FFT {count}", x=-310, y=100 + (count * 30))
        self.nodes_registry.append(fft_node)

        inputs = [n for n in self.nodes_registry if isinstance(n, PROCESSOR_INPUT_TYPES) and n != node]
        if inputs:
            self.node_editor.create_connection(inputs[-1], fft_node)

        self.refresh_project_tree()

    def delete_node(self, node):
        if node not in self.nodes_registry:
            return

        to_remove_conns = list(node.connections)
        for conn in to_remove_conns:
            self.node_editor.delete_connection(conn)

        for n in self.nodes_registry:
            if hasattr(n, "input_node_a") and n.input_node_a == node:
                n.input_node_a = None
                n.mark_dirty()
            if hasattr(n, "input_node_b") and n.input_node_b == node:
                n.input_node_b = None
                n.mark_dirty()
            if hasattr(n, "input_node") and n.input_node == node:
                n.input_node = None
                n.mark_dirty()

        if node.scene() == self.node_editor.scene:
            self.node_editor.scene.removeItem(node)
        self.nodes_registry.remove(node)

        self.right_tabs.clear()
        self.refresh_project_tree()
        self.update_open_tabs_for_all_nodes()

    def add_new_median_filter(self):
        count = sum(1 for n in self.nodes_registry if isinstance(n, MedianFilterNode)) + 1
        node = self.node_editor.add_median_filter_node(f"Filtre Médian {count}", x=120, y=300 + (count * 30))
        self.nodes_registry.append(node)

        inputs = [n for n in self.nodes_registry if isinstance(n, PROCESSOR_INPUT_TYPES) and n != node]
        if inputs:
            self.node_editor.create_connection(inputs[-1], node)

        self.refresh_project_tree()

    def refresh_project_tree(self):
        self.tree_widget.clear()

        sources = [n for n in self.nodes_registry if isinstance(n, (SignalGeneratorNode, CSVImportNode, DO160DoubleExpNode, DO160DampedSineNode))]
        do160_nodes = [n for n in self.nodes_registry if isinstance(n, (DO160DoubleExpNode, DO160DampedSineNode))]
        filters = [n for n in self.nodes_registry if isinstance(n, (LowPassFilterNode, HighPassFilterNode, BandPassFilterNode, BandStopFilterNode))]
        dsp_filters = [n for n in self.nodes_registry if isinstance(n, (FixedAverageNode, MovingAverageNode, MedianFilterNode))]
        maths = [n for n in self.nodes_registry if isinstance(n, (DerivativeNode, IntegratorNode, GainNode, InversionNode, AbsNode, LogNode, ExpNode, PowerNode, AdditionNode))]
        noises = [n for n in self.nodes_registry if isinstance(n, NoiseNode)]
        samplings = [n for n in self.nodes_registry if isinstance(n, (ResampleNode, InterpolationNode, DACNode))]
        analyses = [n for n in self.nodes_registry if isinstance(n, (FFTAnalysisNode, THDAnalysisNode))]

        signal_roots = sources + do160_nodes + samplings + [n for n in self.nodes_registry if isinstance(n, FixedAverageNode)]

        if sources:
            sources_root = QTreeWidgetItem(self.tree_widget, [i18n.tr("sources_cat")])
            for src in sources:
                warning_prefix = "⚠️ " if src.is_dirty else ""
                type_label = "Générateur" if isinstance(src, SignalGeneratorNode) else "CSV"
                src_item = QTreeWidgetItem(sources_root, [f"{warning_prefix}{src.params['name']} ({type_label})"])
                src_item.setData(0, Qt.UserRole, {"type": "node", "obj": src})

        if do160_nodes:
            do160_root = QTreeWidgetItem(self.tree_widget, [i18n.tr("do160_cat")])
            for d_node in do160_nodes:
                warning_prefix = "⚠️ " if d_node.is_dirty else ""
                d_item = QTreeWidgetItem(do160_root, [f"{warning_prefix}{d_node.params['name']}"])
                d_item.setData(0, Qt.UserRole, {"type": "node", "obj": d_node})

        if filters:
            filters_root = QTreeWidgetItem(self.tree_widget, [i18n.tr("filters_cat")])
            for flt in filters:
                warning_prefix = "⚠️ " if flt.is_dirty else ""
                flt_item = QTreeWidgetItem(filters_root, [f"{warning_prefix}{flt.params['name']}"])
                flt_item.setData(0, Qt.UserRole, {"type": "node", "obj": flt})

        if dsp_filters:
            dsp_root = QTreeWidgetItem(self.tree_widget, [i18n.tr("dsp_cat")])
            for d_node in dsp_filters:
                warning_prefix = "⚠️ " if d_node.is_dirty else ""
                d_item = QTreeWidgetItem(dsp_root, [f"{warning_prefix}{d_node.params['name']}"])
                d_item.setData(0, Qt.UserRole, {"type": "node", "obj": d_node})

        if maths:
            maths_root = QTreeWidgetItem(self.tree_widget, [i18n.tr("maths_cat")])
            for m_node in maths:
                warning_prefix = "⚠️ " if m_node.is_dirty else ""
                m_item = QTreeWidgetItem(maths_root, [f"{warning_prefix}{m_node.params['name']}"])
                m_item.setData(0, Qt.UserRole, {"type": "node", "obj": m_node})

        if noises:
            noise_root = QTreeWidgetItem(self.tree_widget, [i18n.tr("noise_cat")])
            for n_node in noises:
                warning_prefix = "⚠️ " if n_node.is_dirty else ""
                n_item = QTreeWidgetItem(noise_root, [f"{warning_prefix}{n_node.params['name']}"])
                n_item.setData(0, Qt.UserRole, {"type": "node", "obj": n_node})

        if samplings:
            sampling_root = QTreeWidgetItem(self.tree_widget, [i18n.tr("sampling_cat")])
            for s_node in samplings:
                warning_prefix = "⚠️ " if s_node.is_dirty else ""
                s_item = QTreeWidgetItem(sampling_root, [f"{warning_prefix}{s_node.params['name']}"])
                s_item.setData(0, Qt.UserRole, {"type": "node", "obj": s_node})

        if analyses:
            analyses_root = QTreeWidgetItem(self.tree_widget, [i18n.tr("analyses_cat")])
            for fft in analyses:
                warning_prefix = "⚠️ " if fft.is_dirty else ""
                fft_item = QTreeWidgetItem(analyses_root, [f"{warning_prefix}{fft.params['name']}"])
                fft_item.setData(0, Qt.UserRole, {"type": "node", "obj": fft})

        if signal_roots:
            signals_root = QTreeWidgetItem(self.tree_widget, [i18n.tr("signals_cat")])
            for sig in signal_roots:
                warning_prefix = "⚠️ " if sig.is_dirty else ""
                type_tag = f" ({sig.params['name']})" if isinstance(sig, (ResampleNode, InterpolationNode, DACNode)) else ""
                sig_item = QTreeWidgetItem(signals_root, [f"{warning_prefix}Pipeline Signal : {sig.params['name']}"])
                sig_item.setData(0, Qt.UserRole, {"type": "signal", "obj": sig})

        self.tree_widget.expandAll()

    # --- Connexions Nœuds ---
    def connect_nodes(self, source_node, target_node, target_port="a"):
        if source_node is None:
            self.node_editor.remove_connection_for_target(target_node)
        else:
            self.node_editor.create_connection(source_node, target_node, target_port=target_port)
        
        self.refresh_project_tree()

    def on_wire_connected(self, source_node, target_node):
        self.refresh_project_tree()
        self.update_open_tabs_for_all_nodes()

    # --- Visualisations des Données (Temporel & Fréquentiel) ---
    def recalculate_from_node(self, start_node):
        """Recalcule start_node et tous ses nœuds dépendants en aval, puis met à jour les onglets ouverts."""
        if not start_node:
            return

        affected = [start_node]
        added = True
        while added:
            added = False
            for n in self.nodes_registry:
                if n not in affected and getattr(n, "input_node", None) in affected:
                    affected.append(n)
                    added = True

        for n in affected:
            n.recalculate()
            self.update_open_tabs_for_node(n)

        self.refresh_project_tree()
        self.update_active_param_widget_status()

    def get_pipeline_data(self, target_node):
        """
        Construit le dictionnaire de données pour l'affichage graphique/tableau.
        Gère à la fois les signaux temporels (pipelines) et les spectres fréquentiels (FFT).
        Chaque nœud créant une nouvelle base temporelle (Générateur, CSV, Rééchantillonnage, Interpolation, DAC)
        constitue sa propre racine de domaine temporel.
        """
        if not target_node:
            return None, {}, "Temps (s)", "Amplitude (V)"

        if getattr(target_node, "node_type", "") == "thd_analysis":
            unit_str = target_node.params.get("display_unit", "% de la Fondamentale")
            x_label = "Ordre Harmonique (k)"
            columns_dict = {}
            if target_node.harm_orders is not None and target_node.harm_v_raw is not None and len(target_node.harm_v_raw) > 0:
                v1_val = target_node.v1_amp if target_node.v1_amp > 1e-12 else 1.0
                if "dB" in unit_str:
                    y_label = "Niveau (dB)"
                    col_name = f"Niveau (dB) - {target_node.params['name']}"
                    db_vals = 20.0 * np.log10(np.maximum(target_node.harm_v_raw / v1_val, 1e-6)) if target_node.v1_amp > 1e-12 else 20.0 * np.log10(np.maximum(target_node.harm_v_raw, 1e-6))
                    columns_dict[col_name] = (target_node.harm_orders, db_vals)
                elif "V" in unit_str or "Amplitude" in unit_str:
                    y_label = "Amplitude (V)"
                    col_name = f"Amplitude (V) - {target_node.params['name']}"
                    columns_dict[col_name] = (target_node.harm_orders, target_node.harm_v_raw)
                else:
                    y_label = "Niveau (% de f0)"
                    col_name = f"Niveau (%) - {target_node.params['name']}"
                    pct_vals = (target_node.harm_v_raw / v1_val) * 100.0 if target_node.v1_amp > 1e-12 else np.zeros_like(target_node.harm_v_raw)
                    columns_dict[col_name] = (target_node.harm_orders, pct_vals)

                return target_node.harm_orders, columns_dict, x_label, y_label
            else:
                return None, {}, x_label, "Niveau (%)"

        if getattr(target_node, "node_type", "") == "fft_analysis":
            x_label = "Fréquence (Hz)"
            y_label = target_node.params.get("unit", "Amplitude (V)")
            if target_node.t_data is not None and target_node.y_data is not None:
                columns_dict = {f"Spectre FFT ({target_node.params['name']})": (target_node.t_data, target_node.y_data)}
                return target_node.t_data, columns_dict, x_label, y_label
            else:
                return None, {}, x_label, y_label

        # Unité de l'axe Y pour le DAC
        y_label = "Amplitude (V)"
        if getattr(target_node, "node_type", "") == "dac_simulation":
            unit_str = str(target_node.params.get("output_unit", "")).lower()
            if "lsb" in unit_str or "code" in unit_str:
                y_label = "Code Numérique (LSB)"

        # Signaux du domaine temporel : remonter jusqu'à la racine du domaine temporel courant
        curr = target_node
        domain_root = target_node
        while curr:
            domain_root = curr
            if isinstance(curr, (SignalGeneratorNode, CSVImportNode, DO160DoubleExpNode, DO160DampedSineNode, ResampleNode, InterpolationNode, DACNode, FixedAverageNode, AdditionNode)):
                break
            if hasattr(curr, "input_node") and curr.input_node:
                if curr.input_node.t_data is not None and curr.t_data is not None and len(curr.input_node.t_data) != len(curr.t_data):
                    break
                curr = curr.input_node
            else:
                break

        if not domain_root or domain_root.t_data is None:
            return None, {}, "Temps (s)", y_label

        t = domain_root.t_data
        columns_dict = {}

        pipeline_nodes = [domain_root]
        added = True
        while added:
            added = False
            for n in self.nodes_registry:
                if n not in pipeline_nodes and hasattr(n, "input_node") and n.input_node in pipeline_nodes:
                    if not isinstance(n, (FFTAnalysisNode, ResampleNode, InterpolationNode, DACNode, FixedAverageNode, AdditionNode)):
                        if n.t_data is not None and len(n.t_data) == len(t):
                            pipeline_nodes.append(n)
                            added = True

        if isinstance(target_node, AdditionNode):
            t = target_node.t_data if target_node.t_data is not None else t
            if target_node.input_node_a and target_node.input_node_a.y_data is not None:
                t_a = target_node.input_node_a.t_data
                y_a = target_node.input_node_a.y_data
                kA = float(target_node.params.get("coef_a", 1.0))
                y_a_val = kA * y_a
                if t is not None and len(t_a) == len(t):
                    columns_dict[f"Signal A ({target_node.input_node_a.params['name']})"] = (t_a, y_a_val)
                elif t is not None:
                    columns_dict[f"Signal A ({target_node.input_node_a.params['name']})"] = (t, np.interp(t, t_a, y_a_val, left=0.0, right=0.0))

            if target_node.input_node_b and target_node.input_node_b.y_data is not None:
                t_b = target_node.input_node_b.t_data
                y_b = target_node.input_node_b.y_data
                kB = float(target_node.params.get("coef_b", 1.0))
                y_b_val = kB * y_b
                if t is not None and len(t_b) == len(t):
                    columns_dict[f"Signal B ({target_node.input_node_b.params['name']})"] = (t_b, y_b_val)
                elif t is not None:
                    columns_dict[f"Signal B ({target_node.input_node_b.params['name']})"] = (t, np.interp(t, t_b, y_b_val, left=0.0, right=0.0))

            if target_node.y_data is not None and t is not None:
                columns_dict[f"{target_node.params['name']} (Somme)"] = (t, target_node.y_data)
        else:
            for n in pipeline_nodes:
                if n.y_data is not None and n.t_data is not None and len(n.y_data) == len(t):
                    if n == domain_root and isinstance(n, (SignalGeneratorNode, CSVImportNode, DO160DoubleExpNode, DO160DampedSineNode)):
                        columns_dict[f"Brut ({n.params['name']})"] = (n.t_data, n.y_data)
                    else:
                        columns_dict[f"{n.params['name']}"] = (n.t_data, n.y_data)

        return t, columns_dict, "Temps (s)", y_label

    def open_graph_for_node(self, node):
        title = f"Graph : {node.params['name']}"
        x_vec, columns_dict, x_label, y_label = self.get_pipeline_data(node)
        return self.open_matplotlib_tab(title, node, columns_dict, x_label, y_label)

    def open_table_for_node(self, node):
        title = f"Tableau : {node.params['name']}"
        if getattr(node, "node_type", "") == "thd_analysis":
            x_vec = node.harm_orders
            x_label = "Ordre Harmonique (k)"
            columns_dict = {}
            if node.harm_orders is not None and node.harm_v_raw is not None and len(node.harm_v_raw) > 0:
                columns_dict["Fréquence (Hz)"] = (node.harm_orders, node.harm_freqs)
                columns_dict["Amplitude (V)"] = (node.harm_orders, node.harm_v_raw)
                v1_val = node.v1_amp if node.v1_amp > 1e-12 else 1.0
                pct_vals = (node.harm_v_raw / v1_val) * 100.0 if node.v1_amp > 1e-12 else np.zeros_like(node.harm_v_raw)
                columns_dict["Niveau (%)"] = (node.harm_orders, pct_vals)
                db_vals = 20.0 * np.log10(np.maximum(node.harm_v_raw / v1_val, 1e-6)) if node.v1_amp > 1e-12 else 20.0 * np.log10(np.maximum(node.harm_v_raw, 1e-6))
                columns_dict["Niveau (dB)"] = (node.harm_orders, db_vals)
            self.open_numpy_tab(title, node, x_vec, columns_dict, x_label)
            return

        x_vec, columns_dict, x_label, y_label = self.get_pipeline_data(node)
        self.open_numpy_tab(title, node, x_vec, columns_dict, x_label)

    def export_csv_for_node(self, node):
        """Exporte les données du pipeline associées au nœud directement au format CSV."""
        x_vec, columns_dict, x_label, y_label = self.get_pipeline_data(node)
        if x_vec is None or not columns_dict:
            QMessageBox.warning(self, i18n.tr("warning"), "Aucune donnée disponible à exporter pour ce nœud.")
            return

        default_name = f"export_{node.params.get('name', 'node')}.csv"
        last_dir = self.settings.get("last_open_dir", "")
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            i18n.tr("export_table_csv"),
            os.path.join(last_dir, default_name),
            "Fichier CSV (*.csv);;Fichier Texte (*.txt);;Tous les fichiers (*)"
        )
        if not file_path:
            return

        delimiter = ";" if file_path.endswith(".csv") else "	"
        headers = [x_label] + list(columns_dict.keys())

        max_rows = max([len(x_vec)] + [len(y) for (t_v, y) in columns_dict.values() if y is not None])

        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(delimiter.join(headers) + "\n")
                for r in range(max_rows):
                    row_vals = []
                    row_vals.append(f"{x_vec[r]:.6f}" if r < len(x_vec) else "")
                    for col_name, (t_v, y) in columns_dict.items():
                        row_vals.append(f"{y[r]:.6f}" if (y is not None and r < len(y)) else "")
                    f.write(delimiter.join(row_vals) + "\n")
            self.statusBar().showMessage(f"Données exportées en CSV : {os.path.basename(file_path)}")
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors de l'exportation CSV : {e}")

    def show_tree_context_menu(self, pos):
        item = self.tree_widget.itemAt(pos)
        if not item:
            return

        data = item.data(0, Qt.UserRole)
        if not data:
            return

        node = data["obj"]
        menu = QMenu(self)

        act_graph = menu.addAction(i18n.tr("view_graph"))
        act_table = menu.addAction(i18n.tr("view_table"))
        act_export = menu.addAction(i18n.tr("export_csv_action"))
        menu.addSeparator()
        act_params = menu.addAction(i18n.tr("edit_params"))
        menu.addSeparator()
        act_del = menu.addAction(i18n.tr("delete_node"))

        action = menu.exec(self.tree_widget.mapToGlobal(pos))
        if action == act_graph:
            self.open_graph_for_node(node)
        elif action == act_table:
            self.open_table_for_node(node)
        elif action == act_export:
            self.export_csv_for_node(node)
        elif action == act_params:
            self.node_editor.scene.clearSelection()
            node.setSelected(True)
            self.node_editor.centerOn(node)
            self.open_node_params_tab(node)
        elif action == act_del:
            self.delete_node(node)

    # --- Interactions Clics / Sélections ---
    def on_node_selected(self, node):
        self.open_node_params_tab(node)

    def on_node_double_clicked(self, node):
        self.open_graph_for_node(node)

    def on_tree_item_clicked(self, item, column):
        data = item.data(0, Qt.UserRole)
        if not data:
            return

        node = data["obj"]
        if data["type"] == "node":
            self.node_editor.scene.clearSelection()
            node.setSelected(True)
            self.node_editor.centerOn(node)
            self.open_node_params_tab(node)

    def on_tree_item_double_clicked(self, item, column):
        data = item.data(0, Qt.UserRole)
        if not data:
            return

        node = data["obj"]
        if data["type"] == "signal":
            self.open_graph_for_node(node)

    def recalc_all_nodes(self):
        recalculated = set()
        nodes_to_recalc = list(self.nodes_registry)
        
        while nodes_to_recalc:
            progress = False
            for n in list(nodes_to_recalc):
                input_node = getattr(n, "input_node", None)
                if input_node is None or input_node in recalculated or input_node not in self.nodes_registry:
                    n.recalculate()
                    recalculated.add(n)
                    nodes_to_recalc.remove(n)
                    progress = True
            if not progress:
                for n in nodes_to_recalc:
                    n.recalculate()
                break

        self.refresh_project_tree()
        self.update_open_tabs_for_all_nodes()
        self.statusBar().showMessage("Projet entièrement recalculé.")

    def update_active_param_widget_status(self):
        if hasattr(self, "right_tabs") and self.right_tabs.count() > 0:
            scroll = self.right_tabs.widget(0)
            if scroll and hasattr(scroll, "widget"):
                p_widget = scroll.widget()
                if hasattr(p_widget, "update_status_label"):
                    p_widget.update_status_label()

    def on_node_param_changed(self, node, executed: bool = False):
        if executed:
            self.recalculate_from_node(node)
        else:
            dirty_nodes = [node]
            added = True
            while added:
                added = False
                for n in self.nodes_registry:
                    if n not in dirty_nodes and getattr(n, "input_node", None) in dirty_nodes:
                        dirty_nodes.append(n)
                        n.mark_dirty()
                        added = True

            self.refresh_project_tree()

    def update_open_tabs_for_node(self, node):
        x_vec, columns_dict, x_label, y_label = self.get_pipeline_data(node)
        for i in range(self.center_tabs.count()):
            widget = self.center_tabs.widget(i)
            if getattr(widget, "associated_node", None) == node:
                if isinstance(widget, MplCanvasWidget):
                    widget.update_multi_plot(columns_dict, title=f"Graph : {node.params['name']}", x_label=x_label, y_label=y_label)
                    self.center_tabs.setTabText(i, f"Graph : {node.params['name']}")
                elif isinstance(widget, NumPyArrayTableWidget):
                    widget.set_multi_signal_data(x_vec, columns_dict, x_label=x_label)
                    self.center_tabs.setTabText(i, f"Tableau : {node.params['name']}")

    def update_open_tabs_for_all_nodes(self):
        for node in self.nodes_registry:
            self.update_open_tabs_for_node(node)

    # --- Gestion des Onglets ---
    def open_node_params_tab(self, node):
        self.right_tabs.clear()
        if isinstance(node, SignalGeneratorNode):
            param_widget = SignalGeneratorParamWidget(
                node,
                on_recalculate_cb=self.on_node_param_changed,
                on_view_graph_cb=self.open_graph_for_node,
                on_view_table_cb=self.open_table_for_node,
                on_export_csv_cb=self.export_csv_for_node,
                on_delete_cb=self.delete_node
            )
        elif isinstance(node, DO160DoubleExpNode):
            param_widget = DO160DoubleExpParamWidget(
                node,
                on_recalculate_cb=self.on_node_param_changed,
                on_view_graph_cb=self.open_graph_for_node,
                on_view_table_cb=self.open_table_for_node,
                on_export_csv_cb=self.export_csv_for_node,
                on_delete_cb=self.delete_node
            )
        elif isinstance(node, DO160DampedSineNode):
            param_widget = DO160DampedSineParamWidget(
                node,
                on_recalculate_cb=self.on_node_param_changed,
                on_view_graph_cb=self.open_graph_for_node,
                on_view_table_cb=self.open_table_for_node,
                on_export_csv_cb=self.export_csv_for_node,
                on_delete_cb=self.delete_node
            )
        elif isinstance(node, CSVImportNode):
            param_widget = CSVImportParamWidget(
                node,
                on_recalculate_cb=self.on_node_param_changed,
                on_view_graph_cb=self.open_graph_for_node,
                on_view_table_cb=self.open_table_for_node,
                on_export_csv_cb=self.export_csv_for_node,
                on_delete_cb=self.delete_node
            )
        elif isinstance(node, LowPassFilterNode):
            available_sources = [n for n in self.nodes_registry if isinstance(n, PROCESSOR_INPUT_TYPES) and n != node]
            param_widget = LowPassFilterParamWidget(
                node,
                available_sources=available_sources,
                on_recalculate_cb=self.on_node_param_changed,
                on_connect_cb=self.connect_nodes,
                on_view_graph_cb=self.open_graph_for_node,
                on_view_table_cb=self.open_table_for_node,
                on_export_csv_cb=self.export_csv_for_node,
                on_delete_cb=self.delete_node
            )
        elif isinstance(node, HighPassFilterNode):
            available_sources = [n for n in self.nodes_registry if isinstance(n, PROCESSOR_INPUT_TYPES) and n != node]
            param_widget = HighPassFilterParamWidget(
                node,
                available_sources=available_sources,
                on_recalculate_cb=self.on_node_param_changed,
                on_connect_cb=self.connect_nodes,
                on_view_graph_cb=self.open_graph_for_node,
                on_view_table_cb=self.open_table_for_node,
                on_export_csv_cb=self.export_csv_for_node,
                on_delete_cb=self.delete_node
            )
        elif isinstance(node, BandPassFilterNode):
            available_sources = [n for n in self.nodes_registry if isinstance(n, PROCESSOR_INPUT_TYPES) and n != node]
            param_widget = BandPassFilterParamWidget(
                node,
                available_sources=available_sources,
                on_recalculate_cb=self.on_node_param_changed,
                on_connect_cb=self.connect_nodes,
                on_view_graph_cb=self.open_graph_for_node,
                on_view_table_cb=self.open_table_for_node,
                on_export_csv_cb=self.export_csv_for_node,
                on_delete_cb=self.delete_node
            )
        elif isinstance(node, BandStopFilterNode):
            available_sources = [n for n in self.nodes_registry if isinstance(n, PROCESSOR_INPUT_TYPES) and n != node]
            param_widget = BandStopFilterParamWidget(
                node,
                available_sources=available_sources,
                on_recalculate_cb=self.on_node_param_changed,
                on_connect_cb=self.connect_nodes,
                on_view_graph_cb=self.open_graph_for_node,
                on_view_table_cb=self.open_table_for_node,
                on_export_csv_cb=self.export_csv_for_node,
                on_delete_cb=self.delete_node
            )
        elif isinstance(node, DerivativeNode):
            available_sources = [n for n in self.nodes_registry if isinstance(n, PROCESSOR_INPUT_TYPES) and n != node]
            param_widget = DerivativeParamWidget(
                node,
                available_sources=available_sources,
                on_recalculate_cb=self.on_node_param_changed,
                on_connect_cb=self.connect_nodes,
                on_view_graph_cb=self.open_graph_for_node,
                on_view_table_cb=self.open_table_for_node,
                on_export_csv_cb=self.export_csv_for_node,
                on_delete_cb=self.delete_node
            )
        elif isinstance(node, IntegratorNode):
            available_sources = [n for n in self.nodes_registry if isinstance(n, PROCESSOR_INPUT_TYPES) and n != node]
            param_widget = IntegratorParamWidget(
                node,
                available_sources=available_sources,
                on_recalculate_cb=self.on_node_param_changed,
                on_connect_cb=self.connect_nodes,
                on_view_graph_cb=self.open_graph_for_node,
                on_view_table_cb=self.open_table_for_node,
                on_export_csv_cb=self.export_csv_for_node,
                on_delete_cb=self.delete_node
            )
        elif isinstance(node, GainNode):
            available_sources = [n for n in self.nodes_registry if isinstance(n, PROCESSOR_INPUT_TYPES) and n != node]
            param_widget = GainParamWidget(
                node,
                available_sources=available_sources,
                on_recalculate_cb=self.on_node_param_changed,
                on_connect_cb=self.connect_nodes,
                on_view_graph_cb=self.open_graph_for_node,
                on_view_table_cb=self.open_table_for_node,
                on_export_csv_cb=self.export_csv_for_node,
                on_delete_cb=self.delete_node
            )
        elif isinstance(node, InversionNode):
            available_sources = [n for n in self.nodes_registry if isinstance(n, PROCESSOR_INPUT_TYPES) and n != node]
            param_widget = InversionParamWidget(
                node,
                available_sources=available_sources,
                on_recalculate_cb=self.on_node_param_changed,
                on_connect_cb=self.connect_nodes,
                on_view_graph_cb=self.open_graph_for_node,
                on_view_table_cb=self.open_table_for_node,
                on_export_csv_cb=self.export_csv_for_node,
                on_delete_cb=self.delete_node
            )
        elif isinstance(node, AbsNode):
            available_sources = [n for n in self.nodes_registry if isinstance(n, PROCESSOR_INPUT_TYPES) and n != node]
            param_widget = AbsParamWidget(
                node,
                available_sources=available_sources,
                on_recalculate_cb=self.on_node_param_changed,
                on_connect_cb=self.connect_nodes,
                on_view_graph_cb=self.open_graph_for_node,
                on_view_table_cb=self.open_table_for_node,
                on_export_csv_cb=self.export_csv_for_node,
                on_delete_cb=self.delete_node
            )
        elif isinstance(node, LogNode):
            available_sources = [n for n in self.nodes_registry if isinstance(n, PROCESSOR_INPUT_TYPES) and n != node]
            param_widget = LogParamWidget(
                node,
                available_sources=available_sources,
                on_recalculate_cb=self.on_node_param_changed,
                on_connect_cb=self.connect_nodes,
                on_view_graph_cb=self.open_graph_for_node,
                on_view_table_cb=self.open_table_for_node,
                on_export_csv_cb=self.export_csv_for_node,
                on_delete_cb=self.delete_node
            )
        elif isinstance(node, ExpNode):
            available_sources = [n for n in self.nodes_registry if isinstance(n, PROCESSOR_INPUT_TYPES) and n != node]
            param_widget = ExpParamWidget(
                node,
                available_sources=available_sources,
                on_recalculate_cb=self.on_node_param_changed,
                on_connect_cb=self.connect_nodes,
                on_view_graph_cb=self.open_graph_for_node,
                on_view_table_cb=self.open_table_for_node,
                on_export_csv_cb=self.export_csv_for_node,
                on_delete_cb=self.delete_node
            )
        elif isinstance(node, AdditionNode):
            available_sources = [n for n in self.nodes_registry if isinstance(n, PROCESSOR_INPUT_TYPES) and n != node]
            param_widget = AdditionParamWidget(
                node,
                available_sources=available_sources,
                on_recalculate_cb=self.on_node_param_changed,
                on_connect_cb=self.connect_nodes,
                on_view_graph_cb=self.open_graph_for_node,
                on_view_table_cb=self.open_table_for_node,
                on_export_csv_cb=self.export_csv_for_node,
                on_delete_cb=self.delete_node
            )
        elif isinstance(node, PowerNode):
            available_sources = [n for n in self.nodes_registry if isinstance(n, PROCESSOR_INPUT_TYPES) and n != node]
            param_widget = PowerParamWidget(
                node,
                available_sources=available_sources,
                on_recalculate_cb=self.on_node_param_changed,
                on_connect_cb=self.connect_nodes,
                on_view_graph_cb=self.open_graph_for_node,
                on_view_table_cb=self.open_table_for_node,
                on_export_csv_cb=self.export_csv_for_node,
                on_delete_cb=self.delete_node
            )
        elif isinstance(node, NoiseNode):
            available_sources = [n for n in self.nodes_registry if isinstance(n, PROCESSOR_INPUT_TYPES) and n != node]
            param_widget = NoiseParamWidget(
                node,
                available_sources=available_sources,
                on_recalculate_cb=self.on_node_param_changed,
                on_connect_cb=self.connect_nodes,
                on_view_graph_cb=self.open_graph_for_node,
                on_view_table_cb=self.open_table_for_node,
                on_export_csv_cb=self.export_csv_for_node,
                on_delete_cb=self.delete_node
            )
        elif isinstance(node, ResampleNode):
            available_sources = [n for n in self.nodes_registry if isinstance(n, PROCESSOR_INPUT_TYPES) and n != node]
            param_widget = ResampleParamWidget(
                node,
                available_sources=available_sources,
                on_recalculate_cb=self.on_node_param_changed,
                on_connect_cb=self.connect_nodes,
                on_view_graph_cb=self.open_graph_for_node,
                on_view_table_cb=self.open_table_for_node,
                on_export_csv_cb=self.export_csv_for_node,
                on_delete_cb=self.delete_node
            )
        elif isinstance(node, InterpolationNode):
            available_sources = [n for n in self.nodes_registry if isinstance(n, PROCESSOR_INPUT_TYPES) and n != node]
            param_widget = InterpolationParamWidget(
                node,
                available_sources=available_sources,
                on_recalculate_cb=self.on_node_param_changed,
                on_connect_cb=self.connect_nodes,
                on_view_graph_cb=self.open_graph_for_node,
                on_view_table_cb=self.open_table_for_node,
                on_export_csv_cb=self.export_csv_for_node,
                on_delete_cb=self.delete_node
            )
        elif isinstance(node, DACNode):
            available_sources = [n for n in self.nodes_registry if isinstance(n, PROCESSOR_INPUT_TYPES) and n != node]
            param_widget = DACParamWidget(
                node,
                available_sources=available_sources,
                on_recalculate_cb=self.on_node_param_changed,
                on_connect_cb=self.connect_nodes,
                on_view_graph_cb=self.open_graph_for_node,
                on_view_table_cb=self.open_table_for_node,
                on_export_csv_cb=self.export_csv_for_node,
                on_delete_cb=self.delete_node
            )
        elif isinstance(node, FixedAverageNode):
            available_sources = [n for n in self.nodes_registry if isinstance(n, PROCESSOR_INPUT_TYPES) and n != node]
            param_widget = FixedAverageParamWidget(
                node,
                available_sources=available_sources,
                on_recalculate_cb=self.on_node_param_changed,
                on_connect_cb=self.connect_nodes,
                on_view_graph_cb=self.open_graph_for_node,
                on_view_table_cb=self.open_table_for_node,
                on_export_csv_cb=self.export_csv_for_node,
                on_delete_cb=self.delete_node
            )
        elif isinstance(node, MovingAverageNode):
            available_sources = [n for n in self.nodes_registry if isinstance(n, PROCESSOR_INPUT_TYPES) and n != node]
            param_widget = MovingAverageParamWidget(
                node,
                available_sources=available_sources,
                on_recalculate_cb=self.on_node_param_changed,
                on_connect_cb=self.connect_nodes,
                on_view_graph_cb=self.open_graph_for_node,
                on_view_table_cb=self.open_table_for_node,
                on_export_csv_cb=self.export_csv_for_node,
                on_delete_cb=self.delete_node
            )
        elif isinstance(node, MedianFilterNode):
            available_sources = [n for n in self.nodes_registry if isinstance(n, PROCESSOR_INPUT_TYPES) and n != node]
            param_widget = MedianFilterParamWidget(
                node,
                available_sources=available_sources,
                on_recalculate_cb=self.on_node_param_changed,
                on_connect_cb=self.connect_nodes,
                on_view_graph_cb=self.open_graph_for_node,
                on_view_table_cb=self.open_table_for_node,
                on_export_csv_cb=self.export_csv_for_node,
                on_delete_cb=self.delete_node
            )
        elif isinstance(node, THDAnalysisNode):
            available_inputs = [n for n in self.nodes_registry if isinstance(n, PROCESSOR_INPUT_TYPES) and n != node]
            param_widget = THDAnalysisParamWidget(
                node,
                available_inputs=available_inputs,
                on_recalculate_cb=self.on_node_param_changed,
                on_connect_cb=self.connect_nodes,
                on_view_graph_cb=self.open_graph_for_node,
                on_view_table_cb=self.open_table_for_node,
                on_export_csv_cb=self.export_csv_for_node,
                on_delete_cb=self.delete_node
            )

        elif isinstance(node, FFTAnalysisNode):
            available_inputs = [n for n in self.nodes_registry if isinstance(n, PROCESSOR_INPUT_TYPES) and n != node]
            param_widget = FFTAnalysisParamWidget(
                node,
                available_inputs=available_inputs,
                on_recalculate_cb=self.on_node_param_changed,
                on_connect_cb=self.connect_nodes,
                on_view_graph_cb=self.open_graph_for_node,
                on_view_table_cb=self.open_table_for_node,
                on_export_csv_cb=self.export_csv_for_node,
                on_delete_cb=self.delete_node
            )

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setWidget(param_widget)
        self.right_tabs.addTab(scroll, f"Paramètres : {node.params['name']}")

        doc_widget = NodeDocWidget(node)
        self.right_tabs.addTab(doc_widget, "📘 Fonctionnement & Théorie")

    def open_matplotlib_tab(self, title: str, node, columns_dict: dict, x_label: str = "Temps (s)", y_label: str = "Amplitude (V)"):
        for i in range(self.center_tabs.count()):
            widget = self.center_tabs.widget(i)
            if getattr(widget, "associated_node", None) == node and isinstance(widget, MplCanvasWidget):
                self.center_tabs.setCurrentIndex(i)
                widget.update_multi_plot(columns_dict, title=f"Graph : {node.params['name']}", x_label=x_label, y_label=y_label)
                return widget

        mpl_widget = MplCanvasWidget(associated_node=node, theme_name=self.current_theme)
        mpl_widget.update_multi_plot(columns_dict, title=f"Graph : {node.params['name']}", x_label=x_label, y_label=y_label)
        index = self.center_tabs.addTab(mpl_widget, title)
        self.center_tabs.setCurrentIndex(index)
        return mpl_widget

    def open_numpy_tab(self, title: str, node, x_vec, columns_dict: dict, x_label: str = "Temps (s)"):
        for i in range(self.center_tabs.count()):
            widget = self.center_tabs.widget(i)
            if getattr(widget, "associated_node", None) == node and isinstance(widget, NumPyArrayTableWidget):
                self.center_tabs.setCurrentIndex(i)
                widget.set_multi_signal_data(x_vec, columns_dict, x_label=x_label)
                return widget

        numpy_widget = NumPyArrayTableWidget(associated_node=node)
        numpy_widget.set_multi_signal_data(x_vec, columns_dict, x_label=x_label)
        index = self.center_tabs.addTab(numpy_widget, title)
        self.center_tabs.setCurrentIndex(index)
        return numpy_widget

    def close_center_tab(self, index: int):
        self.center_tabs.removeTab(index)

    def choose_font_dialog(self):
        current_font = getattr(self, "current_font", QApplication.font())
        ok, font = QFontDialog.getFont(current_font, self, i18n.tr("choose_font"))
        if ok:
            self.current_font = font
            QApplication.setFont(font)
            self.apply_theme(self.current_theme)
            self.statusBar().showMessage(f"Police appliquée : {font.family()}, {font.pointSize()}pt")

    def set_font_size(self, size: int):
        font = getattr(self, "current_font", QApplication.font())
        font.setPointSize(size)
        self.current_font = font
        QApplication.setFont(font)
        self.apply_theme(self.current_theme)
        self.statusBar().showMessage(f"Taille de police changée : {size}pt")

    def switch_language(self, lang_code: str):
        i18n.set_language(lang_code)
        self.retranslate_ui()

    def retranslate_ui(self):
        self.update_window_title()
        self.file_menu.setTitle(i18n.tr("file_menu"))
        self.action_new.setText(i18n.tr("new_project"))
        self.action_open.setText(i18n.tr("open"))
        self.action_save.setText(i18n.tr("save"))
        self.action_save_as.setText(i18n.tr("save_as"))
        self.action_exit.setText(i18n.tr("exit"))

        self.nodes_menu.setTitle(i18n.tr("nodes_menu"))
        self.sources_submenu.setTitle(i18n.tr("sources_submenu"))
        self.do160_submenu.setTitle(i18n.tr("do160_submenu"))
        self.filters_submenu.setTitle(i18n.tr("filters_submenu"))
        self.maths_submenu.setTitle(i18n.tr("maths_submenu"))
        self.noise_submenu.setTitle(i18n.tr("noise_submenu"))
        self.sampling_submenu.setTitle(i18n.tr("sampling_submenu"))
        self.dsp_filters_submenu.setTitle(i18n.tr("dsp_filters_submenu"))
        self.analyses_submenu.setTitle(i18n.tr("analyses_submenu"))
        self.action_add_fixed_avg.setText(i18n.tr("add_fixed_avg"))
        self.action_add_moving_avg.setText(i18n.tr("add_moving_avg"))
        self.action_add_median_filter.setText(i18n.tr("add_median_filter"))
        self.action_add_gen.setText(i18n.tr("add_generator"))
        self.action_add_csv.setText(i18n.tr("add_csv"))
        self.action_add_do160_double_exp.setText(i18n.tr("add_do160_double_exp"))
        self.action_add_do160_damped_sine.setText(i18n.tr("add_do160_damped_sine"))
        self.action_add_lowpass.setText(i18n.tr("add_lowpass"))
        self.action_add_highpass.setText(i18n.tr("add_highpass"))
        self.action_add_bandpass.setText(i18n.tr("add_bandpass"))
        self.action_add_bandstop.setText(i18n.tr("add_bandstop"))
        self.action_add_derivative.setText(i18n.tr("add_derivative"))
        self.action_add_integrator.setText(i18n.tr("add_integrator"))
        self.action_add_gain.setText(i18n.tr("add_gain"))
        self.action_add_inversion.setText(i18n.tr("add_inversion"))
        self.action_add_abs.setText(i18n.tr("add_abs"))
        self.action_add_log.setText(i18n.tr("add_log"))
        self.action_add_exp.setText(i18n.tr("add_exp"))
        self.action_add_power.setText(i18n.tr("add_power"))
        self.action_add_addition.setText(i18n.tr("add_addition"))
        self.action_add_noise.setText(i18n.tr("add_noise"))
        self.action_add_resample.setText(i18n.tr("add_resample"))
        self.action_add_interpolation.setText(i18n.tr("add_interpolation"))
        self.action_add_dac.setText(i18n.tr("add_dac"))
        self.action_add_thd.setText(i18n.tr("add_thd"))
        self.action_add_fft.setText(i18n.tr("add_fft"))

        self.edit_menu.setTitle(i18n.tr("edit_menu"))
        self.calc_menu.setTitle(i18n.tr("calc_menu"))
        self.action_recalc_all.setText(i18n.tr("recalc_project"))

        self.view_menu.setTitle(i18n.tr("view_menu"))
        self.lang_menu.setTitle(i18n.tr("language_menu"))
        self.help_menu.setTitle(i18n.tr("help_menu"))

        self.tree_dock.setWindowTitle(i18n.tr("tree_dock_title"))
        self.bottom_dock.setWindowTitle(i18n.tr("bottom_dock_title"))
        self.right_dock.setWindowTitle(i18n.tr("right_dock_title"))

        self.update_recent_projects_menu()
        self.refresh_project_tree()

    def apply_theme(self, theme_name: str):
        self.current_theme = theme_name
        font = getattr(self, "current_font", QApplication.font())
        font_family = font.family()
        font_size = font.pointSize()
        font_rule = f"* {{ font-family: '{font_family}'; font-size: {font_size}pt; }}\n"

        if theme_name == "dark":
            style = """
                QMainWindow { background-color: #121212; color: #FFFFFF; }
                QDockWidget { color: #FFFFFF; }
                QDockWidget::title { background: #1E1E1E; padding: 6px; border-bottom: 1px solid #333; }
                QMenuBar { background-color: #1E1E1E; color: #FFFFFF; }
                QMenuBar::item:selected { background-color: #00ADB5; }
                QMenu { background-color: #1E1E1E; color: #FFFFFF; border: 1px solid #333; }
                QMenu::item:selected { background-color: #00ADB5; }
                QTreeWidget, QTableWidget, QTabWidget::pane { background-color: #1E1E1E; color: #EEEEEE; border: 1px solid #333; }
                QHeaderView::section { background-color: #2A2A2A; color: #FFFFFF; padding: 4px; }
                QLineEdit, QComboBox, QDoubleSpinBox, QSpinBox { background-color: #2A2A2A; color: #FFFFFF; border: 1px solid #444; padding: 4px; }
                QGroupBox { color: #00ADB5; font-weight: bold; border: 1px solid #333; margin-top: 10px; }
                QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 3px; }
                QPushButton { background-color: #2A2A2A; color: #FFFFFF; border: 1px solid #444; border-radius: 4px; }
                QPushButton:hover { background-color: #00ADB5; }
                QCheckBox { color: #FFFFFF; }
            """
        else:
            style = """
                QMainWindow { background-color: #F5F5F5; color: #000000; }
                QDockWidget { color: #000000; }
                QDockWidget::title { background: #E0E0E0; padding: 6px; border-bottom: 1px solid #CCC; }
                QMenuBar { background-color: #E0E0E0; color: #000000; }
                QMenuBar::item:selected { background-color: #00ADB5; color: #FFFFFF; }
                QMenu { background-color: #FFFFFF; color: #000000; border: 1px solid #CCC; }
                QMenu::item:selected { background-color: #00ADB5; color: #FFFFFF; }
                QTreeWidget, QTableWidget, QTabWidget::pane { background-color: #FFFFFF; color: #000000; border: 1px solid #CCC; }
                QHeaderView::section { background-color: #EAEAEA; color: #000000; padding: 4px; }
                QLineEdit, QComboBox, QDoubleSpinBox, QSpinBox { background-color: #FFFFFF; color: #000000; border: 1px solid #CCC; padding: 4px; }
                QGroupBox { color: #008C9E; font-weight: bold; border: 1px solid #CCC; margin-top: 10px; }
                QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 3px; }
                QPushButton { background-color: #EAEAEA; color: #000000; border: 1px solid #CCC; border-radius: 4px; }
                QPushButton:hover { background-color: #00ADB5; color: #FFFFFF; }
                QCheckBox { color: #000000; }
            """
        self.setStyleSheet(font_rule + style)

        for i in range(self.center_tabs.count()):
            widget = self.center_tabs.widget(i)
            if isinstance(widget, MplCanvasWidget):
                widget.apply_theme(theme_name)
