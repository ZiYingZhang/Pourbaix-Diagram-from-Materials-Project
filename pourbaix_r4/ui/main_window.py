"""Offline-capable PySide6 workbench shell for Pourbaix Studio R4."""

from __future__ import annotations

from pathlib import Path
from typing import Callable
from dataclasses import replace

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg, NavigationToolbar2QT
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont, QPalette
from PySide6.QtWidgets import (
    QCheckBox, QColorDialog, QComboBox, QDockWidget, QDoubleSpinBox, QFileDialog, QFormLayout,
    QApplication, QFontComboBox, QFrame, QHeaderView, QHBoxLayout, QLabel, QLineEdit, QListWidget, QListWidgetItem, QMainWindow,
    QPushButton, QScrollArea, QSizePolicy, QSlider, QTableWidget, QTableWidgetItem, QTabWidget, QToolBar,
    QToolButton, QVBoxLayout, QWidget,
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


class CollapsibleSection(QFrame):
    """DPI-safe expandable section with a real header control."""

    def __init__(self, title: str, content: QWidget, name: str, *, expanded: bool = False):
        super().__init__()
        self.setObjectName(f"{name}Section")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.header = QToolButton()
        self.header.setObjectName(f"{name}SectionHeader")
        self.header.setProperty("sectionHeader", True)
        self.header.setText(title)
        self.header.setCheckable(True)
        self.header.setChecked(expanded)
        self.header.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.header.setArrowType(Qt.ArrowType.DownArrow if expanded else Qt.ArrowType.RightArrow)
        self.header.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.header.setMinimumHeight(self.header.fontMetrics().height() + 16)
        content.setObjectName(f"{name}SectionContent")
        content.setProperty("sectionContent", True)
        content.setVisible(expanded)
        self.header.toggled.connect(
            lambda visible: (
                content.setVisible(visible),
                self.header.setArrowType(Qt.ArrowType.DownArrow if visible else Qt.ArrowType.RightArrow),
            )
        )
        layout.addWidget(self.header)
        layout.addWidget(content)


class PourbaixStudioMainWindow(QMainWindow):
    def __init__(self, *, entry_service=None, credential_resolver: Callable[[], object] | None = None, calculate=calculate_snapshot, parent=None):
        super().__init__(parent)
        self.session = CalculationSession()
        self.preferences = PreferenceStore()
        self.appearance = AppearanceSettings()
        self.interest_regions: list[InterestRegion] = []
        self._canvas = None
        self._screen_layout_applied = False
        self._dock_visibility_before_focus = (True, True)
        self._language: Language = self.preferences.language()
        self._entry_service = entry_service or CachedEntryService(MPResterEntryProvider())
        self._credential_resolver = credential_resolver or (
            lambda: resolve_api_key(None, WindowsCredentialStore(), Path.cwd() / "mp_api_key.txt")
        )
        self._calculate = calculate
        self.setWindowTitle("Pourbaix Studio R4")
        self.resize(1280, 800)
        self._apply_light_palette()
        self._build_workspace()
        self._build_docks()
        self._build_toolbar()

    def _build_workspace(self) -> None:
        self.workspace_tabs = QTabWidget()
        self.workspace_tabs.setObjectName("workspaceTabs")
        self.diagram_host = QWidget(); self.diagram_host.setObjectName("diagramHost"); self.diagram_layout = QVBoxLayout(self.diagram_host)
        self.diagram_layout.addWidget(QLabel("Generate a diagram to begin."))
        self.workspace_tabs.addTab(self.diagram_host, "Diagram")
        self.available_regions = QListWidget(); self.workspace_tabs.addTab(self.available_regions, "Available regions")
        self.boundary_table = QTableWidget(0, 4)
        self.boundary_table.setHorizontalHeaderLabels(["DOMAIN LABEL", "VERTEX", "pH", "POTENTIAL (V vs. SHE)"])
        self.boundary_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.workspace_tabs.addTab(self.boundary_table, "Boundary data")
        self.setCentralWidget(self.workspace_tabs)

    def _build_docks(self) -> None:
        self.composition_panel = CompositionPanel()
        self.composition_panel.input_changed.connect(self.session.invalidate_for_input_change)
        self.composition_panel.calculation_requested.connect(self._generate)
        self.composition_panel.validation_failed.connect(self.statusBar().showMessage)
        query_scroll = self._scroll_area("queryScrollArea", self.composition_panel)
        self.composition_dock = QDockWidget("System and conditions", self)
        self.composition_dock.setMinimumWidth(255)
        self.composition_dock.setWidget(query_scroll)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.composition_dock)

        post_outer = QWidget()
        post_outer_layout = QVBoxLayout(post_outer)
        post_outer_layout.setContentsMargins(0, 0, 0, 0)
        post_content = QWidget()
        post_layout = QVBoxLayout(post_content)
        post_layout.setContentsMargins(10, 10, 10, 10)
        post_layout.addWidget(self._build_regions_group())
        post_layout.addWidget(self._build_appearance_sections())
        post_layout.addStretch(1)
        post_scroll = self._scroll_area("postProcessingScrollArea", post_content)
        post_outer_layout.addWidget(post_scroll, 1)
        self.replot_button = QPushButton("Re-plot current result")
        self.replot_button.setObjectName("replotButton")
        self.replot_button.clicked.connect(self.replot_current_result)
        post_outer_layout.addWidget(self.replot_button)
        self.post_dock = QDockWidget("Post-processing", self)
        self.post_dock.setMinimumWidth(310)
        self.post_dock.setWidget(post_outer)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.post_dock)

    def _scroll_area(self, name: str, widget: QWidget) -> QScrollArea:
        scroll = QScrollArea()
        scroll.setObjectName(name)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setWidget(widget)
        return scroll

    def _build_regions_group(self) -> QFrame:
        group = QFrame()
        group.setObjectName("regionsAndFillsGroup")
        layout = QVBoxLayout(group)
        title = QLabel("REGIONS AND FILLS")
        title.setObjectName("regionsAndFillsTitle")
        layout.addWidget(title)
        add_row = QHBoxLayout()
        self.region_selector = QComboBox()
        self.region_selector.setObjectName("regionSelectorControl")
        add_row.addWidget(self.region_selector, 1)
        add_region = QPushButton("Add")
        add_region.setObjectName("addInterestRegionButton")
        add_region.clicked.connect(self._add_selected_region)
        add_row.addWidget(add_region)
        layout.addLayout(add_row)
        self.interest_list = QListWidget()
        self.interest_list.setMinimumHeight(135)
        self.interest_list.itemChanged.connect(self._interest_visibility_changed)
        self.interest_list.currentRowChanged.connect(self._load_interest_style)
        layout.addWidget(self.interest_list)
        remove_region = QPushButton("Remove selected region")
        remove_region.setObjectName("removeInterestRegionButton")
        remove_region.clicked.connect(lambda: self.remove_interest_region(self.interest_list.currentRow()))
        layout.addWidget(remove_region)
        color_row = QHBoxLayout()
        color_row.addWidget(QLabel("Selected fill"))
        self.region_color_button = QPushButton("#B0C4DE")
        self.region_color_button.setObjectName("regionColorButton")
        self.region_color_button.clicked.connect(self.choose_selected_region_color)
        color_row.addWidget(self.region_color_button, 1)
        layout.addLayout(color_row)
        opacity_row = QHBoxLayout()
        opacity_row.addWidget(QLabel("Opacity"))
        self.region_opacity = QSlider(Qt.Orientation.Horizontal)
        self.region_opacity.setObjectName("regionOpacitySlider")
        self.region_opacity.setRange(0, 100)
        self.region_opacity.setValue(40)
        self.region_opacity.valueChanged.connect(self._update_region_opacity_label)
        opacity_row.addWidget(self.region_opacity, 1)
        self.region_opacity_label = QLabel("40%")
        opacity_row.addWidget(self.region_opacity_label)
        layout.addLayout(opacity_row)
        apply_fill = QPushButton("Apply to selected region")
        apply_fill.clicked.connect(self.apply_selected_region_style)
        layout.addWidget(apply_fill)
        self._selected_region_color = "#B0C4DE"
        self._refresh_region_color_button()
        return group

    def _build_appearance_sections(self) -> QWidget:
        container = QWidget()
        container.setObjectName("postProcessingSections")
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)
        sections = (
            ("ION LABELS", self._build_labels_page(), "ionLabels", True),
            ("AXIS TITLES", self._build_axis_titles_page(), "axisTitles", False),
            ("AXIS AND TICKS", self._build_axis_ticks_page(), "axisAndTicks", False),
            ("TICK LABELS", self._build_tick_labels_page(), "tickLabels", False),
            ("DOMAIN AND STABILITY LINES", self._build_lines_page(), "domainLines", False),
            ("VIEW RANGE", self._build_view_page(), "viewRange", False),
            ("IMAGE EXPORT", self._build_export_page(), "imageExport", False),
        )
        for title, page, name, expanded in sections:
            layout.addWidget(CollapsibleSection(title, page, name, expanded=expanded))
        return container

    def _build_labels_page(self) -> QWidget:
        page = QWidget(); form = QFormLayout(page); self._configure_form(form)
        labels = QCheckBox("Show ion labels"); labels.setObjectName("showIonLabelsControl"); labels.setChecked(self.appearance.show_ion_labels); labels.toggled.connect(self.set_show_ion_labels); form.addRow(labels)
        self.ion_label_font = self._font_combo("ionLabelFontControl", self.appearance.ion_label_font, lambda value: self.apply_appearance(ion_label_font=value)); form.addRow("Font", self.ion_label_font)
        self.ion_label_size = self._appearance_spin("ionLabelSizeControl", self.appearance.ion_label_font_size, lambda value: self.apply_appearance(ion_label_font_size=value)); form.addRow("Ion label size", self.ion_label_size)
        label_background = QCheckBox("Fill label background"); label_background.setObjectName("fillIonLabelBackgroundControl"); label_background.setChecked(self.appearance.fill_ion_label_background); label_background.toggled.connect(lambda value: self.apply_appearance(fill_ion_label_background=value)); form.addRow(label_background)
        label_background_color = QLineEdit(self.appearance.ion_label_background_color); label_background_color.setObjectName("ionLabelBackgroundColorControl"); label_background_color.editingFinished.connect(lambda: self.apply_appearance(ion_label_background_color=label_background_color.text())); form.addRow("Background", label_background_color)
        label_background_alpha = self._appearance_spin("ionLabelBackgroundAlphaControl", self.appearance.ion_label_background_alpha, lambda value: self.apply_appearance(ion_label_background_alpha=value), maximum=1.0, step=0.05); form.addRow("Background opacity", label_background_alpha)
        return page

    def _build_axis_titles_page(self) -> QWidget:
        page = QWidget(); form = QFormLayout(page); self._configure_form(form)
        self.x_axis_label = QLineEdit(self.appearance.x_axis_label); self.x_axis_label.setObjectName("xAxisLabelControl"); self.x_axis_label.editingFinished.connect(lambda: self.apply_appearance(x_axis_label=self.x_axis_label.text())); form.addRow("X title", self.x_axis_label)
        self.x_axis_label_font = self._font_combo("xAxisLabelFontControl", self.appearance.x_axis_label_font, lambda value: self.apply_appearance(x_axis_label_font=value)); form.addRow("X title font", self.x_axis_label_font)
        self.x_axis_label_size = self._appearance_spin("xAxisLabelSizeControl", self.appearance.x_axis_label_size, lambda value: self.apply_appearance(x_axis_label_size=value)); form.addRow("X title size", self.x_axis_label_size)
        self.y_axis_label = QLineEdit(self.appearance.y_axis_label); self.y_axis_label.setObjectName("yAxisLabelControl"); self.y_axis_label.editingFinished.connect(lambda: self.apply_appearance(y_axis_label=self.y_axis_label.text())); form.addRow("Y title", self.y_axis_label)
        self.y_axis_label_font = self._font_combo("yAxisLabelFontControl", self.appearance.y_axis_label_font, lambda value: self.apply_appearance(y_axis_label_font=value)); form.addRow("Y title font", self.y_axis_label_font)
        self.y_axis_label_size = self._appearance_spin("yAxisLabelSizeControl", self.appearance.y_axis_label_size, lambda value: self.apply_appearance(y_axis_label_size=value)); form.addRow("Y title size", self.y_axis_label_size)
        return page

    def _build_axis_ticks_page(self) -> QWidget:
        page = QWidget(); form = QFormLayout(page); self._configure_form(form)
        self.show_x_ticks = QCheckBox("Show X-axis ticks"); self.show_x_ticks.setObjectName("showXTicksControl"); self.show_x_ticks.setChecked(self.appearance.show_x_ticks); self.show_x_ticks.toggled.connect(lambda value: self.apply_appearance(show_x_ticks=value)); form.addRow(self.show_x_ticks)
        self.show_y_ticks = QCheckBox("Show Y-axis ticks"); self.show_y_ticks.setObjectName("showYTicksControl"); self.show_y_ticks.setChecked(self.appearance.show_y_ticks); self.show_y_ticks.toggled.connect(lambda value: self.apply_appearance(show_y_ticks=value)); form.addRow(self.show_y_ticks)
        self.major_tick_direction = QComboBox(); self.major_tick_direction.setObjectName("majorTickDirectionControl")
        for text, value in (("Out", "out"), ("In", "in"), ("In & Out", "inout")):
            self.major_tick_direction.addItem(text, value)
        self.major_tick_direction.setCurrentIndex(self.major_tick_direction.findData(self.appearance.major_tick_direction))
        self.major_tick_direction.currentIndexChanged.connect(lambda index: self.apply_appearance(major_tick_direction=self.major_tick_direction.itemData(index))); form.addRow("Direction", self.major_tick_direction)
        major_length = self._appearance_spin("majorTickLengthControl", self.appearance.major_tick_length, lambda value: self.apply_appearance(major_tick_length=value)); form.addRow("Major length", major_length)
        major_width = self._appearance_spin("majorTickWidthControl", self.appearance.major_tick_width, lambda value: self.apply_appearance(major_tick_width=value)); form.addRow("Major width", major_width)
        self.minor_ticks = QCheckBox("Show minor ticks"); self.minor_ticks.setObjectName("showMinorTicksControl"); self.minor_ticks.setChecked(self.appearance.show_minor_ticks); self.minor_ticks.toggled.connect(lambda value: self.apply_appearance(show_minor_ticks=value)); form.addRow(self.minor_ticks)
        minor_length = self._appearance_spin("minorTickLengthControl", self.appearance.minor_tick_length, lambda value: self.apply_appearance(minor_tick_length=value)); form.addRow("Minor length", minor_length)
        minor_width = self._appearance_spin("minorTickWidthControl", self.appearance.minor_tick_width, lambda value: self.apply_appearance(minor_tick_width=value)); form.addRow("Minor width", minor_width)
        spine = self._appearance_spin("spineWidthControl", self.appearance.spine_width, lambda value: self.set_line_style(spine_width=value)); form.addRow("Axis line width", spine)
        return page

    def _build_tick_labels_page(self) -> QWidget:
        page = QWidget(); form = QFormLayout(page); self._configure_form(form)
        self.show_x_tick_labels = QCheckBox("Show X tick labels"); self.show_x_tick_labels.setObjectName("showXTickLabelsControl"); self.show_x_tick_labels.setChecked(self.appearance.show_x_tick_labels); self.show_x_tick_labels.toggled.connect(lambda value: self.apply_appearance(show_x_tick_labels=value)); form.addRow(self.show_x_tick_labels)
        self.show_y_tick_labels = QCheckBox("Show Y tick labels"); self.show_y_tick_labels.setObjectName("showYTickLabelsControl"); self.show_y_tick_labels.setChecked(self.appearance.show_y_tick_labels); self.show_y_tick_labels.toggled.connect(lambda value: self.apply_appearance(show_y_tick_labels=value)); form.addRow(self.show_y_tick_labels)
        self.axis_tick_font = self._font_combo("axisTickFontControl", self.appearance.axis_tick_font, lambda value: self.apply_appearance(axis_tick_font=value)); form.addRow("Font", self.axis_tick_font)
        self.axis_tick_size = self._appearance_spin("axisTickSizeControl", self.appearance.axis_tick_font_size, lambda value: self.apply_appearance(axis_tick_font_size=value)); form.addRow("Size", self.axis_tick_size)
        return page

    def _build_lines_page(self) -> QWidget:
        page = QWidget(); form = QFormLayout(page); self._configure_form(form)
        solid = self._appearance_spin("solidLineWidthControl", self.appearance.solid_line_width, lambda value: self.set_line_style(solid_line_width=value)); form.addRow("Solid line width", solid)
        stability = self._appearance_spin("stabilityLineWidthControl", self.appearance.stability_line_width, lambda value: self.set_line_style(stability_line_width=value)); form.addRow("Stability line width", stability)
        self.hydrogen_color = QLineEdit(self.appearance.hydrogen_line_color); self.hydrogen_color.setObjectName("hydrogenLineColorControl"); self.hydrogen_color.editingFinished.connect(lambda: self.set_line_style(hydrogen_line_color=self.hydrogen_color.text())); form.addRow("Hydrogen line", self.hydrogen_color)
        self.oxygen_color = QLineEdit(self.appearance.oxygen_line_color); self.oxygen_color.setObjectName("oxygenLineColorControl"); self.oxygen_color.editingFinished.connect(lambda: self.set_line_style(oxygen_line_color=self.oxygen_color.text())); form.addRow("Oxygen line", self.oxygen_color)
        return page

    def _build_view_page(self) -> QWidget:
        page = QWidget(); form = QFormLayout(page); self._configure_form(form)
        self.view_ph_min = self._range_spin("viewPhMinControl", -2.0); form.addRow("pH min", self.view_ph_min)
        self.view_ph_max = self._range_spin("viewPhMaxControl", 16.0); form.addRow("pH max", self.view_ph_max)
        self.view_potential_min = self._range_spin("viewPotentialMinControl", -4.0); form.addRow("Potential min", self.view_potential_min)
        self.view_potential_max = self._range_spin("viewPotentialMaxControl", 4.0); form.addRow("Potential max", self.view_potential_max)
        return page

    def _build_export_page(self) -> QWidget:
        page = QWidget(); form = QFormLayout(page); self._configure_form(form)
        self.dpi_control = self._appearance_spin("exportDpiControl", 300, lambda value: None, maximum=2400); form.addRow("DPI", self.dpi_control)
        self.transparent_control = QCheckBox("Transparent background"); self.transparent_control.setObjectName("transparentBackgroundControl"); form.addRow(self.transparent_control)
        return page

    def _apply_light_palette(self) -> None:
        application = QApplication.instance()
        if application is not None:
            application.setStyle("Fusion")
        palette = QPalette()
        for group in (QPalette.ColorGroup.Active, QPalette.ColorGroup.Inactive):
            palette.setColor(group, QPalette.ColorRole.Window, QColor("#E6EAF0"))
            palette.setColor(group, QPalette.ColorRole.WindowText, QColor("#1F2937"))
            palette.setColor(group, QPalette.ColorRole.Base, QColor("#DCE1E7"))
            palette.setColor(group, QPalette.ColorRole.AlternateBase, QColor("#D3D9E0"))
            palette.setColor(group, QPalette.ColorRole.Text, QColor("#1F2937"))
            palette.setColor(group, QPalette.ColorRole.Button, QColor("#DCE4EC"))
            palette.setColor(group, QPalette.ColorRole.ButtonText, QColor("#1F2937"))
            palette.setColor(group, QPalette.ColorRole.Highlight, QColor("#2D83A7"))
            palette.setColor(group, QPalette.ColorRole.HighlightedText, QColor("#FFFFFF"))
            palette.setColor(group, QPalette.ColorRole.PlaceholderText, QColor("#657384"))
        disabled = QPalette.ColorGroup.Disabled
        palette.setColor(disabled, QPalette.ColorRole.Window, QColor("#E6EAF0"))
        palette.setColor(disabled, QPalette.ColorRole.WindowText, QColor("#7B8794"))
        palette.setColor(disabled, QPalette.ColorRole.Base, QColor("#E2E6EB"))
        palette.setColor(disabled, QPalette.ColorRole.AlternateBase, QColor("#DDE2E8"))
        palette.setColor(disabled, QPalette.ColorRole.Text, QColor("#7B8794"))
        palette.setColor(disabled, QPalette.ColorRole.Button, QColor("#E1E5EA"))
        palette.setColor(disabled, QPalette.ColorRole.ButtonText, QColor("#7B8794"))
        palette.setColor(disabled, QPalette.ColorRole.Highlight, QColor("#B5C0CB"))
        palette.setColor(disabled, QPalette.ColorRole.HighlightedText, QColor("#F4F6F8"))
        palette.setColor(disabled, QPalette.ColorRole.PlaceholderText, QColor("#8B96A2"))
        if application is not None:
            application.setPalette(palette)
        self.setPalette(palette)
        self.setStyleSheet(
            """
            QMainWindow, QDockWidget, QScrollArea, #diagramHost {
                background-color: #E6EAF0;
                color: #1F2937;
            }
            QToolBar, QDockWidget::title {
                background-color: #D3D9E0;
                color: #1F2937;
                border-bottom: 1px solid #AEB8C3;
            }
            QTabWidget::pane {
                background-color: #E6EAF0;
                border: 1px solid #AEB8C3;
            }
            QTabBar::tab {
                background-color: #D3D9E0;
                color: #344150;
                border: 1px solid #AEB8C3;
                padding: 6px 12px;
            }
            QTabBar::tab:selected {
                background-color: #F1F3F6;
                color: #1F2937;
            }
            QGroupBox {
                background-color: #F1F3F6;
                color: #1F2937;
                border: 1px solid #AEB8C3;
                border-radius: 4px;
                margin-top: 16px;
                padding: 12px 8px 8px 8px;
                font-weight: 600;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                left: 10px;
                padding: 2px 6px;
                background-color: #F1F3F6;
                color: #1F2937;
            }
            #regionsAndFillsGroup {
                background-color: #F1F3F6;
                border: 1px solid #AEB8C3;
                border-radius: 4px;
            }
            #regionsAndFillsTitle {
                background-color: transparent;
                border: none;
                color: #1F2937;
                font-weight: 600;
                padding: 2px 0 6px 0;
            }
            #advancedOptionsToggle {
                background-color: #D9EEF8;
                color: #17475C;
                border: 2px solid #2D83A7;
                border-radius: 4px;
                padding: 6px 8px;
                font-weight: 700;
            }
            #advancedOptionsToggle::indicator {
                width: 20px;
                height: 20px;
            }
            #advancedOptionsStatus {
                background-color: #E8EDF2;
                color: #5A6673;
                border: 1px solid #AEB8C3;
                border-radius: 4px;
                padding: 5px 7px;
                font-weight: 700;
            }
            QToolButton[sectionHeader="true"] {
                background-color: #E1E6EC;
                color: #1F2937;
                border: 1px solid #AEB8C3;
                border-radius: 3px;
                padding: 6px 9px;
                font-weight: 600;
                text-align: left;
            }
            QToolButton[sectionHeader="true"]:checked {
                background-color: #D1DAE3;
            }
            QWidget[sectionContent="true"] {
                background-color: #F1F3F6;
                border-left: 1px solid #AEB8C3;
                border-right: 1px solid #AEB8C3;
                border-bottom: 1px solid #AEB8C3;
            }
            QLineEdit, QComboBox, QDoubleSpinBox, QListWidget, QTableWidget {
                background-color: #DCE1E7;
                color: #1F2937;
                border: 1px solid #AEB8C3;
                selection-background-color: #2D83A7;
                selection-color: #FFFFFF;
            }
            QPushButton, QToolButton {
                background-color: #DCE4EC;
                color: #1F2937;
                border: 1px solid #9EABB8;
                border-radius: 4px;
                padding: 5px 8px;
            }
            QPushButton:hover, QToolButton:hover {
                background-color: #CAD6E1;
            }
            QPushButton:pressed, QToolButton:pressed {
                background-color: #B9C8D5;
            }
            QWidget:disabled, QPushButton:disabled, QToolButton:disabled,
            QLineEdit:disabled, QComboBox:disabled, QDoubleSpinBox:disabled {
                background-color: #E1E5EA;
                color: #7B8794;
                border-color: #C2CAD3;
            }
            QScrollBar:vertical {
                background-color: #D8DDE3;
                width: 12px;
            }
            QScrollBar::handle:vertical {
                background-color: #9EABB8;
                min-height: 28px;
                border-radius: 5px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            """
        )

    def _build_toolbar(self) -> None:
        toolbar = QToolBar("Tools", self); self.addToolBar(toolbar)
        toolbar.addAction("API Settings", self.show_api_settings)
        toolbar.addAction("Export Data", self._choose_data_export)
        toolbar.addAction("Export Figure", self._choose_figure_export)
        self.focus_plot_action = toolbar.addAction("Focus Plot")
        self.focus_plot_action.setCheckable(True)
        self.focus_plot_action.setShortcut("F11")
        self.focus_plot_action.toggled.connect(self.set_plot_focus)

    def set_plot_focus(self, focused: bool) -> None:
        if focused:
            self._dock_visibility_before_focus = (
                self.composition_dock.isVisible(), self.post_dock.isVisible(),
            )
            self.composition_dock.hide()
            self.post_dock.hide()
            self.statusBar().showMessage("Plot focus enabled. Press F11 to restore the sidebars.")
            return
        left_visible, right_visible = self._dock_visibility_before_focus
        self.composition_dock.setVisible(left_visible)
        self.post_dock.setVisible(right_visible)
        self.statusBar().showMessage("Sidebars restored.")

    def apply_screen_layout(self, available_width: int) -> bool:
        compact = available_width < 1600
        self.composition_dock.setMinimumWidth(220 if compact else 255)
        self.post_dock.setMinimumWidth(265 if compact else 310)
        if compact:
            self.resizeDocks(
                [self.composition_dock, self.post_dock], [225, 270],
                Qt.Orientation.Horizontal,
            )
        return compact

    def showEvent(self, event) -> None:
        super().showEvent(event)
        if self._screen_layout_applied:
            return
        screen = self.screen()
        if screen is not None:
            self.apply_screen_layout(screen.availableGeometry().width())
        self._screen_layout_applied = True

    def _appearance_spin(self, name, value, callback, *, maximum=100.0, step=0.1):
        control = QDoubleSpinBox(); control.setObjectName(name); control.setRange(0.0, maximum); control.setSingleStep(step); control.setValue(value); control.valueChanged.connect(callback); return control

    def _font_combo(self, name, value, callback):
        control = QFontComboBox(); control.setObjectName(name); control.setCurrentFont(QFont(value)); control.currentFontChanged.connect(lambda font: callback(font.family())); return control

    @staticmethod
    def _configure_form(form: QFormLayout) -> None:
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        form.setFormAlignment(Qt.AlignmentFlag.AlignTop)
        form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)
        form.setHorizontalSpacing(10)

    def _range_spin(self, name, value):
        control = QDoubleSpinBox(); control.setObjectName(name); control.setRange(-100.0, 100.0); control.setDecimals(3); control.setValue(value); return control

    def set_language(self, language: Language) -> None:
        self._language = language
        self.preferences.set_language(language)
        self.setWindowTitle("Pourbaix Studio R4" if language == "en" else "Pourbaix Studio R4 — 倒易图工作台")

    def show_snapshot(self, snapshot: ResultSnapshot) -> None:
        self.session.replace_success(snapshot)
        palette = ("#B0C4DE", "#C6E48B", "#F6C85F", "#E78AC3")
        self.interest_regions = [InterestRegion(label, color=palette[index % len(palette)], opacity=0.35) for index, label in enumerate(snapshot.stable_domain_labels[:4])]
        self.region_selector.clear(); self.region_selector.addItems(snapshot.stable_domain_labels)
        self._populate_interest_list()
        self.view_ph_min.setValue(snapshot.calculation_input.ph_range[0]); self.view_ph_max.setValue(snapshot.calculation_input.ph_range[1])
        self.view_potential_min.setValue(snapshot.calculation_input.potential_range[0]); self.view_potential_max.setValue(snapshot.calculation_input.potential_range[1])
        self.available_regions.clear(); self.available_regions.addItems(snapshot.stable_domain_labels)
        self.boundary_table.setRowCount(len(snapshot.boundaries))
        for row, boundary in enumerate(snapshot.boundaries):
            for column, value in enumerate((boundary.domain_label, boundary.vertex_index, boundary.ph, boundary.potential_v_she)):
                item = QTableWidgetItem(str(value))
                alignment = Qt.AlignmentFlag.AlignLeft if column == 0 else Qt.AlignmentFlag.AlignRight
                item.setTextAlignment(alignment | Qt.AlignmentFlag.AlignVCenter)
                self.boundary_table.setItem(row, column, item)
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
        figure = self._canvas.figure if self._canvas is not None else render_snapshot(snapshot, self.appearance, self.interest_regions, view_limits=self._view_limits())
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
        view_limits = self._view_limits()
        if view_limits is None: return
        figure = render_snapshot(snapshot, self.appearance, self.interest_regions, view_limits=view_limits)
        canvas = FigureCanvasQTAgg(figure)
        toolbar = NavigationToolbar2QT(canvas, self); toolbar.setObjectName("plotNavigationToolbar")
        while self.diagram_layout.count():
            child = self.diagram_layout.takeAt(0).widget()
            if child is not None: child.deleteLater()
        self.diagram_layout.addWidget(toolbar); self.diagram_layout.addWidget(canvas)
        self._canvas = canvas

    def _view_limits(self):
        ph_range = (self.view_ph_min.value(), self.view_ph_max.value())
        potential_range = (self.view_potential_min.value(), self.view_potential_max.value())
        if ph_range[0] >= ph_range[1] or potential_range[0] >= potential_range[1]:
            self.statusBar().showMessage("View minimum must be smaller than maximum.")
            return None
        return ph_range, potential_range

    def replot_current_result(self) -> None:
        if self.session.snapshot is None:
            self.statusBar().showMessage("Generate a diagram before re-plotting.")
            return
        self._render()
        self.statusBar().showMessage("Re-plotted from the current result; no API request was made.")

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
        self.interest_regions[index] = replace(
            self.interest_regions[index],
            color=self._selected_region_color,
            opacity=self.region_opacity.value() / 100.0,
        )
        self._populate_interest_list(current_row=index)
        self._render()

    def choose_selected_region_color(self) -> None:
        color = QColorDialog.getColor(QColor(self._selected_region_color), self, "Selected region fill")
        if color.isValid():
            self.set_selected_region_color(color.name())

    def set_selected_region_color(self, color: str) -> None:
        selected = QColor(color)
        if not selected.isValid():
            self.statusBar().showMessage("Choose a valid fill color.")
            return
        self._selected_region_color = selected.name()
        self._refresh_region_color_button()

    def _refresh_region_color_button(self) -> None:
        self.region_color_button.setText(self._selected_region_color.upper())
        self.region_color_button.setStyleSheet(
            f"QPushButton {{ background-color: {self._selected_region_color}; color: #172033; }}"
        )

    def _update_region_opacity_label(self, value: int) -> None:
        self.region_opacity_label.setText(f"{value}%")

    def _populate_interest_list(self, current_row=0) -> None:
        self.interest_list.blockSignals(True)
        self.interest_list.clear()
        for region in self.interest_regions:
            item = QListWidgetItem(region.label)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(Qt.CheckState.Checked if region.visible else Qt.CheckState.Unchecked)
            self.interest_list.addItem(item)
        self.interest_list.blockSignals(False)
        if self.interest_regions:
            self.interest_list.setCurrentRow(min(current_row, len(self.interest_regions) - 1))

    def _load_interest_style(self, index: int) -> None:
        if 0 <= index < len(self.interest_regions):
            region = self.interest_regions[index]
            self.set_selected_region_color(region.color)
            self.region_opacity.setValue(round(region.opacity * 100))

    def _interest_visibility_changed(self, item) -> None:
        index = self.interest_list.row(item)
        if 0 <= index < len(self.interest_regions):
            visible = item.checkState() == Qt.CheckState.Checked
            self.interest_regions[index] = replace(self.interest_regions[index], visible=visible)
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
        self._populate_interest_list(current_row=len(self.interest_regions) - 1)
        self._render()

    def _add_selected_region(self) -> None:
        label = self.region_selector.currentText()
        if label:
            self.add_interest_region(label)

    def remove_interest_region(self, index: int) -> None:
        if 0 <= index < len(self.interest_regions):
            self.interest_regions.pop(index)
            self._populate_interest_list(current_row=max(0, index - 1))
            self._render()

    def interest_region_count(self) -> int:
        return len(self.interest_regions)
