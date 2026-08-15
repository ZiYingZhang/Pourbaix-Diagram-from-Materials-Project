# Research Application Specification

## Project identity

- Project: Pourbaix GUI R3.0.
- Primary users: materials researchers who need publication-ready Pourbaix diagrams without maintaining a Python environment.
- Scientific purpose: construct pH-potential phase-stability diagrams and export their visible stability-domain boundaries.
- Target: Windows x64, CPython 3.13.15, PyQt5, PyInstaller onedir ZIP.
- Route: migration from the preserved R2.8 implementation.

## Trust map

- R2 is retained as a behavioral reference for UI controls, plotting style, figure export, and boundary clipping/export.
- Thermodynamic construction is not reimplemented or snapshot-copied from R2; the pinned pymatgen release is the scientific authority.
- R2 composition handling is explicitly untrusted because it included H/O in `comp_dict`.
- Old R2 build environments are unusable because their base interpreters are missing; old packages remain historical artifacts only.

## Workflows

The primary workflow accepts elements, ratios for non-H/O elements, pH bounds, potential bounds, and a user-supplied Materials Project API key. It validates locally, fetches Pourbaix entries, delegates diagram construction to pymatgen, and displays the plot.

Independent workflows are figure export, boundary export, species-label listing, diagnostics, cache clearing, and runtime self-test. Figure export requires a current successful figure; boundary export performs its own validated calculation. Self-test requires neither GUI display nor API key.

## Files and delivery

- Inputs: UI text fields and online Materials Project data.
- Outputs: PNG, JPEG, TIFF, SVG, CSV, XLSX, TXT, runtime log.
- Network: required for Materials Project calculations; not required for self-test or viewing a generated package.
- Permissions: no administrator rights; logs live below `%LOCALAPPDATA%/PourbaixGUI/logs`.
- Delivery: `_release/R3.0/pourbaix_gui_R3/` plus `_release/R3.0/pourbaix_gui_R3-win64.zip`.
- Secrets: API keys are runtime-only and excluded from source, logs, manifests, and archives.

## Scope

R3 includes R2 recovery, Python 3.13 compatibility, scientific input validation, exactly-one targeted sanitation retry, stale-result invalidation, reproducible dependencies, packaging, verification, and documentation. It excludes UI redesign, background threading, offline datasets, installers, signing, and auto-update.

## Completion definition

Automated tests, source self-test, headless Qt smoke, clean package build, packaged self-test, package-content inspection, archive/extract/self-test, and a machine-readable manifest must pass. A live Ti request is executed only when an API key is available. Clean-machine Windows x64 acceptance remains Pending until performed against the final archive hash.

