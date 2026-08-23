"""Offline-capable PySide6 workbench shell for Pourbaix Studio R4."""

from __future__ import annotations

from pathlib import Path
from typing import Callable

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDockWidget, QHBoxLayout, QLabel, QListWidget, QMainWindow, QPushButton, QTableWidget, QTableWidgetItem,
    QTabWidget, QToolBar, QVBoxLayout, QWidget,
)

from pourbaix_r4.i18n import Language, PreferenceStore
from pourbaix_r4.calculation import calculate_snapshot
from pourbaix_r4.credentials import WindowsCredentialStore, resolve_api_key
from pourbaix_r4.materials_project import CachedEntryService, MPResterEntryProvider
from pourbaix_r4.models import AppearanceSettings, InterestRegion, ResultSnapshot
from pourbaix_r4.plotting import render_snapshot
from pourbaix_r4.session import CalculationSession
from pourbaix_r4.ui.composition_panel import CompositionPanel


class PourbaixStudioMainWindow(QMainWindow):
    def __init__(self, *, entry_service=None, credential_resolver: Callable[[], object] | None = None, calculate=calculate_snapshot, parent=None):
        super().__init__(parent)
        self.session = CalculationSession()
        self.preferences = PreferenceStore()
        self.appearance = AppearanceSettings()
        self.interest_regions: list[InterestRegion] = []
        self._language: Language = self.preferences.language()
        self._entry_service = entry_service or CachedEntryService(MPResterEntryProvider())
        self._credential_resolver = credential_resolver or (
            lambda: resolve_api_key(None, WindowsCredentialStore(), Path.cwd() / "mp_api_key.txt")
        )
        self._calculate = calculate
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
        self.composition_panel.calculation_requested.connect(self._generate)
        composition_dock = QDockWidget("System and conditions", self); composition_dock.setWidget(self.composition_panel)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, composition_dock)
        interest_widget = QWidget(); interest_layout = QVBoxLayout(interest_widget)
        self.interest_list = QListWidget(); interest_layout.addWidget(self.interest_list)
        controls = QHBoxLayout()
        add_region = QPushButton("Add selected"); add_region.setObjectName("addInterestRegionButton"); add_region.clicked.connect(self._add_selected_region); controls.addWidget(add_region)
        remove_region = QPushButton("Remove"); remove_region.setObjectName("removeInterestRegionButton"); remove_region.clicked.connect(lambda: self.remove_interest_region(self.interest_list.currentRow())); controls.addWidget(remove_region)
        interest_layout.addLayout(controls)
        interest_dock = QDockWidget("Interest regions", self); interest_dock.setWidget(interest_widget)
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

    def _generate(self, calculation_input) -> None:
        try:
            credential = self._credential_resolver()
            result = self._entry_service.fetch(calculation_input.elements, credential.value)
            self.show_snapshot(self._calculate(calculation_input, result.entries))
            self.statusBar().showMessage("Diagram generated.")
        except Exception as error:
            self.session.replace_failure(error)
            self.statusBar().showMessage("Calculation failed. See diagnostics for details.")

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

    def _add_selected_region(self) -> None:
        item = self.available_regions.currentItem()
        if item is not None:
            self.add_interest_region(item.text())

    def remove_interest_region(self, index: int) -> None:
        if 0 <= index < len(self.interest_regions):
            self.interest_regions.pop(index)
            self.interest_list.takeItem(index)
            self._render()

    def interest_region_count(self) -> int:
        return len(self.interest_regions)
