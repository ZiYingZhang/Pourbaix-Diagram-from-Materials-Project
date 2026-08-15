from pourbaix_core import InputValidationError
from pourbaix_gui_R3 import PourbaixApp


def test_failed_new_plot_invalidates_previous_figure_and_metadata(qapplication):
    window = PourbaixApp()
    errors = []
    try:
        window._last_figure = object()
        window._last_elements = ["Fe"]
        window._last_comp_dict = {"Fe": 1.0}
        window.elements_input.setText("Ti,O")
        window.ratios_input.setText("1,2")
        window._report_error = lambda _title, exc: errors.append(exc)

        window.plot_pourbaix()

        assert len(errors) == 1
        assert isinstance(errors[0], InputValidationError)
        assert window._last_figure is None
        assert window._last_elements == []
        assert window._last_comp_dict == {}
    finally:
        window.close()
