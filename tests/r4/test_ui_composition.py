from dataclasses import dataclass

from PySide6.QtCore import QUrl

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
        assert panel.advanced_options.isCheckable() is True
        assert panel.heatmap_toggle.isEnabled() is False
        assert panel.heatmap_entry.isEnabled() is False
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
