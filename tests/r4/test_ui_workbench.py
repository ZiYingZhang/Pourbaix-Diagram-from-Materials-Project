from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDockWidget, QTabWidget

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
