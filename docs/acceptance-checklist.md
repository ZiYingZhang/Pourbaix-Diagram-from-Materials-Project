# Pourbaix GUI R3 Acceptance Checklist

Only checks backed by fresh evidence in `release-manifest.json` may be marked complete.

## Automated and package validation

- [ ] Focused contract tests pass.
- [ ] Full test suite passes.
- [ ] Source `--self-test` passes.
- [ ] Headless Qt construction smoke passes.
- [ ] Clean R3 onedir build passes.
- [ ] Packaged `--self-test` passes.
- [ ] Package contains `pymatgen/core/entries`.
- [ ] GUI launch/close smoke passes.
- [ ] ZIP is non-empty and extracts cleanly.
- [ ] Extracted packaged `--self-test` passes.
- [ ] Package entry count, size, SHA-256, toolchain, and test results are recorded.
- [ ] Archive contains no API key or runtime log.

## Conditional live validation

- [ ] A real Materials Project Ti request passes when `MP_API_KEY`, `MAPI_KEY`, or `PMG_MAPI_KEY` is available.

## Pending external acceptance

| Gate | Status | Required environment | Steps |
|---|---|---|---|
| Portable package | Pending | Clean Windows x64 machine without Python | Extract final ZIP, run self-test, launch GUI, perform Ti workflow |
| Standard-user launch | Pending | Non-admin Windows account | Launch and confirm log creation below `%LOCALAPPDATA%` |
| Display scaling | Pending | Windows at 100%, 125%, 150% | Launch and inspect all controls |

