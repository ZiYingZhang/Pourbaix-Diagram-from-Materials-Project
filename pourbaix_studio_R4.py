"""Command-line entry point for Pourbaix Studio R4."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import sys
from typing import Sequence


def prepare_windowed_runtime() -> None:
    """Make console-oriented dependencies safe in a windowed executable."""
    os.environ.setdefault("TQDM_DISABLE", "1")
    for stream_name in ("stdout", "stderr"):
        stream = getattr(sys, stream_name, None)
        if not callable(getattr(stream, "write", None)):
            setattr(sys, stream_name, open(os.devnull, "w", encoding="utf-8"))


def run_self_test() -> int:
    """Verify R4's runtime dependencies without creating a Qt application."""
    import keyring  # noqa: F401
    import matplotlib  # noqa: F401
    import pandas  # noqa: F401
    import shapely  # noqa: F401
    from PySide6 import QtCore  # noqa: F401
    from pymatgen.analysis import pourbaix_diagram  # noqa: F401

    print("R4 self-test: OK")
    return 0


def run_gui_smoke() -> int:
    """Construct and close the offline workbench without a network request."""
    from PySide6.QtWidgets import QApplication
    from pourbaix_r4.ui.main_window import PourbaixStudioMainWindow

    application = QApplication.instance() or QApplication([])
    window = PourbaixStudioMainWindow()
    window.show()
    application.processEvents()
    window.close()
    print("R4 GUI smoke: OK")
    return 0


def run_mpcontribs_smoke() -> int:
    """Load MPContribs and its RFC3987 grammar without making a network request."""
    import mpcontribs.client  # noqa: F401
    import rfc3987_syntax

    grammar = Path(rfc3987_syntax.__file__).with_name("syntax_rfc3987.lark")
    if not grammar.is_file():
        raise RuntimeError(f"MPContribs parser grammar is missing: {grammar}")
    print("R4 MPContribs smoke: OK")
    return 0


def run_gui() -> int:
    from PySide6.QtWidgets import QApplication
    from pourbaix_r4.ui.main_window import PourbaixStudioMainWindow

    application = QApplication.instance() or QApplication([])
    window = PourbaixStudioMainWindow()
    window.show()
    return application.exec()


def main(argv: Sequence[str] | None = None) -> int:
    prepare_windowed_runtime()
    parser = argparse.ArgumentParser(description="Pourbaix Studio R4")
    parser.add_argument("--self-test", action="store_true", help="verify runtime dependencies")
    parser.add_argument("--gui-smoke", action="store_true", help="construct and close the offline workbench")
    parser.add_argument("--mpcontribs-smoke", action="store_true", help="verify offline MPContribs parser resources")
    arguments = parser.parse_args(argv)

    if arguments.self_test:
        return run_self_test()
    if arguments.gui_smoke:
        return run_gui_smoke()
    if arguments.mpcontribs_smoke:
        return run_mpcontribs_smoke()
    return run_gui()


if __name__ == "__main__":
    raise SystemExit(main())
