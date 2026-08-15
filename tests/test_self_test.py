import os
from pathlib import Path
import subprocess
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = PROJECT_ROOT / "pourbaix_gui_R3.py"


def _subprocess_env(tmp_path):
    env = os.environ.copy()
    env["LOCALAPPDATA"] = str(tmp_path / "local-app-data")
    env["MPLCONFIGDIR"] = str(tmp_path / "matplotlib")
    env["QT_QPA_PLATFORM"] = "offscreen"
    return env


def test_self_test_exits_without_starting_gui(tmp_path):
    completed = subprocess.run(
        [sys.executable, str(SCRIPT), "--self-test"],
        cwd=PROJECT_ROOT,
        env=_subprocess_env(tmp_path),
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr
    assert "SELF-TEST PASS" in completed.stdout


def test_runtime_log_uses_per_user_local_app_data(tmp_path):
    env = _subprocess_env(tmp_path)
    completed = subprocess.run(
        [sys.executable, "-c", "import pourbaix_gui_R3; print(pourbaix_gui_R3.log_path)"],
        cwd=PROJECT_ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )

    expected = Path(env["LOCALAPPDATA"]) / "PourbaixGUI" / "logs" / "pourbaix_gui_R3_runtime.log"
    assert completed.returncode == 0, completed.stderr
    assert Path(completed.stdout.strip()) == expected
    assert expected.parent.is_dir()


def test_gui_smoke_constructs_processes_events_and_closes(tmp_path):
    completed = subprocess.run(
        [sys.executable, str(SCRIPT), "--gui-smoke"],
        cwd=PROJECT_ROOT,
        env=_subprocess_env(tmp_path),
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr
    assert "GUI-SMOKE PASS" in completed.stdout
