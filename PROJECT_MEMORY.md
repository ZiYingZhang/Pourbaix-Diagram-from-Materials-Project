# Project Memory

Last updated: 2026-08-15

## Authoritative documents

- Design: `docs/superpowers/specs/2026-08-15-pourbaix-r3-compatibility-design.md`
- Research application specification: `docs/research-app-spec.md`
- Numerical contract: `docs/numerical-contract.md`
- Acceptance checklist: `docs/acceptance-checklist.md`
- Implementation plan: `docs/superpowers/plans/2026-08-15-pourbaix-r3-implementation.md`

## Current handoff

- Checkpoint: R3.1 candidate addressing the TiO2 default and MPContribs diagnostics is in progress.
- Last evidence: 43 tests pass; venv `ContribsClient` initializes, so the packaged failure was frozen-runtime specific and is now surfaced through warnings capture plus a clear error.
- Next task: run packaged `--contribs-probe`, rebuild the final ZIP, then publish.
- Branch: `codex/r3-compatibility-release`.

## Non-negotiable behavior

- pH is dimensionless; potential is volts versus SHE.
- H/O are open species and excluded from `comp_dict`.
- Display styling cannot change exported boundary data.
- Failed calculations cannot leave stale figures exportable.
- The app never persists API keys.

## Resume procedure

1. Read this file and its authoritative documents.
2. Run the latest verification commands recorded in `release-manifest.json` if present.
3. Continue the first unchecked plan/checklist item.

## Latest build evidence

`_release/R3.0/release-manifest.json` is the single source for the current archive name, byte size, entry count, SHA-256, test counts, smoke exit codes, source commit, toolchain, build time, and external acceptance status. The GitHub release must upload that manifest beside the exact ZIP; do not copy an earlier candidate hash into this file.
