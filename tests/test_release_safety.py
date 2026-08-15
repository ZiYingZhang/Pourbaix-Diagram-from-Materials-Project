from pathlib import Path
import subprocess


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

