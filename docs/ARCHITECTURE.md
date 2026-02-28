# Architecture Overview

This repository implements a locally runnable governed RAG stack with isolated domains and shared worker runtime infrastructure.

## System Layout
- `domains/`: infrastructure, app, governance, and worker runtime domains, each independently startable via `stack.sh`.
- `libs/pipeline-common/`: shared runtime contracts, startup orchestration, queue/storage/lineage adapters.
- `domains/gov_governance/`: job and policy definitions (`job.*` custom properties).
- `docs/requirements/`: architecture/requirements references.

## Dependency Direction
- `domains/*` may depend on `libs/pipeline-common`.
- `libs/pipeline-common` must not depend on `domains/*`.
- `domains/gov_governance/*` defines configuration schema consumed by workers at runtime.

## Worker Startup Model
Workers follow a shared startup pipeline:
1. `app.py` acts as composition root.
2. `RuntimeContextFactory` assembles runtime gateways and parsed job properties.
3. `WorkerRuntimeLauncher` orchestrates extractor -> service factory -> service loop.
4. Services/processors implement business behavior.

See:
- `docs/patterns/composition-root.md`
- `docs/patterns/dependency-injection.md`

## Runtime Contracts
- `WorkerRuntimeContext` bundles lineage, object storage, stage queue, and job properties.
- Config extraction is strategy-based (`WorkerConfigExtractor`).
- Service graph assembly is encapsulated in `WorkerServiceFactory` implementations.

## Configuration and Governance
- Worker runtime config is sourced from DataHub custom properties expanded from dot notation into nested `job_properties`.
- Canonical key namespace is `job.*`.
- Queue/storage key changes require coordinated updates in governance definitions and worker config extractors.

## Error, Logging, and Traceability
- Worker loops are long-running and fail-soft where appropriate.
- Queue-driven workers should send failed messages to DLQ where contracts allow.
- Lineage events are emitted per processing run for input/output traceability.

See:
- `docs/patterns/error-handling.md`
- `docs/patterns/logging-and-tracing.md`

## Change Safety Rules
- Keep runtime behavior unchanged unless explicitly requested.
- Keep entrypoints orchestration-only.
- Update architecture/pattern docs when changing startup contracts or boundaries.
