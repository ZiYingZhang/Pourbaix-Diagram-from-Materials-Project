# Changelog

## R3.0 — 2026-08-15

- Recovered byte-identical R2.8 source, build definition, and user documentation into `legacy/R2`.
- Rebuilt the environment on CPython 3.13.15 with `mp-api==0.46.4`, `pymatgen`, and `pymatgen-core`; added a complete Windows lock file.
- Added strict local validation for element symbols, non-H/O ratios, finite ordered pH/potential ranges, and duplicate elements.
- Excluded H/O from `comp_dict` so ratios describe only non-H/O elements.
- Defaulted the elements field to `Ti,O` (TiO2 requires both in the API chemical system) with ratio `1.0` for Ti.
- Added exactly-one sanitation retry for empty results or targeted missing ion-reference fields while preserving unrelated exceptions.
- Invalidated stale figures and metadata before every new plot attempt.
- Moved logs to `%LOCALAPPDATA%\PourbaixGUI\logs` and added source/packaged self-test and GUI smoke modes.
- Routed Python warnings into the local log and added an actionable error when the MPContribs ion-reference service cannot initialize.
- Extended self-test to cover the dynamically imported MPContribs client and added `--contribs-probe` for packaged diagnostics.
- Replaced the absolute R2 PyInstaller spec with an environment-relative R3 spec and automated release validation/manifest generation.

## R2.8

- Historical PyQt5 GUI with Materials Project retrieval, plotting controls, caching, diagnostics, figure export, and boundary export.
