import os
from pathlib import Path
import subprocess


REPO_ROOT = Path(__file__).resolve().parents[2]
SPEC = REPO_ROOT / "pourbaix_studio_R4.spec"
BUILD_SCRIPT = REPO_ROOT / "scripts" / "build_release_r4.ps1"
RELEASE_HELPERS = REPO_ROOT / "scripts" / "release_helpers.psm1"


def _validate_paths(build_root: str, release_root: str):
    return subprocess.run(
        [
            "powershell.exe",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(BUILD_SCRIPT),
            "-BuildRoot",
            build_root,
            "-ReleaseRoot",
            release_root,
            "-ValidatePathsOnly",
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )


def test_r4_spec_is_environment_relative_and_targets_r4_entrypoint():
    source = SPEC.read_text(encoding="utf-8")

    assert '"pourbaix_studio_R4.py"' in source
    assert 'name="PourbaixStudioR4"' in source
    assert "E:/" not in source
    assert "E:\\" not in source


def test_r4_spec_embeds_windows_and_runtime_icon_assets():
    source = SPEC.read_text(encoding="utf-8")

    assert '"assets", "pourbaix-studio-r4.png"' in source
    assert 'icon=os.path.join(project_root, "assets", "pourbaix-studio-r4.ico")' in source


def test_r4_release_script_accepts_only_dedicated_project_staging_paths():
    accepted = _validate_paths("_build/R4.0-test", "_release/R4.0-test")
    rejected_root = _validate_paths(".", "_release/R4.0-test")
    rejected_outside = _validate_paths("../outside", "_release/R4.0-test")

    assert accepted.returncode == 0, accepted.stderr
    assert "PATH-VALIDATION PASS" in accepted.stdout
    assert rejected_root.returncode != 0
    assert "Refusing unsafe staging path" in (rejected_root.stdout + rejected_root.stderr)
    assert rejected_outside.returncode != 0
    assert "Refusing unsafe staging path" in (rejected_outside.stdout + rejected_outside.stderr)


def test_r4_release_tests_use_a_build_local_temporary_directory():
    source = BUILD_SCRIPT.read_text(encoding="utf-8")

    assert '$env:TEMP = Join-Path $ResolvedBuildRoot "temp"' in source
    assert '$env:TMP = $env:TEMP' in source


def test_r4_release_runs_only_the_r4_release_gate():
    source = BUILD_SCRIPT.read_text(encoding="utf-8")

    assert '& $Python -m pytest -q "tests/r4"' in source


def test_release_path_sanitizer_removes_external_icu_but_keeps_system_icu(tmp_path):
    fake_system_root = tmp_path / "Windows"
    system_bin = fake_system_root / "System32"
    external_bin = tmp_path / "external-poppler"
    ordinary_bin = tmp_path / "ordinary"
    for directory in (system_bin, external_bin, ordinary_bin):
        directory.mkdir(parents=True)
    (system_bin / "icuuc.dll").touch()
    (external_bin / "icuuc.dll").touch()
    candidate_path = os.pathsep.join(map(str, (external_bin, system_bin, ordinary_bin)))
    environment = os.environ.copy()
    environment["R4_TEST_PATH"] = candidate_path
    environment["R4_TEST_SYSTEM_ROOT"] = str(fake_system_root)

    completed = subprocess.run(
        [
            "powershell.exe",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-Command",
            f"Import-Module '{RELEASE_HELPERS}' -Force; "
            "Remove-IncompatibleIcuDirectoriesFromPath "
            "-PathValue $env:R4_TEST_PATH -SystemRootPath $env:R4_TEST_SYSTEM_ROOT",
        ],
        cwd=REPO_ROOT,
        env=environment,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr
    sanitized_entries = completed.stdout.strip().split(os.pathsep)
    assert str(external_bin) not in sanitized_entries
    assert str(system_bin) in sanitized_entries
    assert str(ordinary_bin) in sanitized_entries


def test_release_instructions_name_the_r4_source_and_portable_executable():
    readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
    guide = (REPO_ROOT / "USER_GUIDE.md").read_text(encoding="utf-8")

    assert "pourbaix_studio_R4.py" in readme
    assert "build_release_r4.ps1" in readme
    assert "PourbaixStudioR4.exe" in guide
    assert "_internal" in guide
