from pathlib import Path

from PySide6.QtGui import QIcon

from pourbaix_r4.paths import application_resource_path
from pourbaix_r4.ui.main_window import PourbaixStudioMainWindow


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def test_source_branding_asset_resolves_to_a_loadable_icon(qapplication):
    icon_path = application_resource_path("assets/pourbaix-studio-r4.png")

    assert icon_path == PROJECT_ROOT / "assets" / "pourbaix-studio-r4.png"
    assert icon_path.is_file()
    assert not QIcon(str(icon_path)).isNull()


def test_main_window_uses_the_project_icon(qapplication):
    window = PourbaixStudioMainWindow()
    try:
        assert not window.windowIcon().isNull()
    finally:
        window.close()
