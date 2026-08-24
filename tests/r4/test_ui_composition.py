from dataclasses import dataclass

from PySide6.QtCore import Qt, QUrl

from pourbaix_r4.ui.api_dialog import ApiSettingsDialog
from pourbaix_r4.ui.composition_panel import CompositionPanel, PeriodicTableDialog


def test_formula_quick_fill_and_open_species_regenerate_ratio_rows(qapplication):
    panel = CompositionPanel()
    try:
        panel.apply_formula("Sb2Se3")
        assert panel.selected_elements() == ("Sb", "Se")
        assert panel.ratio_values() == {"Sb": "2.0", "Se": "3.0"}

        panel.set_selected_elements(("Sb", "Se", "O", "H"))
        assert panel.selected_elements() == ("Sb", "Se", "O", "H")
        assert panel.ratio_values() == {"Sb": "2.0", "Se": "3.0"}
        assert "open reservoir" in panel.open_species_notice.text().lower()
    finally:
        panel.close()


def test_formula_commit_builds_summary_concentrations_and_heatmap_placeholder(qapplication):
    panel = CompositionPanel()
    try:
        panel.formula_input.setText("Sb2Se3")
        panel.formula_input.editingFinished.emit()
        assert panel.element_chip_texts() == ("Sb", "Se")
        assert panel.composition_summary.text() == "Sb : Se = 2 : 3"
        assert panel.concentration_values() == {"Sb": "0.000001", "Se": "0.000001"}
        assert panel.filter_solids.isChecked() is True
        assert panel.advanced_options_toggle.text() == "Enable advanced options"
        assert panel.advanced_options_toggle.isChecked() is False
        assert panel.advanced_options_toggle.minimumHeight() >= 32
        assert panel.advanced_options_status.text() == "OPTIONAL · OFF"
        assert panel.advanced_options_content.isEnabled() is False
        assert panel.heatmap_toggle.isEnabled() is False
        assert panel.heatmap_entry.isEnabled() is False
    finally:
        panel.close()


def test_diagram_range_defaults_match_materials_project_full_view(qapplication):
    panel = CompositionPanel()
    try:
        assert (panel.ph_min.text(), panel.ph_max.text()) == ("-2", "16")
        assert (panel.potential_min.text(), panel.potential_max.text()) == ("-4", "4")
    finally:
        panel.close()


def test_composition_sections_use_uppercase_titles_and_aligned_form_columns(qapplication):
    panel = CompositionPanel()
    try:
        expected_alignment = Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        assert panel.ratio_group.title() == "COMPOSITION CONTROL"
        assert panel.advanced_options.title() == "ADVANCED OPTIONS — OPTIONAL"
        assert panel.ratio_form.labelAlignment() == expected_alignment
        assert panel.concentration_form.labelAlignment() == expected_alignment
    finally:
        panel.close()


def test_explicit_advanced_options_toggle_enables_optional_controls(qapplication):
    panel = CompositionPanel()
    try:
        panel.advanced_options_toggle.click()
        assert panel.advanced_options_toggle.isChecked() is True
        assert panel.advanced_options_status.text() == "OPTIONAL · ON"
        assert panel.advanced_options_content.isEnabled() is True
        assert panel.filter_solids.isEnabled() is True
    finally:
        panel.close()


def test_ratio_draft_keeps_live_summary_responsive_until_validation(qapplication):
    panel = CompositionPanel()
    try:
        panel.apply_formula("Sb2Se3")
        panel.set_ratio_value("Sb", "draft")
        assert panel.composition_summary.text() == "Sb : Se = ? : 3"
    finally:
        panel.close()


def test_all_periodic_table_symbols_are_available_and_valid_input_emits_request(qapplication):
    panel = CompositionPanel()
    received = []
    panel.calculation_requested.connect(received.append)
    try:
        assert "H" in panel.available_element_symbols()
        assert "Og" in panel.available_element_symbols()
        panel.set_selected_elements(("Fe", "Ni"))
        panel.set_ratio_value("Fe", "1")
        panel.set_ratio_value("Ni", "1")
        panel.request_calculation()

        assert len(received) == 1
        assert received[0].comp_dict == {"Fe": 1.0, "Ni": 1.0}
        assert received[0].conc_dict == {"Fe": 1e-6, "Ni": 1e-6}
    finally:
        panel.close()


def test_searchable_periodic_table_selection_rebuilds_editor(qapplication):
    dialog = PeriodicTableDialog(("Sb",))
    panel = CompositionPanel()
    try:
        dialog.search_input.setText("iron")
        assert dialog.matching_symbols() == ("Fe",)

        dialog.set_selected_symbols(("Fe", "Ni", "O"))
        assert dialog.selected_symbols() == ("Fe", "Ni", "O")

        panel.apply_element_selection(dialog.selected_symbols())
        assert panel.selected_elements() == ("Fe", "Ni", "O")
        assert panel.ratio_values() == {"Fe": "1.0", "Ni": "1.0"}
        assert panel.concentration_values() == {
            "Fe": "0.000001",
            "Ni": "0.000001",
        }

        panel.remove_element("Ni")
        assert panel.selected_elements() == ("Fe", "O")
        assert panel.ratio_values() == {"Fe": "1.0"}
    finally:
        dialog.close()
        panel.close()


def test_periodic_table_uses_standard_positions_and_marks_open_reservoirs(qapplication):
    dialog = PeriodicTableDialog(("Ti", "O"))
    try:
        assert dialog.width() <= 1040
        positions = {}
        for symbol in ("H", "He", "Fe", "La", "Ce"):
            index = dialog.periodic_grid.indexOf(dialog.element_buttons[symbol])
            row, column, _row_span, _column_span = dialog.periodic_grid.getItemPosition(index)
            positions[symbol] = (row, column)

        assert positions == {
            "H": (0, 0), "He": (0, 17), "Fe": (3, 7), "La": (7, 2), "Ce": (7, 3),
        }
        assert dialog.element_buttons["H"].property("openReservoir") is True
        assert dialog.element_buttons["O"].property("openReservoir") is True
        assert dialog.selection_count.text() == "Closed elements: 1/4 · Open reservoirs: O"
        assert dialog.selected_chip_texts() == ("Ti", "O")
    finally:
        dialog.close()


def test_periodic_table_search_highlights_matches_and_clear_resets_draft(qapplication):
    dialog = PeriodicTableDialog(("Fe", "O"))
    try:
        dialog.search_input.setText("iron")
        assert dialog.element_buttons["Fe"].property("searchMatch") is True
        assert dialog.element_buttons["Ni"].property("searchDimmed") is True

        dialog.clear_selection_button.click()
        assert dialog.selected_symbols() == ()
        assert dialog.selected_chip_texts() == ()
        assert dialog.selection_count.text() == "Closed elements: 0/4 · Open reservoirs: none"
    finally:
        dialog.close()


def test_element_picker_rejects_fifth_closed_element_without_losing_last_valid_state(qapplication):
    panel = CompositionPanel()
    errors = []
    panel.validation_failed.connect(errors.append)
    try:
        panel.set_selected_elements(("Fe", "Ni", "Co", "Cr", "O"))
        assert panel.ratio_values() == {"Fe": "1.0", "Ni": "1.0", "Co": "1.0", "Cr": "1.0"}

        panel.set_selected_elements(("Fe", "Ni", "Co", "Cr", "Mn", "O"))
        assert panel.selected_elements() == ("Fe", "Ni", "Co", "Cr", "O")
        assert errors and "at most 4" in errors[-1]
    finally:
        panel.close()


def test_periodic_table_prevents_clicking_a_fifth_closed_element(qapplication):
    dialog = PeriodicTableDialog(("Fe", "Ni", "Co", "Cr", "O"))
    try:
        dialog.element_buttons["Mn"].click()
        assert dialog.selected_symbols() == ("Fe", "Ni", "Co", "Cr", "O")
        assert "Up to 4" in dialog.selection_limit_notice.text()
    finally:
        dialog.close()


@dataclass
class FakeStore:
    value: str | None = None
    def get(self): return self.value
    def set(self, value): self.value = value
    def delete(self): self.value = None


def test_api_dialog_masks_remembers_forgets_and_exposes_direct_links(qapplication):
    opened = []
    store = FakeStore()
    dialog = ApiSettingsDialog(store=store, open_url=lambda url: opened.append(url))
    try:
        assert dialog.api_input.echoMode() != dialog.api_input.EchoMode.Normal
        dialog.api_input.setText("test-secret")
        dialog.remember_current_key()
        assert store.value == "test-secret"
        dialog.forget_saved_key()
        assert store.value is None
        dialog.open_key_page()
        dialog.open_documentation()
        assert [url.toString() for url in opened] == [
            "https://next-gen.materialsproject.org/api",
            "https://docs.materialsproject.org/downloading-data/using-the-api/getting-started",
        ]
        assert dialog.api_key_link.text() == "Get a Materials Project API key"
        dialog.api_key_link.click()
        assert opened[-1].toString() == "https://next-gen.materialsproject.org/api"
    finally:
        dialog.close()
