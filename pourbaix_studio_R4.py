"""Command-line entry point for Pourbaix Studio R4."""

from __future__ import annotations

import argparse
from importlib.metadata import version
from typing import Sequence


def run_self_test() -> int:
    """Verify R4's runtime dependencies without creating a Qt application."""
    import keyring  # noqa: F401
    import matplotlib  # noqa: F401
    import pandas  # noqa: F401
    import shapely  # noqa: F401
    from PySide6 import QtCore  # noqa: F401
    from pymatgen.analysis import pourbaix_diagram  # noqa: F401

    for distribution in ("PySide6", "keyring", "mp-api", "pymatgen", "pymatgen-core"):
        version(distribution)
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


def run_gui() -> int:
    from PySide6.QtWidgets import QApplication
    from pourbaix_r4.ui.main_window import PourbaixStudioMainWindow

    application = QApplication.instance() or QApplication([])
    window = PourbaixStudioMainWindow()
    window.show()
    return application.exec()


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Pourbaix Studio R4")
    parser.add_argument("--self-test", action="store_true", help="verify runtime dependencies")
    parser.add_argument("--gui-smoke", action="store_true", help="construct and close the offline workbench")
    arguments = parser.parse_args(argv)

    if arguments.self_test:
        return run_self_test()
    if arguments.gui_smoke:
        return run_gui_smoke()
    return run_gui()


if __name__ == "__main__":
    raise SystemExit(main())
