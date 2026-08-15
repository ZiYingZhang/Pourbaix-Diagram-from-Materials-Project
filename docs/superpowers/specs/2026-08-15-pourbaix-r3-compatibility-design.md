# Pourbaix GUI R3 Compatibility and Release Design

Date: 2026-08-15

## Objective

Restore source and packaged Windows operation after the `pymatgen` / `pymatgen-core` split, make the build reproducible, and prevent oxygen or hydrogen from being treated as closed composition dimensions in `PourbaixDiagram.comp_dict`.

## Confirmed platform and delivery

- Platform: Windows x64.
- Runtime: CPython 3.13.15, installed and managed by Python Install Manager 26.3.
- Development environment: `.venv-pourbaix-py313` inside the project.
- UI stack: existing PyQt5 application.
- Distribution: PyInstaller `onedir` folder plus ZIP archive.
- Online dependency: Materials Project API; users provide their own API key at runtime.

## Approaches considered

1. **Clean Python 3.13 environment and rebuild (selected).** Resolves the package split using a coherent current dependency set and produces a reproducible lock file.
2. **Repair the old `pourbaix_env` in place (rejected).** Its base interpreter no longer exists and it contains the incompatible `mp-api 0.44.0` stack.
3. **Ship a fake `pymatgen.core.entries` shim (rejected).** This would mask serialization incompatibility without proving that returned Materials Project objects remain scientifically and structurally compatible.

## Paths

- Runtime: managed by Python Install Manager; no hard-coded runtime path in source or spec.
- Virtual environment: `.venv-pourbaix-py313`.
- Tests: `tests/`.
- PyInstaller work directory: `_build/R3.0/`.
- Release directory: `_release/R3.0/pourbaix_gui_R3/`.
- Archive: `_release/R3.0/pourbaix_gui_R3-win64.zip`.
- Logs: `%LOCALAPPDATA%/PourbaixGUI/logs/pourbaix_gui_R3_runtime.log`.

## Dependency design

- Start from `mp-api==0.46.4` and resolve a coherent current set including `pymatgen`, `pymatgen-core`, `mpcontribs-client`, PyQt5, NumPy, pandas, Matplotlib, Shapely, openpyxl, certifi, pytest, and PyInstaller.
- Verify imports before accepting the resolved set, especially `pymatgen.core.entries` and `pymatgen.analysis.pourbaix_diagram`.
- Freeze the verified full environment to `requirements-lock-py313-win64.txt`.
- Future builds install from the lock file rather than unconstrained upgrades.

## Production changes

1. Add pure input parsing that validates element symbols, ranges, ratio counts, positive ratios, and excludes H/O from `comp_dict`.
2. Change the default single-metal example to `Ti` with ratio `1.0`.
3. Make sanitation retry run when the initial ion-reference path raises the targeted missing-field exception, not only when it returns an empty list.
4. Add `--self-test` to import the runtime-critical modules and exit without showing the GUI.
5. Move logs out of the executable directory into the per-user local application data directory.
6. Replace the absolute-path R2 spec with an environment-relative R3 spec and explicit collection of dynamically imported Materials Project/pymatgen modules and package data.
7. Add workspace VS Code configuration that points both the Python extension and Code Runner at `.venv-pourbaix-py313`.

## Scientific behavior contract

- H and O are open species in the Pourbaix formalism and must not be keys in `comp_dict`.
- Ratios describe only non-H/O elements and may be normalized by the established pymatgen behavior.
- pH remains dimensionless; potential remains volts versus SHE.
- Plot styling must not change boundary data exported to CSV/XLSX/TXT.
- The implementation continues to delegate thermodynamic construction to the pinned pymatgen release; no custom energy model is introduced.

## Error handling

- Invalid input is rejected before any network call and reported with an actionable field-level message.
- Targeted malformed ion-reference data triggers exactly one sanitation retry; unrelated exceptions preserve their original traceback in the local log.
- A failed new calculation must not leave an old figure exportable under new input metadata.
- No API key is written to logs, lock files, build manifests, or archives.

## Test-first implementation

1. A runtime compatibility test fails against the old environment because `pymatgen.core.entries` is absent.
2. Input contract tests fail until H/O exclusion and length/range validation exist.
3. Retry tests fail until the exception path performs exactly one sanitation retry.
4. Stale-result tests fail until failed calculations invalidate pending metadata safely.
5. Implement the minimum changes needed to pass each test before refactoring.

## Release verification

- Run focused and full tests in the new environment.
- Run source `--self-test` and a headless Qt construction smoke test.
- Run a real Materials Project Ti request when an API key is available.
- Build from clean R3 work/release directories without deleting the old R2 artifacts.
- Run packaged `--self-test`, inspect the package for `pymatgen/core/entries`, launch and close the real GUI, archive, extract to a fresh directory, and rerun packaged self-test.
- Record package entries, byte size, SHA-256, toolchain versions, test results, and external acceptance status in `release-manifest.json`.

## Excluded from this release

- Major UI redesign.
- Background worker/thread architecture.
- Offline Materials Project dataset.
- Automatic application updating.

## External acceptance

Testing on a separate clean Windows x64 machine without Python is required for final portable-package acceptance. Until executed against the final archive hash, this gate remains Pending.

