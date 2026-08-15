# Pourbaix GUI R3.0

Pourbaix GUI is a Windows desktop application for creating pH-potential stability diagrams from Materials Project data through pymatgen. R3.0 restores the historical R2.8 source, upgrades the runtime to Python 3.13, fixes open-species composition handling, and adds reproducible tests and packaging.

## Download and run

Download `pourbaix_gui_R3-win64.zip` from the GitHub R3.0 release, extract the whole archive, and launch `pourbaix_gui_R3\pourbaix_gui_R3.exe`. Keep the executable beside its `_internal` directory. No Python installation or administrator rights are intended to be required.

Paste your own Materials Project API key at runtime. The app requires internet access for calculations and does not intentionally store the key in logs or release artifacts.

For a first calculation, use:

- Elements: `Ti,O`
- Ratios: `1.0`
- pH range: `0,14`
- Potential range: `-2,4` V versus SHE

H and O are open species in the Pourbaix formalism. They may appear in the API chemical system, but they must not receive ratios and are never included in `PourbaixDiagram.comp_dict`.

## Features

- Multi-element Pourbaix diagrams using Materials Project and pymatgen
- Validated element symbols, ratios, pH bounds, and potential bounds before network access
- Custom fonts, line widths, water-line colors, labels, fills, DPI, and transparency
- Boundary export to CSV, XLSX, and tab-separated TXT
- Figure export to PNG, JPEG, TIFF, and SVG
- Exactly one sanitation retry for targeted malformed ion-reference records
- Runtime diagnostics, entry caching, `--self-test`, and `--gui-smoke`
- Clear diagnostics when the MPContribs ion-reference service cannot be initialized
- Per-user logs at `%LOCALAPPDATA%\PourbaixGUI\logs\pourbaix_gui_R3_runtime.log`

## Scientific contract

pH is dimensionless and potential is volts versus SHE. R3 does not implement a custom thermodynamic or energy model: diagram construction and ratio normalization remain delegated to the exact pymatgen packages recorded in `requirements-lock-py313-win64.txt`. Plot styling does not alter exported boundary coordinates. A failed calculation invalidates the previous figure so stale results cannot be exported under new metadata.

## Develop and test

The confirmed development runtime is Windows x64 with CPython 3.13.15.

```powershell
C:\Users\hp\AppData\Local\Python\bin\python3.13.exe -m venv .venv-pourbaix-py313
.\.venv-pourbaix-py313\Scripts\python.exe -m pip install --no-cache-dir -r requirements-lock-py313-win64.txt
.\.venv-pourbaix-py313\Scripts\python.exe -m pytest -q
.\.venv-pourbaix-py313\Scripts\python.exe pourbaix_gui_R3.py --self-test
.\.venv-pourbaix-py313\Scripts\python.exe pourbaix_gui_R3.py --gui-smoke
```

The VS Code workspace settings point the Python extension and Code Runner at `.venv-pourbaix-py313`.

## Build the Windows release

From a clean Git working tree:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\build_release.ps1
```

The script validates staging paths before recursive cleanup, runs the full test and smoke suite, optionally performs a live Ti request when an API key is present, builds the PyInstaller onedir package, checks for `pymatgen/core/entries`, rejects key/log files, creates and extracts the ZIP, reruns packaged self-test, and writes `_release\R3.0\release-manifest.json` with size, entries, SHA-256, versions, and acceptance status.

Clean-machine validation on a separate Windows x64 system without Python remains an explicit Pending external gate until performed against the final archive hash.

## Documentation

- [Windows user guide](USER_GUIDE.md)
- [R3 design](docs/superpowers/specs/2026-08-15-pourbaix-r3-compatibility-design.md)
- [Scientific contract](docs/numerical-contract.md)
- [Acceptance checklist](docs/acceptance-checklist.md)
- [R2 recovery record](docs/r2-recovery.md)

The original screenshots and example diagrams remain in the repository as historical visual examples.
