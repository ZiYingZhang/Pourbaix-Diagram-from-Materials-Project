# Pourbaix GUI R3 Acceptance Checklist

Only checks backed by fresh evidence in `release-manifest.json` may be marked complete.

## Automated and package validation

- [x] Focused contract tests pass.
- [x] Full test suite passes.
- [x] Source `--self-test` passes.
- [x] Headless Qt construction smoke passes.
- [x] Clean R3 onedir build passes.
- [x] Packaged `--self-test` passes.
- [x] Package contains `pymatgen/core/entries`.
- [x] GUI launch/close smoke passes.
- [x] ZIP is non-empty and extracts cleanly.
- [x] Extracted packaged `--self-test` passes.
- [x] Package entry count, size, SHA-256, toolchain, and test results are recorded.
- [x] Archive contains no API key or runtime log.

## Conditional live validation

- [ ] A real Materials Project Ti request passes when `MP_API_KEY`, `MAPI_KEY`, or `PMG_MAPI_KEY` is available.

## Pending external acceptance

| Gate | Status | Required environment | Steps |
|---|---|---|---|
| Portable package | Pending | Clean Windows x64 machine without Python | Extract final ZIP, run self-test, launch GUI, perform Ti workflow |
| Standard-user launch | Pending | Non-admin Windows account | Launch and confirm log creation below `%LOCALAPPDATA%` |
| Display scaling | Pending | Windows at 100%, 125%, 150% | Launch and inspect all controls |

## Evidence

The release command is `powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\build_release.ps1`. It runs the full project suite, source self-test, source Qt smoke, packaged self-test, packaged Qt smoke, archive extraction, extracted self-test, package-content inspection, and forbidden-file scan. Fresh counts, toolchain versions, archive bytes, entries, SHA-256, timestamp, source commit, and every smoke exit code are written to `_release\R3.0\release-manifest.json`; that manifest is uploaded beside the final ZIP.

The live Materials Project Ti check remains unchecked because no API key was available to the release process. Clean-machine, non-admin, and display-scaling checks remain Pending and must be bound to the SHA-256 in the final uploaded manifest.
