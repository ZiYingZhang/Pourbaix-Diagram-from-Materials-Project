import pytest

from pourbaix_core import InputValidationError
from pourbaix_gui_R3 import PourbaixApp


def test_gui_defaults_to_titanium_oxide_system_with_one_titanium_ratio(qapplication):
    window = PourbaixApp()
    try:
        assert window.elements_input.text() == "Ti,O"
        assert window.ratios_input.text() == "1.0"
    finally:
        window.close()


@pytest.mark.parametrize("action_name", ["plot_pourbaix", "export_data"])
def test_invalid_ratio_count_is_rejected_before_entry_fetch(qapplication, action_name):
    window = PourbaixApp()
    errors = []

    def forbidden_fetch(*args, **kwargs):
        raise AssertionError("entry fetch must not run for invalid input")

    try:
        window.elements_input.setText("Ti,O")
        window.ratios_input.setText("1,2")
        window.api_input.setText("not-a-real-key")
        window._safe_get_entries = forbidden_fetch
        window._report_error = lambda _title, exc: errors.append(exc)

        getattr(window, action_name)()

        assert len(errors) == 1
        assert isinstance(errors[0], InputValidationError)
    finally:
        window.close()
