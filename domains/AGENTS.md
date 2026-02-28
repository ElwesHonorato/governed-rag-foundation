# Domains Agent Guide

Applies to everything under `domains/`.

## Local Rules
- Keep domain entrypoints orchestration-only; move parsing/business logic to `services/`, `startup/`, or `configs/`.
- Do not couple one worker domain directly to another worker domain's Python modules.
- Prefer shared abstractions from `libs/pipeline-common` instead of duplicating contracts.

## If You Change X, Also Update Y
- If `job.storage` or `job.queue` field names change in worker code, update `domains/gov_governance/definitions/600_jobs/600_governed-rag.yaml` in the same change.
- If worker startup wiring changes, update `docs/patterns/composition-root.md` and `docs/ARCHITECTURE.md`.
- If a domain `README.md` startup instructions change, keep `README.md` (repo root) stack examples aligned.

## Local Commands
- Start one domain: `./stack.sh up <domain>`
- Inspect one domain: `./stack.sh logs <domain>`
- Worker sanity compile: `python3 -m compileall domains/worker_*/src`
