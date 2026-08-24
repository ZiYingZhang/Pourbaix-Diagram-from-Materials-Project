import json
from pathlib import Path

from pourbaix_r4.paths import application_base_dir, legacy_api_key_path


REPO_ROOT = Path(__file__).resolve().parents[2]


def test_source_application_base_is_independent_of_current_working_directory(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    assert application_base_dir() == REPO_ROOT
    assert legacy_api_key_path() == REPO_ROOT / "mp_api_key.txt"


def test_vscode_interpreter_uses_workspace_relative_path():
    settings = json.loads((REPO_ROOT / ".vscode" / "settings.json").read_text(encoding="utf-8"))

    assert settings["python.defaultInterpreterPath"].startswith("${workspaceFolder}")
    assert "E:\\" not in settings["python.defaultInterpreterPath"]
    assert "${workspaceFolder}" in settings["code-runner.executorMap"]["python"]
