"""Offline-capable PySide6 workbench shell for Pourbaix Studio R4."""

from __future__ import annotations

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDockWidget, QLabel, QListWidget, QMainWindow, QTableWidget, QTableWidgetItem,
    QTabWidget, QToolBar, QVBoxLayout, QWidget,
)

from pourbaix_r4.i18n import Language, PreferenceStore
from pourbaix_r4.models import AppearanceSettings, InterestRegion, ResultSnapshot
from pourbaix_r4.plotting import render_snapshot
from pourbaix_r4.session import CalculationSession
from pourbaix_r4.ui.composition_panel import CompositionPanel


class PourbaixStudioMainWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.session = CalculationSession()
        self.preferences = PreferenceStore()
        self.appearance = AppearanceSettings()
        self.interest_regions: list[InterestRegion] = []
        self._language: Language = self.preferences.language()
        self.setWindowTitle("Pourbaix Studio R4")
        self.resize(1280, 800)
        self._build_workspace()
        self._build_docks()
        self._build_toolbar()

    def _build_workspace(self) -> None:
        self.workspace_tabs = QTabWidget()
        self.workspace_tabs.setObjectName("workspaceTabs")
        self.diagram_host = QWidget(); self.diagram_layout = QVBoxLayout(self.diagram_host)
        self.diagram_layout.addWidget(QLabel("Generate a diagram to begin."))
        self.workspace_tabs.addTab(self.diagram_host, "Diagram")
        self.available_regions = QListWidget(); self.workspace_tabs.addTab(self.available_regions, "Available regions")
        self.boundary_table = QTableWidget(0, 4); self.boundary_table.setHorizontalHeaderLabels(["domain_label", "vertex_index", "pH", "potential_V_SHE"])
        self.workspace_tabs.addTab(self.boundary_table, "Boundary data")
        self.setCentralWidget(self.workspace_tabs)

    def _build_docks(self) -> None:
        self.composition_panel = CompositionPanel()
        self.composition_panel.input_changed.connect(self.session.invalidate_for_input_change)
        composition_dock = QDockWidget("System and conditions", self); composition_dock.setWidget(self.composition_panel)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, composition_dock)
        self.interest_list = QListWidget()
        interest_dock = QDockWidget("Interest regions", self); interest_dock.setWidget(self.interest_list)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, interest_dock)

    def _build_toolbar(self) -> None:
        toolbar = QToolBar("Tools", self); self.addToolBar(toolbar)
        toolbar.addAction("English", lambda: self.set_language("en"))
        toolbar.addAction("中文", lambda: self.set_language("zh_CN"))

    def set_language(self, language: Language) -> None:
        self._language = language
        self.preferences.set_language(language)
        self.setWindowTitle("Pourbaix Studio R4" if language == "en" else "Pourbaix Studio R4 — 倒易图工作台")

    def show_snapshot(self, snapshot: ResultSnapshot) -> None:
        self.session.replace_success(snapshot)
        self.available_regions.clear(); self.available_regions.addItems(snapshot.stable_domain_labels)
        self.boundary_table.setRowCount(len(snapshot.boundaries))
        for row, boundary in enumerate(snapshot.boundaries):
            for column, value in enumerate((boundary.domain_label, boundary.vertex_index, boundary.ph, boundary.potential_v_she)):
                self.boundary_table.setItem(row, column, QTableWidgetItem(str(value)))
        self._render()

    def _render(self) -> None:
        snapshot = self.session.snapshot
        if snapshot is None: return
        figure = render_snapshot(snapshot, self.appearance, self.interest_regions)
        canvas = FigureCanvasQTAgg(figure)
        while self.diagram_layout.count():
            child = self.diagram_layout.takeAt(0).widget()
            if child is not None: child.deleteLater()
        self.diagram_layout.addWidget(canvas)

    def add_interest_region(self, label: str) -> None:
        snapshot = self.session.snapshot
        if snapshot is None or label not in snapshot.stable_domain_labels:
            return
        self.interest_regions.append(InterestRegion(label))
        self.interest_list.addItem(label)
        self._render()

    def remove_interest_region(self, index: int) -> None:
        if 0 <= index < len(self.interest_regions):
            self.interest_regions.pop(index)
            self.interest_list.takeItem(index)
            self._render()

    def interest_region_count(self) -> int:
        return len(self.interest_regions)
