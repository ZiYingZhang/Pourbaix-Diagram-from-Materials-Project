import os
from pathlib import Path

import pytest


os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("MPLBACKEND", "Agg")
os.environ.setdefault("MPLCONFIGDIR", str(Path(".pytest_cache") / "matplotlib"))
os.environ["LOCALAPPDATA"] = str(Path(".pytest_cache") / "local-app-data")


@pytest.fixture(scope="session")
def qapplication():
    from PyQt5.QtWidgets import QApplication

    app = QApplication.instance() or QApplication([])
    yield app
