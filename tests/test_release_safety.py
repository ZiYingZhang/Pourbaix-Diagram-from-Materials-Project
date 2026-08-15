from pathlib import Path
import subprocess
import sys
import time


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = PROJECT_ROOT / "scripts" / "build_release.ps1"


def _run_release_validation(build_root, release_root):
    return subprocess.run(
        [
            "powershell.exe",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(SCRIPT),
            "-BuildRoot",
            str(build_root),
            "-ReleaseRoot",
            str(release_root),
            "-ValidatePathsOnly",
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )


def test_release_script_accepts_dedicated_project_staging_directories():
    completed = _run_release_validation("_build/R3.0-test", "_release/R3.0-test")

    assert completed.returncode == 0, completed.stderr
    assert "PATH-VALIDATION PASS" in completed.stdout


def test_release_script_rejects_project_root_as_recursive_cleanup_target():
    completed = _run_release_validation(".", "_release/R3.0-test")

    assert completed.returncode != 0
    assert "Refusing unsafe staging path" in (completed.stdout + completed.stderr)


def test_release_script_rejects_paths_outside_the_project():
    completed = _run_release_validation("../outside", "_release/R3.0-test")

    assert completed.returncode != 0
    assert "Refusing unsafe staging path" in (completed.stdout + completed.stderr)


def test_gui_process_helper_waits_for_windowed_executable_to_finish(tmp_path):
    worker = tmp_path / "delayed_marker.py"
    marker = tmp_path / "finished.txt"
    worker.write_text(
        "import pathlib, sys, time\ntime.sleep(0.5)\npathlib.Path(sys.argv[1]).write_text('done')\n",
        encoding="utf-8",
    )
    pythonw = Path(sys.executable).with_name("pythonw.exe")
    module = PROJECT_ROOT / "scripts" / "release_helpers.psm1"
    command = (
        f"Import-Module '{module}'; "
        f"Invoke-CheckedGuiProcess -FilePath '{pythonw}' -ArgumentList @('{worker}', '{marker}'); "
        f"if (-not (Test-Path -LiteralPath '{marker}')) {{ throw 'helper returned before GUI process completed' }}"
    )

    started = time.monotonic()
    completed = subprocess.run(
        [
            "powershell.exe",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-Command",
            command,
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr
    assert time.monotonic() - started >= 0.5
    assert marker.read_text(encoding="utf-8") == "done"
