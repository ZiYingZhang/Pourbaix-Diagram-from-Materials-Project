"""Portable application paths for source and frozen R4 launches."""

from __future__ import annotations

import sys
from pathlib import Path


def application_base_dir() -> Path:
    """Return the directory users can move together with the application."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[1]


def application_resource_path(relative_path: str | Path) -> Path:
    """Resolve a bundled read-only asset in source and PyInstaller launches."""
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        resource_root = Path(sys._MEIPASS)
    else:
        resource_root = Path(__file__).resolve().parents[1]
    return resource_root / Path(relative_path)


def legacy_api_key_path() -> Path:
    """Locate the read-only R2/R3 plaintext-key compatibility file."""
    return application_base_dir() / "mp_api_key.txt"
