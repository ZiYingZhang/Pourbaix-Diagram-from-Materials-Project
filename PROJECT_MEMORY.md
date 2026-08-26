# Project Memory

Last updated: 2026-08-26

## Authoritative documents

- R4 design: `docs/superpowers/specs/2026-08-22-pourbaix-r4-pyside6-design.md`
- R4 implementation plan: `docs/superpowers/plans/2026-08-22-pourbaix-r4-implementation.md`
- Research application specification: `docs/research-app-spec.md`
- Numerical contract: `docs/numerical-contract.md`
- Acceptance checklist: `docs/acceptance-checklist.md`

## Current handoff

- Branch: `codex/r4-foundation`
- Checkpoint: R4 core UI, Origin-style plotting controls, application branding, portable source paths, and Windows `onedir` packaging are implemented.
- Latest source evidence: 126 R4 tests passed; R4 source self-test and GUI smoke passed.
- Latest package evidence: source, packaged, and freshly extracted self-test/GUI smoke passed for `_release/R4.0/PourbaixStudioR4-win64.zip`.
- Release source commit: `3cb6fc415c5b8609f68eb49634b337b387437155` with `working_tree_dirty: false` in the manifest.
- Candidate SHA-256: `2E44ECBFFA74AD84723B9B62FD23EFD0E5DE69D5E341CC37C131EDD028755408`.
- Packaging fix: non-system ICU directories are removed from the PyInstaller PATH so external Poppler ICU DLLs cannot shadow the Windows ICU required by PySide6.
- Next product task: repair API-key session use and actionable calculation diagnostics before the first public R4 release.

## Non-negotiable behavior

- pH is dimensionless; potential is volts versus SHE.
- H/O are open species and excluded from `comp_dict`.
- Up to four closed elements are supported.
- Display styling cannot change calculated or exported boundary data.
- Re-plotting from a current snapshot cannot make an API request.
- Failed calculations cannot leave stale figures exportable.
- API keys use Windows Credential Manager for new persistence and are never packaged.
- Preserve the user-owned untracked `test Sb2Se3.svg`.

## Portable release

- Build command: `powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\build_release_r4.ps1`.
- Default source runtime: `.venv-pourbaix-py313\Scripts\python.exe`; recreate the virtual environment after moving the source folder.
- Distribute the complete `PourbaixStudioR4` directory or its ZIP. Never move `PourbaixStudioR4.exe` without `_internal`.
- Clean-machine Windows x64 validation without Python is still Pending and must be tied to the final archive SHA-256.
