from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDockWidget, QPushButton, QTabWidget

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
        assert {"System and conditions", "Interest regions"}.issubset(docks)
        tabs = window.findChild(QTabWidget, "workspaceTabs")
        assert [tabs.tabText(index) for index in range(tabs.count())] == ["Diagram", "Available regions", "Boundary data"]

        window.show_snapshot(_snapshot())
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
