import os
import sys
import warnings

import pourbaix_core
import pourbaix_studio_R4
from pourbaix_core import install_warning_capture, last_captured_warning


def test_windowed_entrypoint_recovers_missing_standard_streams(monkeypatch):
    with monkeypatch.context() as patch:
        patch.setattr(sys, "stdout", None)
        patch.setattr(sys, "stderr", None)

        assert pourbaix_studio_R4.main(["--self-test"]) == 0
        assert callable(sys.stdout.write)
        assert callable(sys.stderr.write)
        assert os.environ["TQDM_DISABLE"] == "1"


def test_warning_capture_does_not_crash_without_standard_error(monkeypatch):
    def windowed_showwarning(message, category, filename, lineno, file=None, line=None):
        target = file if file is not None else sys.stderr
        target.write(str(message))

    with warnings.catch_warnings():
        warnings.simplefilter("always")
        install_warning_capture()
        with monkeypatch.context() as patch:
            patch.setattr(pourbaix_core, "_ORIGINAL_SHOWWARNING", windowed_showwarning)
            patch.setattr(sys, "stderr", None)
            warnings.warn("windowed diagnostic warning", UserWarning)

    assert "windowed diagnostic warning" in (last_captured_warning() or "")
