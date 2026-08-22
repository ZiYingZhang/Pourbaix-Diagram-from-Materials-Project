# Pourbaix Studio R4 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deliver a portable Windows x64 PySide6/Qt6 Pourbaix Studio R4 that preserves every R2.8 workflow while adding composition-first system entry, unlimited interest-region fills, bilingual UI, snapshot-safe export, and optional secure API-key storage.

**Architecture:** Keep R3 untouched as the compatibility baseline and introduce an R4 package with pure domain, credentials, Materials Project, calculation, session, plotting, export, translation, and Qt UI boundaries. One immutable calculation snapshot is the sole source for diagram display, available regions, and exports; presentation preferences and locale can never change its boundary data.

**Tech Stack:** CPython 3.13 (exact lock validated first), PySide6/Qt6, mp-api 0.46.4, pymatgen/pymatgen-core, Matplotlib, Shapely, pandas/openpyxl, keyring (Windows Credential Manager), pytest, PyInstaller, PowerShell.

**Spec:** [R4 PySide6 design](../specs/2026-08-22-pourbaix-r4-pyside6-design.md)

## Global constraints

- Retain `pourbaix_gui_R3.py` and the `legacy/R2` tree unchanged; R4 is introduced through a separate entry point, package, tests, spec, and build artifacts until release acceptance is complete.
- R4 is an equilibrium Pourbaix workbench only. Do not introduce metastable calculations, energy models, offline databases, automatic updates, or custom thermodynamic rules.
- H/O are open species: they may be selected in the chemical system but never have ratio controls and never occur in `PourbaixDiagram.comp_dict`. Fe-Ni without selected O remains a valid aqueous query.
- Validate formula, selected elements, ratios, pH, and potential before resolving credentials or touching the network. Invalid state must leave the last result non-exportable.
- Use exactly the established one targeted malformed-ion sanitation retry; do not hide arbitrary Materials Project failures behind retries.
- Treat the successful calculation as immutable. Appearance, interest regions, language, layout, and export options consume it but cannot mutate its boundaries or force a refetch.
- API keys are secrets: no logging, QSettings storage, source-control writes, archive manifests, screenshots, translation files, or scientific exports. New persistent storage is Windows Credential Manager only; the legacy text file is read-compatible and migrates only after explicit confirmation.
- Keep all R2.8 controls: API direct link, pH/potential ranges, fonts, labels/backgrounds, axes/ticks/spines/line widths, water-line colors, available labels, entry cache/clear cache/diagnostics, data and image exports, DPI, and transparency. The four fixed fills become unlimited interest-region rows.
- Application-owned text, validation messages, diagnostics, and dialogs are bilingual at runtime; formulas, symbols, units, species labels, user-entered axis labels, and exported column headers remain stable. Persist only the language/layout/appearance preferences with QSettings.
- Build only from a fresh locked Windows x64 virtual environment. Release remains PyInstaller `onedir` plus ZIP unless packaging validation documents a compatible change.

## Planned file structure

```text
pourbaix_studio_R4.py                 # R4 CLI, GUI launcher, source self-tests
pourbaix_studio_R4.spec               # PyInstaller onedir definition
pourbaix_r4/
  __init__.py
  domain.py                            # formula/input/appearance validation
  models.py                            # immutable cross-layer value objects
  credentials.py                       # transient/keyring/env/legacy resolution
  materials_project.py                 # entry cache and sanitation retry
  calculation.py                       # pymatgen diagram -> immutable snapshot
  session.py                           # result lifecycle and stale/export state
  plotting.py                          # Matplotlib rendering from snapshot only
  exporting.py                         # data/figure writes and verification
  i18n.py                              # English/Chinese catalog and preference
  ui/
    __init__.py
    composition_panel.py               # formula/tags/periodic table/conditions
    interest_regions.py                # dynamic region model/editor
    appearance_panel.py                # retained R2.8 display controls
    api_dialog.py                      # API key/settings/migration dialogs
    main_window.py                     # docks, workspace, toolbar, orchestration
tests/r4/
  conftest.py
  test_domain.py
  test_models_session.py
  test_credentials.py
  test_materials_project.py
  test_calculation.py
  test_plotting_exporting.py
  test_i18n.py
  test_ui_composition.py
  test_ui_workbench.py
  test_r2_compatibility.py
  test_release_r4.py
scripts/build_release_r4.ps1
docs/r4-migration.md
docs/r4-release-validation.md
```

---

### Task 1: Establish the isolated Qt6 runtime and R4 test harness

**Files:** modify `requirements.in`, `requirements-dev.in`; create `requirements-lock-py313-win64-r4.txt`, `tests/r4/conftest.py`, `tests/r4/test_release_r4.py`, `pourbaix_studio_R4.py`.

- [x] Add `PySide6` and `keyring` as explicit runtime requirements, pin the resolved Windows x64 versions, and retain existing R3 dependencies. Create or reuse the Python 3.13 virtual environment only after recording its exact patch version.
- [x] Add an R4 headless Qt fixture using `QT_QPA_PLATFORM=offscreen`, `MPLBACKEND=Agg`, and a temporary `LOCALAPPDATA`; its `qapplication` fixture must import `PySide6.QtWidgets.QApplication`, not PyQt5.
- [x] Write the failing runtime smoke test:

  ```python
  def test_r4_self_test_runs_without_constructing_a_window(tmp_path):
      completed = subprocess.run(
          [sys.executable, "pourbaix_studio_R4.py", "--self-test"],
          cwd=REPO_ROOT, text=True, capture_output=True, check=False,
          env={**os.environ, "LOCALAPPDATA": str(tmp_path)},
      )
      assert completed.returncode == 0, completed.stderr
      assert "R4 self-test: OK" in completed.stdout
  ```

- [x] Run `pytest -q tests/r4/test_release_r4.py` and confirm it fails because the R4 launcher is absent.
- [x] Add a minimal `run_self_test()` and `main(argv)` to `pourbaix_studio_R4.py`; test only imports of the R4 package, PySide6, Matplotlib, Shapely, pandas, keyring, and the existing Materials Project stack. Do not construct `QApplication` for `--self-test`.
- [x] Rerun the focused test and then `pytest -q`; record the lockfile command and versions in the lockfile header.
- [x] Commit: `chore: establish R4 PySide6 runtime baseline`.

### Task 2: Define immutable R4 models and the composition/input contract

**Files:** create `pourbaix_r4/__init__.py`, `pourbaix_r4/models.py`, `pourbaix_r4/domain.py`, `tests/r4/test_domain.py`, `tests/r4/test_models_session.py`.

**Interfaces:**

```python
parse_formula(formula: str) -> tuple[tuple[str, ...], dict[str, float]]
parse_calculation_input(
    selected_elements: Sequence[str], ratios: Mapping[str, str | float],
    ph_range: tuple[str | float, str | float], potential_range: tuple[str | float, str | float],
) -> CalculationInput
import_legacy_element_ratio_text(elements_text: str, ratios_text: str) -> tuple[tuple[str, ...], dict[str, float]]
```

- [x] Write table-driven failing tests for `Sb2Se3`, `BiVO4`, `FeNi`, `TiO2`, repeated elements, invalid grammar/symbols, duplicate tags, `H/O`-only input, H/O excluded from ratios and `comp_dict`, `2:3` and decimal ratios, ratio count mismatch, non-positive/non-finite values, and unordered/non-finite pH/potential ranges.
- [x] Write model tests requiring frozen dataclasses: `CalculationInput`, `InterestRegion`, `AppearanceSettings`, `BoundaryRecord`, and `ResultSnapshot`. `ResultSnapshot` must carry the validated input, stable-domain labels, clipped boundaries, and result metadata, but no live QWidget.
- [x] Run `pytest -q tests/r4/test_domain.py tests/r4/test_models_session.py` and confirm import failures.
- [x] Implement formula tokenization with `pymatgen.core.Composition` only as a parser/validator, preserving first-occurrence element order. Implement domain validation with no Qt, network, file-dialog, or credential import. A formula's stoichiometry supplies editable initial closed-element ratios; it does not normalize or alter subsequent user ratios.
- [x] Implement `import_legacy_element_ratio_text` so prior comma-separated R2.8/R3 input is accepted, including optional H/O. Ensure `CalculationInput.comp_dict` returns non-H/O values only.
- [x] Rerun focused tests; add regression assertions that Fe-Ni `1:1` is valid with no O and that changing appearance fields cannot be represented in `CalculationInput`.
- [x] Commit: `feat: add R4 composition and input domain contract`.

### Task 3: Implement secure, compatible API-key resolution

**Files:** create `pourbaix_r4/credentials.py`, `tests/r4/test_credentials.py`; modify `pourbaix_studio_R4.py`.

**Interfaces:**

```python
class CredentialStore(Protocol):
    def get(self) -> str | None: ...
    def set(self, api_key: str) -> None: ...
    def delete(self) -> None: ...

resolve_api_key(current_value: str | None, legacy_path: Path) -> ResolvedCredential
detect_legacy_key(legacy_path: Path) -> str | None
```

- [x] Write failing tests using a fake `CredentialStore` for precedence: current UI entry, credential manager, `MP_API_KEY`, `MAPI_KEY`, `PMG_MAPI_KEY`, then `mp_api_key.txt`. Test empty/whitespace values, non-disclosure in `repr`, and source labels without the key.
- [x] Add tests that a legacy key is read but never modified; only `migrate_legacy_key(store, legacy_path)` writes to the store and leaves the legacy file present. Add tests for remember/replace/forget and storage-backend failure.
- [x] Run `pytest -q tests/r4/test_credentials.py` and observe failure.
- [x] Implement a `keyring`-backed `WindowsCredentialStore` with a stable service name and current-user key name. Keep imports and errors testable; use QSettings for no secret. Give callers typed `CredentialError` messages safe for dialogs/logging.
- [x] Add `api_key_url()` returning the preserved direct link `https://next-gen.materialsproject.org/api` and `api_docs_url()` for the official documentation fallback. The launcher self-test must verify constants only and never resolve a real key.
- [x] Rerun focused and complete tests. Inspect test logs to confirm no fake key appears.
- [x] Commit: `feat: add secure R4 API credential handling`.

### Task 4: Move cached Materials Project retrieval behind a tested service

**Files:** create `pourbaix_r4/materials_project.py`, `tests/r4/test_materials_project.py`; modify `pourbaix_r4/models.py`.

**Interfaces:**

```python
class EntryProvider(Protocol):
    def fetch(self, elements: Sequence[str], api_key: str) -> FetchResult: ...

class CachedEntryService:
    def fetch(self, elements: Sequence[str], api_key: str) -> FetchResult: ...
    def clear(self) -> None: ...
    def diagnostics(self) -> CacheDiagnostics: ...
```

- [ ] Port the R3 controlled-client tests first: normal first-call success, cache hit, five-minute expiry, empty/malformed known-ion targeted retry, unrelated error propagation, and exactly one retry.
- [ ] Add failing tests proving cache keys include the canonical selected chemical system but never the API key, and that diagnostic objects expose entry count/cache age/retry state but not secret values.
- [ ] Run `pytest -q tests/r4/test_materials_project.py` and observe expected import failures.
- [ ] Implement the cache and reuse the proven R3 sanitation logic without copying GUI state. Make the clock injectable for expiry tests and write sanitized traceback detail only through the app logger.
- [ ] Add a test that `clear()` removes entries and metadata without changing a `ResultSnapshot` already held by the session.
- [ ] Rerun focused tests and the full suite.
- [ ] Commit: `refactor: isolate R4 Materials Project entry service`.

### Task 5: Build snapshot-safe calculation, clipping, session lifecycle, and data export

**Files:** create `pourbaix_r4/calculation.py`, `pourbaix_r4/session.py`, `pourbaix_r4/exporting.py`, `tests/r4/test_calculation.py`, `tests/r4/test_plotting_exporting.py`; modify `pourbaix_r4/models.py`.

**Interfaces:**

```python
calculate_snapshot(inputs: CalculationInput, entries: Sequence[object]) -> ResultSnapshot
class CalculationSession:
    def replace_success(self, snapshot: ResultSnapshot) -> None: ...
    def invalidate_for_input_change(self) -> None: ...
    def replace_failure(self, error: Exception) -> None: ...
    @property
    def exportable_snapshot(self) -> ResultSnapshot | None: ...
export_boundaries(snapshot: ResultSnapshot, path: Path, file_format: Literal["csv", "xlsx", "txt"]) -> Path
```

- [ ] Write failing calculation tests with a small deterministic stub diagram/entries: labels and vertices are constructed once, polygons are clipped to the requested pH/potential rectangle, and `comp_dict` excludes H/O.
- [ ] Write session tests: successful replacement enables exports; formula/ratio/range change marks result stale; failed calculation clears diagram metadata/exportability; appearance and language changes preserve a valid snapshot byte-for-byte.
- [ ] Write export tests that create CSV/XLSX/TXT, read each back, and require fixed English headers such as `domain_label`, `pH`, and `potential_V_SHE`. Assert no fetch function is called by an export.
- [ ] Run the three focused test modules and confirm failure.
- [ ] Port only the mature R3/pymatgen diagram construction and Shapely clipping logic into `calculate_snapshot`. Store plain immutable boundary records for export and a non-exported diagram/rendering payload needed by plotting. Do not derive data from Matplotlib artists.
- [ ] Implement atomic temporary-file write/replace where the format permits, non-empty output verification, and user-safe `ExportError` failures. Preserve snapshot input and generated-at metadata in a clearly separated, non-secret metadata sheet/section.
- [ ] Rerun focused tests, then all R4 tests. Manually compare a Ti/O boundary export against the R3 output structure without freezing remote phase names.
- [ ] Commit: `feat: add immutable R4 calculation snapshots and data export`.

### Task 6: Render snapshots with all retained R2.8 appearance settings

**Files:** create `pourbaix_r4/plotting.py`, modify `pourbaix_r4/exporting.py`, `pourbaix_r4/models.py`; modify `tests/r4/test_plotting_exporting.py`, create `tests/r4/test_r2_compatibility.py`.

**Interfaces:**

```python
render_snapshot(snapshot: ResultSnapshot, appearance: AppearanceSettings, regions: Sequence[InterestRegion]) -> Figure
export_figure(figure: Figure, path: Path, image_format: Literal["png", "jpeg", "tiff", "svg"], dpi: int, transparent: bool) -> Path
```

- [ ] Extend failing plotting tests to assert that pH/potential bounds, labels visibility, label font/size/background/color/alpha, axis/tick font and sizes, axis labels/sizes, spine/solid/stability widths, major/minor tick settings, hydrogen/oxygen water-line colors, and interest-region colors/opacity are applied to a figure.
- [ ] Add tests for unlimited interest regions: unknown labels are rejected, duplicate selections stay explicit rather than silently rewritten, and each valid selected label is filled from the same clipped snapshot geometry.
- [ ] Add failing image-export tests for PNG/JPEG/TIFF/SVG, requested DPI for raster output, transparent background, empty output detection, and no recalculation/refetch during export.
- [ ] Run `pytest -q tests/r4/test_plotting_exporting.py tests/r4/test_r2_compatibility.py` and observe failure.
- [ ] Implement pure snapshot rendering. Use only `ResultSnapshot.boundaries` for fills and line geometry; `AppearanceSettings` is display-only. Preserve the R2.8 water stability line rendering and non-overlapping label strategy as far as the pinned Matplotlib/pymatgen APIs permit.
- [ ] Implement image write verification. For SVG, validate a non-empty XML text output; for raster formats, reopen with Pillow only if already present in the resolved environment, otherwise validate file presence/size and document the toolchain limitation.
- [ ] Rerun focused tests and include a visual smoke image in a temporary test directory; do not commit generated figures.
- [ ] Commit: `feat: restore R2 plotting controls in R4 renderer`.

### Task 7: Add runtime bilingual catalog and non-secret UI preferences

**Files:** create `pourbaix_r4/i18n.py`, `tests/r4/test_i18n.py`; modify `pourbaix_r4/models.py`.

**Interfaces:**

```python
class TranslationCatalog:
    def text(self, key: str, language: Literal["en", "zh_CN"], **values: object) -> str: ...
class PreferenceStore:
    def language(self) -> Literal["en", "zh_CN"]: ...
    def set_language(self, language: Literal["en", "zh_CN"]) -> None: ...
```

- [ ] Write failing tests that require the English and Chinese dictionaries to have identical key sets; cover representative toolbar/actions, all validation errors, credential messages, diagnostics, export successes/failures, and all R2.8 control labels.
- [ ] Test missing translation keys, unsupported languages, interpolation without secret values, and QSettings persistence using an isolated organization/application namespace.
- [ ] Run `pytest -q tests/r4/test_i18n.py` and observe failure.
- [ ] Implement a catalog with stable symbolic keys (not source text) and a thin QSettings-backed preference store. Catalog values must never interpolate raw API keys, credentials, or stack traces.
- [ ] Add a `retranslate` protocol used by Qt widgets so they update immediately while leaving composition, session snapshot, cache, interest rows, and export options untouched.
- [ ] Rerun focused tests and add a test that language change leaves `ResultSnapshot.boundaries` equal before/after.
- [ ] Commit: `feat: add bilingual R4 translation and preference layer`.

### Task 8: Build the PySide6 composition and API surfaces test-first

**Files:** create `pourbaix_r4/ui/__init__.py`, `pourbaix_r4/ui/composition_panel.py`, `pourbaix_r4/ui/api_dialog.py`, `tests/r4/test_ui_composition.py`; modify `pourbaix_r4/i18n.py`.

**Interfaces:**

```python
class CompositionPanel(QWidget):
    calculation_requested = Signal(CalculationInput)
    input_changed = Signal()
    def apply_formula(self, formula: str) -> None: ...
    def selected_elements(self) -> tuple[str, ...]: ...

class ApiSettingsDialog(QDialog):
    credentials_changed = Signal()
```

- [ ] Write failing headless Qt tests for formula quick-fill, element type-ahead/tags, periodic-table selection, adding/removing a closed element, open H/O notice, dynamically regenerated ratios, legacy comma-text import, pH/potential editors, and no calculate signal when field validation fails.
- [ ] Add dialog tests for masked key input, show/hide behavior, direct key link, documentation link, connection-test callback error display, remember/replace/forget, and explicit legacy-file migration prompt. Fake browser/credential/network dependencies; tests must not use a real API key.
- [ ] Implement a `QDialog` periodic-table selector with every official element symbol available and searchable, rather than a hand-maintained partial list. Keep H/O checkable but omit them from ratio rows.
- [ ] Implement the composition panel with accessible object names, keyboard-focus order, and layout constraints usable at 100%, 125%, and 150% scaling. Keep validation text in `TranslationCatalog`.
- [ ] Rerun UI tests with `pytest -q tests/r4/test_ui_composition.py`; then run a source GUI smoke that creates and closes the panel without a network call.
- [ ] Commit: `feat: add R4 composition and API Qt controls`.

### Task 9: Build dynamic interest regions, appearance controls, and workbench layout

**Files:** create `pourbaix_r4/ui/interest_regions.py`, `pourbaix_r4/ui/appearance_panel.py`, `pourbaix_r4/ui/main_window.py`, `tests/r4/test_ui_workbench.py`; modify `pourbaix_studio_R4.py`.

- [ ] Write failing UI tests requiring a `QMainWindow` with left “System and conditions” dock, central Diagram/Available regions/Boundary data tabs, right interest-region/appearance dock, and toolbar actions for API settings, language, exports, diagnostics, and clear cache.
- [ ] Write tests for adding/removing an arbitrary number of interest rows, region selector refresh from a successful snapshot, invalid-region feedback, visibility/color/opacity persistence, and redraw without recalculation. Test all R2.8 appearance controls are exposed in named collapsible groups.
- [ ] Test state transitions: changed calculation input disables export and marks the diagram stale; calculation failure clears old visual/result availability; successful calculation refreshes regions/boundary table and enables exports. Use fake calculation services and a deterministic snapshot.
- [ ] Implement interest-region rows as a `QAbstractListModel` or equivalent testable model rather than mutable widget-only state. Build the appearance dock around `AppearanceSettings`; do not place numerical science logic in widgets.
- [ ] Implement `PourbaixStudioMainWindow` orchestration: validate -> resolve credentials -> fetch -> calculate -> session replace -> render, with progress/error handling and local sanitized logging. Start synchronous only if live responsiveness is acceptable; if not, introduce a `QThreadPool` worker with the same session state transitions and add cancellation/race tests before enabling it.
- [ ] Add launcher `--gui-smoke` to construct, switch language once, resize to representative sizes, then close without opening the API/network.
- [ ] Rerun `pytest -q tests/r4/test_ui_workbench.py` and source `--gui-smoke` under offscreen Qt.
- [ ] Commit: `feat: add bilingual R4 Qt workbench`.

### Task 10: Complete R2.8 workflow parity, diagnostics, and live acceptance gates

**Files:** modify `tests/r4/test_r2_compatibility.py`, `tests/r4/test_release_r4.py`, `pourbaix_r4/materials_project.py`, `pourbaix_r4/ui/main_window.py`, `pourbaix_studio_R4.py`; create `docs/r4-migration.md`.

- [ ] Convert the R4 compatibility matrix into executable tests that enumerate every R2.8 control and workflow, including: direct API link; pH/potential; labels/backgrounds; fonts; axis/tick/spine/line settings; water-line colors; available labels; cache/clear cache; diagnostics; four legacy fill values imported as interest regions; CSV/XLSX/TXT; PNG/JPEG/TIFF/SVG; DPI; transparency.
- [ ] Add diagnostics tests for backend/dependency versions, cache state, entry count, sanitation retry, session freshness, and credential source name without credential value. Verify full tracebacks go only to local logs, while user dialogs remain translated and concise.
- [ ] Add regression tests that styling/locale changes do not change boundary export bytes for a fixed snapshot, and that a stale/failed result cannot be exported through any toolbar/menu shortcut.
- [ ] Run all R4 tests and fix only behavioral gaps revealed by the compatibility suite. Do not alter R3 code to make an R4 test pass.
- [ ] Add `docs/r4-migration.md` explaining R3 coexistence, R2.8-to-R4 control mapping, interest-region migration, API-key sources/migration, known R4 scope exclusions, and rollback route to R3.
- [ ] When a valid key is supplied by the user, run guarded live acceptance: Ti-O (1), Sb-Se (2:3), and Fe-Ni (1:1, no O). Record only pass/fail, response timing, source revision, and snapshot consistency—never the key or mutable remote phase names. Mark unavailable-key checks `Skipped`, not `Passed`.
- [ ] Commit: `test: verify R4 R2.8 workflow parity`.

### Task 11: Package, inspect, archive, and document R4 release evidence

**Files:** create `pourbaix_studio_R4.spec`, `scripts/build_release_r4.ps1`, `docs/r4-release-validation.md`; modify `README.md`, `USER_GUIDE.md`, `CHANGELOG.md`, `docs/acceptance-checklist.md`, `PROJECT_MEMORY.md`, `tests/r4/test_release_r4.py`.

- [ ] Write failing release-safety tests that inspect the spec/script for R4 entry point, PySide6 collection, Matplotlib Qt backend, pymatgen/mp-api/mpcontribs/Shapely/keyring dependencies, no absolute development paths, and no key-file-writing code.
- [ ] Add subprocess tests for source and packaged `--self-test`/`--gui-smoke`, then run them first to identify missing hidden imports/data files.
- [ ] Implement `pourbaix_studio_R4.spec` as environment-relative `onedir` packaging. Include package metadata/licenses and only necessary non-code assets; do not bundle a user credential, `mp_api_key.txt`, local logs, or generated diagrams.
- [ ] Implement `scripts/build_release_r4.ps1`: validate clean locked environment; build to `_build/R4.0`; run packaged self-test/gui smoke; forbidden-secret scan; archive `_release/R4.0/pourbaix_studio_R4-win64.zip`; extract to a fresh staging directory; rerun smoke; and write `release-manifest.json` containing revision, lock versions, tests, smoke exits, archive bytes/hash/entries, scan result, and Pending external gates.
- [ ] Run the full suite, source smokes, fresh package build, package/extracted smokes, archive inspection, and manifest validation. Manually verify English/Chinese switching, controls, API link, export, and dock usability at 100%, 125%, and 150% Windows scaling.
- [ ] Update README/user guide/changelog/acceptance checklist/project memory with the exact R4 launch and release paths, API-key security behavior, all validated evidence, and clearly labelled Pending clean-machine/non-admin/live-MP gates.
- [ ] Inspect `git status` and staged diff; commit only intended R4 source, tests, docs, requirements, and packaging changes: `release: prepare Pourbaix Studio R4 evidence`.

## Final verification checklist

- [ ] `pytest -q` succeeds in the locked R4 environment, including existing R3 tests.
- [ ] `python pourbaix_studio_R4.py --self-test` and `--gui-smoke` succeed without a network request or GUI display server.
- [ ] R3 source and preserved R2 source remain byte/content unchanged except explicitly documented non-source metadata changes.
- [ ] Domain, credentials, cache/retry, session invalidation, snapshot exports, plots, bilingual retranslation, UI dynamic rows, and R2.8 parity tests have fresh green evidence.
- [ ] The release ZIP is created from a clean locked environment, scans clean for secrets, extracts, and passes both smoke modes.
- [ ] With user-provided credentials, the three live systems complete and produce internally consistent snapshot/export results; otherwise those gates are accurately marked Pending/Skipped.
- [ ] Clean-machine, non-administrator, display-scaling, and final live-server acceptance are recorded against the final ZIP SHA-256 before a public release is claimed.
