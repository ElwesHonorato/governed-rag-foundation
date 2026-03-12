# Repository Agent Guide

This file defines repo-wide rules for Codex changes.

## Quick Commands
- Setup (root deps): `poetry install`
- Setup (project deps): `cd <project-dir> && poetry install`
- Stack lifecycle: `./stack.sh up <domain>`, `./stack.sh down`, `./stack.sh ps`, `./stack.sh logs <domain>`
- Test (baseline sanity): `python3 -m compileall libs domains`
- Test (project-level): `cd <project-dir> && poetry run pytest` (when tests exist)
- Lint: project-specific only (no repo-wide lint command configured yet). TODO: standardize.
- Format: project-specific only (no repo-wide formatter command configured yet). TODO: standardize.
- Typecheck: project-specific only (no repo-wide typecheck command configured yet). TODO: standardize.

## Repo Map
- `domains/`: deployable local domains (infra + apps + workers).
- `libs/pipeline-common/`: shared worker/runtime library.
- `domains/gov_governance/`: config definitions (`job.*` custom properties and policies).
- `docs/requirements/`: requirements and architecture decision references.
- `docs/`: normalized architecture/pattern guidance for day-to-day development.
- `docs/standards/patterns/`: preserved standards corpus and policy source material.
- `tooling/ops/`, `tooling/python_env/`, `tooling/ci/`, `stack.sh`: repo operations and developer tooling.

## Architecture Rules
- Dependency direction: `domains/` may depend on `libs/pipeline-common`; `libs/` must not depend on `domains/`.
- Worker entrypoints (`domains/worker_*/src/app.py`) are composition roots only; business logic stays in services/processors.
- Governance config uses `job.*` namespace; key changes must be coordinated with worker config extractors.
- Keep runtime behavior unchanged unless the request explicitly asks for behavior change.

## Compatibility Policy
- No backward compatibility unless explicitly requested by the user.
- Do not add aliases, fallback keys, dual-read/dual-write logic, or deprecation shims by default.
- Prefer clean contract breaks and update all call sites in the same change.
- When old payloads/contracts are incompatible, fail fast with a clear error.
- If compatibility is required, the task must state it explicitly.

## Definition Of Done
- Changed code compiles/tests for affected projects.
- No unrelated refactors or behavior drift.
- If architecture or patterns changed, update `docs/ARCHITECTURE.md` and relevant `docs/patterns/*`.
- If governance keys changed, update worker config contracts and governance docs together.

## Pattern References
- `docs/ARCHITECTURE.md`
- `docs/patterns/composition-root.md`
- `docs/patterns/dependency-injection.md`
- `docs/patterns/error-handling.md`
- `docs/patterns/logging-and-tracing.md`
- `docs/patterns/tool-registry.md` (where applicable)
- `docs/GUIDANCE_INVENTORY.md`
