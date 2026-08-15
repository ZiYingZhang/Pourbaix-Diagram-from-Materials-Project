# Project Memory

Last updated: 2026-08-15

## Authoritative documents

- Design: `docs/superpowers/specs/2026-08-15-pourbaix-r3-compatibility-design.md`
- Research application specification: `docs/research-app-spec.md`
- Numerical contract: `docs/numerical-contract.md`
- Acceptance checklist: `docs/acceptance-checklist.md`
- Implementation plan: `docs/superpowers/plans/2026-08-15-pourbaix-r3-implementation.md`

## Current handoff

- Checkpoint: byte-identical R2 source and documents recovered into `legacy/R2`; R3 implementation branch created.
- Last evidence: both legacy R2 virtual environments fail because their base Python executables no longer exist; Python 3.13.15 is available through Python Install Manager.
- Next task: commit the recovery checkpoint and create the clean Python 3.13 environment.
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
