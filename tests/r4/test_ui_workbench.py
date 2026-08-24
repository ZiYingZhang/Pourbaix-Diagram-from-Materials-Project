from PySide6.QtCore import Qt
from PySide6.QtGui import QPalette
from PySide6.QtWidgets import QCheckBox, QComboBox, QDockWidget, QDoubleSpinBox, QFrame, QHeaderView, QLabel, QPushButton, QScrollArea, QSlider, QTabWidget, QToolBar, QToolBox

from pourbaix_core import FetchResult
from pourbaix_r4.credentials import ResolvedCredential
from pourbaix_r4.models import BoundaryRecord, CalculationInput, ResultSnapshot
from pourbaix_r4.ui.main_window import PourbaixStudioMainWindow


def _snapshot():
    return ResultSnapshot(
        CalculationInput(("Fe", "Ni"), (("Fe", 1.0), ("Ni", 1.0)), (0, 14), (-2, 4)),
        ("Fe(s)",),
        (BoundaryRecord("Fe(s)", 0, -2), BoundaryRecord("Fe(s)", 14, 4), BoundaryRecord("Fe(s)", 7, 1)),
        2,
    )


def test_workbench_exposes_required_docks_tabs_and_dynamic_interest_regions(qapplication):
    window = PourbaixStudioMainWindow()
    try:
        docks = {dock.windowTitle() for dock in window.findChildren(QDockWidget)}
        assert {"System and conditions", "Post-processing"}.issubset(docks)
        tabs = window.findChild(QTabWidget, "workspaceTabs")
        assert [tabs.tabText(index) for index in range(tabs.count())] == ["Diagram", "Available regions", "Boundary data"]

        window.show_snapshot(_snapshot())
        assert len(window.interest_regions) == 1
        canvas = window.diagram_layout.itemAt(1).widget()
        assert len(canvas.figure.axes[0].patches) >= 1
        assert window.interest_region_count() == 1
        window.add_interest_region("Fe(s)")
        assert window.interest_region_count() == 1
        window.remove_interest_region(0)
        assert window.interest_region_count() == 0
    finally:
        window.close()


def test_language_switch_and_input_change_preserve_or_invalidate_correct_state(qapplication):
    window = PourbaixStudioMainWindow()
    try:
        snapshot = _snapshot()
        window.show_snapshot(snapshot)
        window.set_language("zh_CN")
        assert window.windowTitle().startswith("Pourbaix")
        assert window.session.exportable_snapshot is snapshot
        window.composition_panel.input_changed.emit()
        assert window.session.exportable_snapshot is None
    finally:
        window.close()


def test_generate_uses_injected_runtime_services_and_replaces_snapshot(qapplication):
    calls = []
    class Entries:
        def fetch(self, elements, api_key):
            calls.append((tuple(elements), api_key)); return FetchResult(["entry"], False)
    def resolve(): return ResolvedCredential("current_ui", "runtime-secret")
    def calculate(inputs, entries):
        assert entries == ["entry"]
        return _snapshot()

    window = PourbaixStudioMainWindow(entry_service=Entries(), credential_resolver=resolve, calculate=calculate)
    try:
        window.composition_panel.set_selected_elements(("Fe", "Ni"))
        window.composition_panel.request_calculation()
        assert calls == [(("Fe", "Ni"), "runtime-secret")]
        assert window.session.exportable_snapshot is not None
        assert window.available_regions.count() == 1
    finally:
        window.close()


def test_interest_region_toolbar_controls_add_and_remove_selected_region(qapplication):
    window = PourbaixStudioMainWindow()
    try:
        window.show_snapshot(_snapshot())
        window.available_regions.setCurrentRow(0)
        window.findChild(QPushButton, "addInterestRegionButton").click()
        assert window.interest_region_count() == 1
        window.interest_list.setCurrentRow(0)
        window.findChild(QPushButton, "removeInterestRegionButton").click()
        assert window.interest_region_count() == 0
    finally:
        window.close()


def test_workbench_exports_current_snapshot_without_refetching(qapplication, tmp_path):
    window = PourbaixStudioMainWindow()
    try:
        window.show_snapshot(_snapshot())
        output = window.export_current_data(tmp_path / "boundaries.csv", "csv")
        assert output.is_file()
        assert "domain_label" in output.read_text(encoding="utf-8")
    finally:
        window.close()


def test_workbench_exports_rendered_snapshot_image_without_refetching(qapplication, tmp_path):
    window = PourbaixStudioMainWindow()
    try:
        window.show_snapshot(_snapshot())
        output = window.export_current_figure(tmp_path / "diagram.png", "png", dpi=144, transparent=True)
        assert output.is_file()
        assert output.stat().st_size > 0
    finally:
        window.close()


def test_workbench_appearance_updates_rendering_without_invalidating_snapshot(qapplication):
    window = PourbaixStudioMainWindow()
    try:
        snapshot = _snapshot(); window.show_snapshot(snapshot)
        window.set_show_ion_labels(False)
        assert window.appearance.show_ion_labels is False
        assert window.session.exportable_snapshot is snapshot
    finally:
        window.close()


def test_workbench_updates_line_style_without_invalidating_snapshot(qapplication):
    window = PourbaixStudioMainWindow()
    try:
        snapshot = _snapshot(); window.show_snapshot(snapshot)
        window.set_line_style(spine_width=2.5, stability_line_width=3.0, hydrogen_line_color="#123456")
        assert window.appearance.spine_width == 2.5
        assert window.appearance.stability_line_width == 3.0
        assert window.appearance.hydrogen_line_color == "#123456"
        assert window.session.exportable_snapshot is snapshot
    finally:
        window.close()


def test_appearance_line_width_control_updates_snapshot_preserving_style(qapplication):
    window = PourbaixStudioMainWindow()
    try:
        window.show_snapshot(_snapshot())
        control = window.findChild(QDoubleSpinBox, "spineWidthControl")
        control.setValue(2.2)
        assert window.appearance.spine_width == 2.2
        assert window.findChild(QComboBox, "ionLabelFontControl") is not None
        assert window.findChild(QComboBox, "axisTickFontControl") is not None
        assert window.findChild(QCheckBox, "transparentBackgroundControl") is not None
        assert window.findChild(QDoubleSpinBox, "exportDpiControl") is not None
    finally:
        window.close()


def test_toolbar_defers_partial_bilingual_switch_and_exposes_figure_export(qapplication):
    window = PourbaixStudioMainWindow()
    try:
        action_texts = [action.text() for action in window.findChildren(QToolBar)[0].actions()]
        assert "中文" not in action_texts
        assert "English" not in action_texts
        assert action_texts == ["API Settings", "Export Data", "Export Figure"]
    finally:
        window.close()


def test_replot_uses_current_snapshot_without_fetch_or_calculation(qapplication):
    fetch_calls = []
    calculate_calls = []

    class Entries:
        def fetch(self, elements, api_key):
            fetch_calls.append((elements, api_key))

    def calculate(*args):
        calculate_calls.append(args)

    window = PourbaixStudioMainWindow(entry_service=Entries(), calculate=calculate)
    try:
        snapshot = _snapshot()
        window.show_snapshot(snapshot)
        window.findChild(QDoubleSpinBox, "viewPhMinControl").setValue(-1.0)
        window.findChild(QDoubleSpinBox, "viewPhMaxControl").setValue(10.0)
        window.findChild(QDoubleSpinBox, "viewPotentialMinControl").setValue(-1.5)
        window.findChild(QDoubleSpinBox, "viewPotentialMaxControl").setValue(2.5)
        window.findChild(QPushButton, "replotButton").click()

        canvas = window.diagram_layout.itemAt(1).widget()
        assert canvas.figure.axes[0].get_xlim() == (-1.0, 10.0)
        assert canvas.figure.axes[0].get_ylim() == (-1.5, 2.5)
        assert fetch_calls == []
        assert calculate_calls == []
        assert window.session.exportable_snapshot is snapshot
    finally:
        window.close()


def test_right_panel_exposes_region_selector_and_interactive_navigation(qapplication):
    window = PourbaixStudioMainWindow()
    try:
        window.show_snapshot(_snapshot())
        selector = window.findChild(QComboBox, "regionSelectorControl")
        assert selector.itemText(0) == "Fe(s)"
        assert window.findChild(QToolBar, "plotNavigationToolbar") is not None
    finally:
        window.close()


def test_sidebars_scroll_and_region_color_controls_share_one_section(qapplication):
    window = PourbaixStudioMainWindow()
    try:
        query_scroll = window.findChild(QScrollArea, "queryScrollArea")
        post_scroll = window.findChild(QScrollArea, "postProcessingScrollArea")
        regions_group = window.findChild(QFrame, "regionsAndFillsGroup")
        color_button = window.findChild(QPushButton, "regionColorButton")
        opacity_slider = window.findChild(QSlider, "regionOpacitySlider")

        assert query_scroll.widgetResizable() is True
        assert post_scroll.widgetResizable() is True
        assert regions_group.isAncestorOf(color_button)
        assert regions_group.isAncestorOf(opacity_slider)
        assert window.palette().color(QPalette.ColorRole.Window).lightness() > 128
    finally:
        window.close()


def test_postprocessing_titles_and_boundary_table_use_clear_alignment(qapplication):
    window = PourbaixStudioMainWindow()
    try:
        regions_group = window.findChild(QFrame, "regionsAndFillsGroup")
        regions_title = window.findChild(QLabel, "regionsAndFillsTitle")
        toolbox = window.findChild(QToolBox, "postProcessingSections")
        assert regions_title.text() == "REGIONS AND FILLS"
        assert regions_group.isAncestorOf(regions_title)
        assert [toolbox.itemText(index) for index in range(toolbox.count())] == [
            "LABELS AND FONTS",
            "LINES AND AXES",
            "VIEW RANGE",
            "IMAGE EXPORT",
        ]
        assert window.boundary_table.horizontalHeaderItem(0).text() == "DOMAIN LABEL"
        assert all(
            window.boundary_table.horizontalHeader().sectionResizeMode(column)
            == QHeaderView.ResizeMode.Stretch
            for column in range(4)
        )

        window.show_snapshot(_snapshot())
        assert window.boundary_table.item(0, 0).textAlignment() & Qt.AlignmentFlag.AlignLeft
        assert window.boundary_table.item(0, 1).textAlignment() & Qt.AlignmentFlag.AlignRight
        assert window.boundary_table.item(0, 2).textAlignment() & Qt.AlignmentFlag.AlignRight
        assert window.boundary_table.item(0, 3).textAlignment() & Qt.AlignmentFlag.AlignRight
    finally:
        window.close()


def test_shallow_gray_theme_keeps_active_and_disabled_controls_readable(qapplication):
    window = PourbaixStudioMainWindow()
    try:
        palette = window.palette()
        assert qapplication.style().objectName().casefold() == "fusion"
        assert palette.color(QPalette.ColorGroup.Active, QPalette.ColorRole.Window).name() == "#e6eaf0"
        assert palette.color(QPalette.ColorGroup.Active, QPalette.ColorRole.WindowText).name() == "#1f2937"
        assert palette.color(QPalette.ColorGroup.Disabled, QPalette.ColorRole.ButtonText).name() == "#7b8794"
        assert palette.color(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Text).name() == "#7b8794"
    finally:
        window.close()


def test_selected_region_color_and_opacity_are_applied_together(qapplication):
    window = PourbaixStudioMainWindow()
    try:
        snapshot = _snapshot()
        window.show_snapshot(snapshot)
        window.interest_list.setCurrentRow(0)
        window.set_selected_region_color("#123456")
        window.findChild(QSlider, "regionOpacitySlider").setValue(55)
        window.apply_selected_region_style()

        assert window.interest_regions[0].color == "#123456"
        assert window.interest_regions[0].opacity == 0.55
        assert window.session.exportable_snapshot is snapshot
    finally:
        window.close()


def test_composition_validation_is_visible_in_workbench_status(qapplication):
    window = PourbaixStudioMainWindow()
    try:
        window.composition_panel.validation_failed.emit("Up to 4 elements are supported")
        assert window.statusBar().currentMessage() == "Up to 4 elements are supported"
    finally:
        window.close()


def test_workbench_applies_full_appearance_options_without_staling_snapshot(qapplication):
    window = PourbaixStudioMainWindow()
    try:
        snapshot = _snapshot(); window.show_snapshot(snapshot)
        window.apply_appearance(ion_label_font_size=18, axis_tick_font_size=16, major_tick_length=9, show_minor_ticks=False, oxygen_line_color="#654321")
        assert window.appearance.ion_label_font_size == 18
        assert window.appearance.axis_tick_font_size == 16
        assert window.appearance.major_tick_length == 9
        assert window.appearance.show_minor_ticks is False
        assert window.appearance.oxygen_line_color == "#654321"
        assert window.session.exportable_snapshot is snapshot
    finally:
        window.close()
