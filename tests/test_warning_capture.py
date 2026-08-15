import warnings

from pourbaix_core import install_warning_capture, last_captured_warning


def test_warnings_are_captured_for_local_logging():
    previous_showwarning = warnings.showwarning
    try:
        install_warning_capture()
        warnings.warn("diagnostic probe warning", UserWarning)

        captured = last_captured_warning()

        assert captured is not None
        assert "diagnostic probe warning" in captured
    finally:
        warnings.showwarning = previous_showwarning
