# Project Memory

Last updated: 2026-08-25

## Authoritative documents

- R4 design: `docs/superpowers/specs/2026-08-22-pourbaix-r4-pyside6-design.md`
- R4 implementation plan: `docs/superpowers/plans/2026-08-22-pourbaix-r4-implementation.md`
- Research application specification: `docs/research-app-spec.md`
- Numerical contract: `docs/numerical-contract.md`
- Acceptance checklist: `docs/acceptance-checklist.md`

## Current handoff

- Branch: `codex/r4-foundation`
- Checkpoint: R4 core UI, plotting, portable source paths, and Windows `onedir` packaging are implemented.
- Latest source evidence: 155 tests passed; R4 source self-test and GUI smoke passed.
- Latest package evidence: packaged and extracted self-test/GUI smoke passed for `_release/R4.0/PourbaixStudioR4-win64.zip`.
- Candidate SHA-256: `0CC7E74203BB594C8ABEF48C14CD27E1FBF711ED9C8873CE20D13B3AEA6F7D3F`.
- The candidate manifest records a dirty working tree because it was built before the implementation commit and while the user-owned untracked `test Sb2Se3.svg` was present. Rebuild after committing before treating an archive as final.
- Next product task: style presets; design was discussed but not yet implemented.

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
