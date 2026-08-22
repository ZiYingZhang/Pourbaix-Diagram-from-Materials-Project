import os
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "pourbaix_studio_R4.py"


def test_r4_self_test_runs_without_constructing_a_window(tmp_path):
    completed = subprocess.run(
        [sys.executable, str(SCRIPT), "--self-test"],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
        env={
            **os.environ,
            "LOCALAPPDATA": str(tmp_path / "local-app-data"),
            "QT_QPA_PLATFORM": "offscreen",
        },
    )

    assert completed.returncode == 0, completed.stderr
    assert "R4 self-test: OK" in completed.stdout
