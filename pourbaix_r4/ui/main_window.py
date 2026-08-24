"""Offline-capable PySide6 workbench shell for Pourbaix Studio R4."""

from __future__ import annotations

from pathlib import Path
from typing import Callable
from dataclasses import replace

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox, QComboBox, QDockWidget, QDoubleSpinBox, QFileDialog, QFormLayout, QHBoxLayout,
    QLabel, QLineEdit, QListWidget, QMainWindow, QPushButton, QTableWidget, QTableWidgetItem,
    QTabWidget, QToolBar, QVBoxLayout, QWidget,
)

from pourbaix_r4.i18n import Language, PreferenceStore
from pourbaix_r4.calculation import calculate_snapshot
from pourbaix_r4.credentials import WindowsCredentialStore, resolve_api_key
from pourbaix_r4.exporting import ExportError, export_boundaries, export_figure
from pourbaix_r4.materials_project import CachedEntryService, MPResterEntryProvider
from pourbaix_r4.models import AppearanceSettings, InterestRegion, ResultSnapshot
from pourbaix_r4.plotting import render_snapshot
from pourbaix_r4.session import CalculationSession
from pourbaix_r4.ui.composition_panel import CompositionPanel
from pourbaix_r4.ui.api_dialog import ApiSettingsDialog


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
        appearance_widget = QWidget(); appearance_layout = QVBoxLayout(appearance_widget)
        labels = QCheckBox("Show ion labels"); labels.setObjectName("showIonLabelsControl"); labels.setChecked(self.appearance.show_ion_labels); labels.toggled.connect(self.set_show_ion_labels); appearance_layout.addWidget(labels)
        form = QFormLayout()
        self.ion_label_font = QComboBox(); self.ion_label_font.setObjectName("ionLabelFontControl"); self.ion_label_font.addItems(["Arial", "DejaVu Sans", "Times New Roman"]); self.ion_label_font.setCurrentText(self.appearance.ion_label_font); self.ion_label_font.currentTextChanged.connect(lambda value: self.apply_appearance(ion_label_font=value)); form.addRow("Ion label font", self.ion_label_font)
        self.axis_tick_font = QComboBox(); self.axis_tick_font.setObjectName("axisTickFontControl"); self.axis_tick_font.addItems(["Arial", "DejaVu Sans", "Times New Roman"]); self.axis_tick_font.setCurrentText(self.appearance.axis_tick_font); self.axis_tick_font.currentTextChanged.connect(lambda value: self.apply_appearance(axis_tick_font=value)); form.addRow("Axis/tick font", self.axis_tick_font)
        self.ion_label_size = self._appearance_spin("ionLabelSizeControl", self.appearance.ion_label_font_size, lambda value: self.apply_appearance(ion_label_font_size=value)); form.addRow("Ion label size", self.ion_label_size)
        self.axis_tick_size = self._appearance_spin("axisTickSizeControl", self.appearance.axis_tick_font_size, lambda value: self.apply_appearance(axis_tick_font_size=value)); form.addRow("Axis/tick size", self.axis_tick_size)
        spine = self._appearance_spin("spineWidthControl", self.appearance.spine_width, lambda value: self.set_line_style(spine_width=value)); form.addRow("Spine width", spine)
        solid = self._appearance_spin("solidLineWidthControl", self.appearance.solid_line_width, lambda value: self.set_line_style(solid_line_width=value)); form.addRow("Solid line width", solid)
        stability = self._appearance_spin("stabilityLineWidthControl", self.appearance.stability_line_width, lambda value: self.set_line_style(stability_line_width=value)); form.addRow("Stability line width", stability)
        self.dpi_control = self._appearance_spin("exportDpiControl", 300, lambda value: None, maximum=2400); form.addRow("Export DPI", self.dpi_control)
        self.transparent_control = QCheckBox("Transparent background"); self.transparent_control.setObjectName("transparentBackgroundControl"); form.addRow(self.transparent_control)
        self.minor_ticks = QCheckBox("Show minor ticks"); self.minor_ticks.setChecked(self.appearance.show_minor_ticks); self.minor_ticks.toggled.connect(lambda value: self.apply_appearance(show_minor_ticks=value)); form.addRow(self.minor_ticks)
        self.hydrogen_color = QLineEdit(self.appearance.hydrogen_line_color); self.hydrogen_color.setObjectName("hydrogenLineColorControl"); self.hydrogen_color.editingFinished.connect(lambda: self.set_line_style(hydrogen_line_color=self.hydrogen_color.text())); form.addRow("Hydrogen line", self.hydrogen_color)
        self.oxygen_color = QLineEdit(self.appearance.oxygen_line_color); self.oxygen_color.setObjectName("oxygenLineColorControl"); self.oxygen_color.editingFinished.connect(lambda: self.set_line_style(oxygen_line_color=self.oxygen_color.text())); form.addRow("Oxygen line", self.oxygen_color)
        appearance_layout.addLayout(form)
        fill_form = QFormLayout()
        self.region_color = QLineEdit("#B0C4DE"); self.region_color.setObjectName("regionFillColorControl"); fill_form.addRow("Selected fill color", self.region_color)
        self.region_opacity = self._appearance_spin("regionFillOpacityControl", 0.4, lambda value: None, maximum=1.0, step=0.05); fill_form.addRow("Selected fill alpha", self.region_opacity)
        apply_fill = QPushButton("Apply selected region style"); apply_fill.clicked.connect(self.apply_selected_region_style); fill_form.addRow(apply_fill)
        appearance_layout.addLayout(fill_form)
        appearance_dock = QDockWidget("Appearance", self); appearance_dock.setWidget(appearance_widget)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, appearance_dock)

    def _build_toolbar(self) -> None:
        toolbar = QToolBar("Tools", self); self.addToolBar(toolbar)
        toolbar.addAction("API settings", self.show_api_settings)
        toolbar.addAction("Export data", self._choose_data_export)
        toolbar.addAction("Export figure", self._choose_figure_export)

    def _appearance_spin(self, name, value, callback, *, maximum=100.0, step=0.1):
        control = QDoubleSpinBox(); control.setObjectName(name); control.setRange(0.0, maximum); control.setSingleStep(step); control.setValue(value); control.valueChanged.connect(callback); return control

    def set_language(self, language: Language) -> None:
        self._language = language
        self.preferences.set_language(language)
        self.setWindowTitle("Pourbaix Studio R4" if language == "en" else "Pourbaix Studio R4 — 倒易图工作台")

    def show_snapshot(self, snapshot: ResultSnapshot) -> None:
        self.session.replace_success(snapshot)
        palette = ("#B0C4DE", "#C6E48B", "#F6C85F", "#E78AC3")
        self.interest_regions = [InterestRegion(label, color=palette[index % len(palette)], opacity=0.35) for index, label in enumerate(snapshot.stable_domain_labels[:4])]
        self.interest_list.clear(); self.interest_list.addItems(region.label for region in self.interest_regions)
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

    def show_api_settings(self) -> None:
        ApiSettingsDialog(store=WindowsCredentialStore(), parent=self).exec()

    def export_current_data(self, path: Path, file_format: str) -> Path:
        snapshot = self.session.exportable_snapshot
        if snapshot is None:
            raise ExportError("Generate a current diagram before exporting data")
        return export_boundaries(snapshot, Path(path), file_format)

    def export_current_figure(self, path: Path, image_format: str, *, dpi: int = 300, transparent: bool = False) -> Path:
        snapshot = self.session.exportable_snapshot
        if snapshot is None:
            raise ExportError("Generate a current diagram before exporting an image")
        figure = render_snapshot(snapshot, self.appearance, self.interest_regions)
        return export_figure(figure, Path(path), image_format, dpi=dpi, transparent=transparent)

    def _choose_data_export(self) -> None:
        path, selected = QFileDialog.getSaveFileName(self, "Export data", "", "CSV (*.csv);;Excel (*.xlsx);;Text (*.txt)")
        if not path: return
        file_format = "xlsx" if "xlsx" in selected else "txt" if "txt" in selected else "csv"
        try:
            self.export_current_data(Path(path), file_format)
            self.statusBar().showMessage(f"Export completed: {path}")
        except ExportError as error:
            self.statusBar().showMessage(str(error))

    def _choose_figure_export(self) -> None:
        path, selected = QFileDialog.getSaveFileName(self, "Export figure", "", "PNG (*.png);;SVG (*.svg);;TIFF (*.tiff *.tif)")
        if not path: return
        image_format = "svg" if "svg" in selected.lower() else "tiff" if "tiff" in selected.lower() or "tif" in selected.lower() else "png"
        try:
            self.export_current_figure(Path(path), image_format, dpi=int(self.dpi_control.value()), transparent=self.transparent_control.isChecked())
            self.statusBar().showMessage(f"Export completed: {path}")
        except ExportError as error:
            self.statusBar().showMessage(str(error))

    def _render(self) -> None:
        snapshot = self.session.snapshot
        if snapshot is None: return
        figure = render_snapshot(snapshot, self.appearance, self.interest_regions)
        canvas = FigureCanvasQTAgg(figure)
        while self.diagram_layout.count():
            child = self.diagram_layout.takeAt(0).widget()
            if child is not None: child.deleteLater()
        self.diagram_layout.addWidget(canvas)

    def set_show_ion_labels(self, visible: bool) -> None:
        self.appearance = replace(self.appearance, show_ion_labels=visible)
        self._render()

    def set_line_style(self, **values) -> None:
        allowed = {"spine_width", "solid_line_width", "stability_line_width", "hydrogen_line_color", "oxygen_line_color"}
        self.appearance = replace(self.appearance, **{key: value for key, value in values.items() if key in allowed})
        self._render()

    def apply_selected_region_style(self) -> None:
        index = self.interest_list.currentRow()
        if not (0 <= index < len(self.interest_regions)):
            return
        self.interest_regions[index] = replace(self.interest_regions[index], color=self.region_color.text(), opacity=self.region_opacity.value())
        self._render()

    def apply_appearance(self, **values) -> None:
        allowed = set(self.appearance.__dataclass_fields__)
        self.appearance = replace(self.appearance, **{key: value for key, value in values.items() if key in allowed})
        self._render()

    def add_interest_region(self, label: str) -> None:
        snapshot = self.session.snapshot
        if snapshot is None or label not in snapshot.stable_domain_labels or any(region.label == label for region in self.interest_regions):
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
