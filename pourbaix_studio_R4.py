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


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Pourbaix Studio R4")
    parser.add_argument("--self-test", action="store_true", help="verify runtime dependencies")
    arguments = parser.parse_args(argv)

    if arguments.self_test:
        return run_self_test()
    parser.error("the R4 workbench is not available until the UI tasks are implemented")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
