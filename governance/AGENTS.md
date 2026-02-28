# Governance Agent Guide

Applies to `governance/`.

## Local Rules
- Keep custom properties schema under `job.*`.
- Prefer explicit, typed, stage-safe keys over ambiguous names.
- Do not change key semantics silently; schema changes must be coordinated with worker extractors.

## If You Change X, Also Update Y
- If job property keys change, update all affected worker config extractors and contracts under `domains/worker_*/src`.
- If queue/storage naming conventions change, update `docs/patterns/composition-root.md` and `docs/ARCHITECTURE.md`.
- Keep examples and comments in governance docs consistent with actual key names.

## Local Commands
- Search job keys: `rg -n "job\\." governance/definitions -S`
- Validate impacted workers compile: `python3 -m compileall domains/worker_*/src`
