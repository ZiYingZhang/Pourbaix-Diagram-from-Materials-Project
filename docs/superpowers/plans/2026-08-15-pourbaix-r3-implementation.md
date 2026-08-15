# Pourbaix GUI R3 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Restore R2 into source control, upgrade it to a reproducible Python 3.13-compatible R3, build a verified Windows onedir ZIP, and publish source plus release evidence to GitHub.

**Architecture:** Preserve the R2 PyQt5 GUI while extracting pure input validation and API-entry retry behavior into testable modules. pymatgen remains the thermodynamic authority; PyInstaller packages the pinned environment, and a release script produces fresh smoke evidence and a manifest.

**Tech Stack:** CPython 3.13.15, PyQt5, mp-api 0.46.4, pymatgen/pymatgen-core, pandas, Matplotlib, Shapely, pytest, PyInstaller, PowerShell, GitHub CLI.

## Global constraints

- Windows x64; `.venv-pourbaix-py313`; PyInstaller onedir; archive `_release/R3.0/pourbaix_gui_R3-win64.zip`.
- H/O are open species and must not appear in `comp_dict`; ratios describe only non-H/O elements.
- Invalid input is rejected before network access; targeted malformed ion data receives exactly one sanitation retry.
- Failed calculations invalidate old figure metadata; styling does not alter exported boundaries.
- Logs use `%LOCALAPPDATA%/PourbaixGUI/logs`; secrets are excluded from logs, manifests, Git, and archives.
- Clean-machine acceptance remains Pending until run against the final ZIP hash.

---

### Task 1: Recover and preserve R2

**Files:** create `legacy/R2/pourbaix_gui_R2.py`, `legacy/R2/pourbaix_gui_R2.spec`, `legacy/R2/requirements.txt`, `legacy/R2/README.md`, `legacy/R2/USER_GUIDE.md`; create active `pourbaix_gui_R3.py` from the preserved R2 source.

- [x] Copy the byte-identical R2 source and documents from the located historical project.
- [x] Record SHA-256 values and the broken legacy-interpreter evidence in `docs/r2-recovery.md`.
- [x] Confirm the active R3 source initially matches the recovered R2 source, apart from its filename.
- [x] Commit the recovery as an independent historical checkpoint.

### Task 2: Establish the Python 3.13 dependency baseline

**Files:** create `requirements.in`, `requirements-dev.in`, `requirements-lock-py313-win64.txt`.

- [x] Create `.venv-pourbaix-py313` with the managed Python 3.13.15 executable.
- [x] Install `mp-api==0.46.4`, pymatgen, pymatgen-core, mpcontribs-client, PyQt5, NumPy, pandas, Matplotlib, Shapely, openpyxl, certifi, pytest, and PyInstaller.
- [x] Run an import probe for `pymatgen.core.entries`, `pymatgen.analysis.pourbaix_diagram`, `mp_api.client`, PyQt5, Shapely, pandas, and Matplotlib.
- [x] Freeze the complete resolved environment and verify a second import probe from the lock file metadata.

### Task 3: Implement the scientific input contract test-first

**Files:** create `pourbaix_core.py`; create `tests/test_input_contract.py`; modify `pourbaix_gui_R3.py`.

**Interface:** `parse_inputs(elements_text, ratios_text, ph_text, potential_text) -> PourbaixInputs`, where `PourbaixInputs.elements` contains the validated API chemical system and `PourbaixInputs.comp_dict` contains only non-H/O elements.

- [x] Write table-driven tests proving valid Ti, Ti/O, and multi-metal parsing plus rejection of invalid symbols, duplicate elements, ratio-count mismatch, non-positive/non-finite ratios, malformed ranges, and unordered ranges.
- [x] Run the focused tests and confirm they fail because `pourbaix_core` is absent.
- [x] Implement the immutable parsed-input value object and minimal validation.
- [x] Run the focused tests and confirm they pass.
- [x] Wire plot, boundary export, and species listing to validate before resolving the API key or invoking network code; set defaults to `Ti` and `1.0`.

### Task 4: Implement targeted sanitation retry and stale-state invalidation test-first

**Files:** modify `pourbaix_core.py`, `pourbaix_gui_R3.py`; create `tests/test_entry_fetch.py`, `tests/test_gui_state.py`.

**Interfaces:** `fetch_pourbaix_entries(mpr, elements) -> FetchResult(entries, used_sanitation_retry)` and `PourbaixApp._invalidate_result() -> None`.

- [x] Write controlled-client tests for first-call success, empty-result retry, targeted missing-ion-field exception retry, unrelated exception propagation, and exactly one retry.
- [x] Run and observe the expected failures, then implement the smallest fetch helper using a patched ion-reference selector only for the retry.
- [x] Write a headless Qt test proving a failed new plot clears the prior figure/elements/composition before export can use them.
- [x] Run and observe the failure, implement `_invalidate_result`, then rerun focused and full tests.

### Task 5: Add runtime self-test, local logging, and reproducible packaging

**Files:** modify `pourbaix_gui_R3.py`; create `pourbaix_gui_R3.spec`, `.vscode/settings.json`, `scripts/build_release.ps1`, `tests/test_self_test.py`, `tests/test_release_safety.py`.

- [x] Write a subprocess test requiring `--self-test` to exit 0 without constructing a GUI and a log-path test using a temporary `LOCALAPPDATA`.
- [x] Observe failures, then add `run_self_test()` and user-local log directory initialization without printing secrets.
- [x] Replace the absolute R2 spec with environment-relative module/data collection and include package metadata, docs, and licenses.
- [ ] Add PowerShell release orchestration that resolves and validates `_build/R3.0` and `_release/R3.0` before cleaning, builds onedir, runs packaged self-test, checks `pymatgen/core/entries`, archives, extracts to a fresh staging folder, reruns self-test, and writes `release-manifest.json`.
- [x] Add VS Code interpreter and Code Runner settings targeting `.venv-pourbaix-py313`.

### Task 6: Verify, document, and publish

**Files:** modify `README.md`, `USER_GUIDE.md`, `docs/acceptance-checklist.md`, `PROJECT_MEMORY.md`; create `CHANGELOG.md`; generate `_release/R3.0/release-manifest.json`.

- [ ] Run focused tests, full pytest, source self-test, and headless Qt construction smoke with fresh output.
- [ ] If an API key is present, run the Ti live request without printing the key; otherwise record the gate as Skipped with reason.
- [ ] Build from validated clean staging, run packaged and extracted smokes, inspect secrets/package contents, and record ZIP bytes, entries, SHA-256, toolchain, timestamps, and external Pending gates.
- [ ] Update user-facing docs for Ti/1.0 inputs, log location, release download, and external-acceptance status.
- [ ] Inspect `git status` and diff, stage only intended source/docs/tests/metadata, commit, push the `codex/r3-compatibility-release` branch, and open a draft PR to `main`.
- [ ] Create GitHub Release `R3.0` for the reviewed commit/tag and upload the ZIP plus `release-manifest.json`; do not upload any API key or log.
