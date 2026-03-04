# 1. Purpose

`pipeline_common.startup` standardizes worker bootstrap.

Problem it solves:
- Every worker needs the same startup sequence: load shared runtime context, extract worker config, build service, start loop.

Why it exists:
- Avoid duplicated composition logic across `domains/worker_*` entrypoints.
- Keep worker `app.py` files thin and consistent.

What it does:
- Defines startup contracts (`WorkerConfigExtractor`, `WorkerServiceFactory`, `WorkerService`).
- Builds `WorkerRuntimeContext` from settings + DataHub job key.
- Launches worker startup pipeline through `WorkerRuntimeLauncher`.
- Parses DataHub custom properties into nested `job_properties`.

What it does not do:
- It does not implement worker business processing.
- It does not own worker-specific config semantics.
- It does not run deployment orchestration or process supervision.

Boundaries:
- Upstream: worker entrypoints under `domains/worker_*/src/app.py`.
- Downstream: `pipeline_common.settings` and `pipeline_common.gateways`.

# 2. High-Level Responsibilities

Core responsibilities:
- Provide shared startup abstractions for worker extensibility.
- Construct runtime dependencies used by all workers.
- Execute one canonical startup flow.

Non-responsibilities:
- No domain processing logic.
- No persistent runtime state management.
- No retry/backoff orchestration beyond what services/gateways do.

Separation of concerns:
- `contracts.py`: startup extension interfaces.
- `runtime_context.py`: immutable runtime dependency bundle.
- `runtime_factory.py`: runtime context assembly.
- `job_properties.py`: dot-key to nested dict parser.
- `launcher.py`: orchestration of startup sequence.

# 3. Architectural Overview

Overall design:
- This package is a startup orchestration layer with explicit extension points.
- Worker domains supply implementations of extractor and service factory.
- Shared startup code builds infra dependencies once and passes them forward.

Layering in this package:
- Contracts layer: generic worker startup interfaces.
- Composition layer: runtime context factory.
- Orchestration layer: launcher.

Patterns used:
- Composition Root support: workers use this package to compose runtime services.
- Dependency Injection: launcher receives runtime factory + extractor + service factory.
- Factory pattern: `RuntimeContextFactory` and worker service factories build objects.
- Template-method-like sequence: launcher enforces fixed startup order.

Why chosen:
- Constrains worker startup drift.
- Preserves flexibility for worker-specific config/service graphs.
- Keeps startup mechanics reusable across multiple workers.

# 4. Module Structure

Package layout:
- `contracts.py`: startup contracts and polling contract dataclass.
- `runtime_context.py`: `WorkerRuntimeContext` dataclass.
- `runtime_factory.py`: `RuntimeContextFactory`.
- `job_properties.py`: `JobPropertiesParser`.
- `launcher.py`: `WorkerRuntimeLauncher`.
- `__init__.py`: package exports.

What belongs where:
- Add new shared startup contract types in `contracts.py`.
- Add runtime dependency fields in `runtime_context.py`.
- Add cross-worker bootstrap assembly in `runtime_factory.py`.
- Keep worker-specific parsing/building in worker domain `startup/` folders.

Dependency flow:
- `launcher` depends on `contracts` + `runtime_factory`.
- `runtime_factory` depends on gateway factories, settings bundle, and job-properties parser.
- Worker domains depend on this package; this package does not depend on worker domains.

```mermaid
graph TD
    A[domains/worker_*/src/app.py] --> B[SettingsProvider bundle]
    A --> C[RuntimeContextFactory]
    A --> D[WorkerRuntimeLauncher]

    C --> E[Gateway Factories]
    C --> F[JobPropertiesParser]
    C --> G[WorkerRuntimeContext]

    D --> H[WorkerConfigExtractor]
    D --> I[WorkerServiceFactory]
    I --> J[WorkerService]

    E --> K[pipeline_common.gateways]
    B --> L[pipeline_common.settings]
```

# 5. Runtime Flow (Golden Path)

Standard startup path used by worker entrypoints:
1. Worker entrypoint creates `SettingsProvider(SettingsRequest(...)).bundle`.
2. Worker builds `RuntimeContextFactory(data_job_key, settings_bundle)`.
3. Runtime factory builds lineage gateway, resolves job metadata, parses custom properties, builds storage/queue gateways, and builds optional Spark session.
4. Worker creates `WorkerRuntimeLauncher(runtime_factory, config_extractor, service_factory)`.
5. Launcher `start()` reads runtime context.
6. Launcher calls extractor to build typed worker config.
7. Launcher calls service factory to construct worker service.
8. Launcher invokes `service.serve()` and transfers control to worker loop.
9. Launcher `finally` block stops Spark session when present.

Shutdown/termination behavior:
- Service lifecycle termination is owned by worker service implementation.
- Shared runtime finalization currently stops Spark session from launcher `finally`.

```mermaid
flowchart TD
    A[Worker app.py] --> B[Load settings bundle]
    B --> C[Create RuntimeContextFactory]
    C --> D[Build gateways + parse job properties]
    D --> E[Create WorkerRuntimeLauncher]
    E --> F[Extract typed worker config]
    F --> G[Build worker service]
    G --> H[service.serve]
```

# 6. Key Abstractions

`WorkerConfigExtractor[T]`
- Represents: worker-specific config parser contract.
- Why exists: keeps worker-specific config parsing out of shared startup orchestration.
- Depends on: resolved `job_properties` mapping.
- Depended on by: `WorkerRuntimeLauncher`.
- Safe extension: keep extraction deterministic and validation-focused.

`WorkerServiceFactory[TConfig, TService]`
- Represents: worker-specific service construction contract.
- Why exists: isolate dependency graph creation per worker.
- Depends on: `WorkerRuntimeContext`, typed worker config.
- Depended on by: `WorkerRuntimeLauncher`.
- Safe extension: avoid side effects unless explicitly required (for example schema/bootstrap checks).

`WorkerService`
- Represents: long-running worker loop contract (`serve()`).
- Why exists: launcher can start workers uniformly.
- Depends on: concrete service internals.
- Depended on by: launcher and worker entrypoint path.
- Safe extension: keep `serve()` blocking and lifecycle-owned by service implementation.

`RuntimeContextFactory`
- Represents: shared runtime dependency assembler.
- Why exists: one place to build lineage/storage/queue gateways, optional Spark session, and parsed job properties.
- Depends on: settings bundle, data job key, gateway factories.
- Depended on by: worker entrypoints and launcher.
- Safe extension: preserve returned `WorkerRuntimeContext` contract and avoid worker-specific logic.

`WorkerRuntimeLauncher`
- Represents: startup orchestration executor.
- Why exists: enforce one bootstrap sequence across workers.
- Depends on: runtime factory, extractor, service factory.
- Depended on by: worker entrypoints.
- Safe extension: maintain startup order and finalization semantics unless cross-worker migration is coordinated.

# 7. Extension Points

Where to add features:
- New shared startup contract: `contracts.py`.
- New shared runtime dependency: `runtime_context.py` + `runtime_factory.py`.
- New worker config logic: worker-local `startup/config_extractor.py`.
- New worker service graph: worker-local `startup/service_factory.py`.

How to add a new worker following conventions:
1. Create worker `src/app.py` composition root.
2. Request needed settings via `SettingsRequest`.
3. Build `RuntimeContextFactory` with job key from registry.
4. Implement worker extractor + service factory.
5. Start with `WorkerRuntimeLauncher(...).start()`.

Boundary guardrails:
- Do not import worker-specific modules into `pipeline_common.startup`.
- Do not embed worker business logic in runtime factory or launcher.
- Keep startup package generic and reusable.

# 8. Known Issues & Technical Debt

Issue: `RuntimeContextFactory.__init__` performs full runtime assembly.
- Why problem: object construction has side effects (metadata resolution and gateway initialization).
- Direction: consider explicit `.build()` method to separate construction from execution.

Issue: `JobPropertiesParser` only expands dotted keys.
- Why problem: non-dotted custom properties are ignored by parser output.
- Direction: document this contract clearly or support explicit passthrough map for flat keys.

Issue: implicit required nested keys in runtime factory.
- Why problem: `job_properties["job"]["queue"]` can fail if metadata contract is missing/incomplete.
- Direction: add explicit validation and clearer startup errors near parser/factory boundary.

Issue: launcher has limited shutdown/error policy hooks.
- Why problem: startup flow finalizes Spark shutdown only; it does not expose generalized lifecycle callbacks.
- Direction: add optional lifecycle hooks only if multiple workers require them.

# 9. Future Roadmap / Planned Enhancements

Confirmed roadmap:
- None explicitly documented in this module.

# 10. Anti-Patterns / What Not To Do

- Do not place worker business processing logic in `pipeline_common.startup`.
- Do not bypass `WorkerRuntimeLauncher` with inconsistent startup ordering across workers.
- Do not couple shared startup contracts to specific worker types.
- Do not mutate `WorkerRuntimeContext` after build; treat it as immutable runtime input.
- Do not assume all custom properties are present without validation.

# 11. Glossary

- Worker Runtime Context: shared dependencies injected into worker services.
- Config Extractor: worker-specific parser from generic job properties to typed config.
- Service Factory: worker-specific constructor for the concrete worker service.
- Launcher: orchestrator that runs the standard bootstrap sequence.
- Job Properties: nested config derived from DataHub `custom_properties` dot-notation keys.
