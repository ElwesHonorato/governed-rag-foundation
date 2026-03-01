# Repository Architecture

This document describes architecture inferred from code structure and imports.
It avoids target-state theory and captures the current implementation.

## High-Level Shape
- `domains/` contains deployable processes: workers, HTTP apps, governance tooling, and infra compose domains.
- `libs/pipeline-common/` is the shared runtime package used by worker domains.
- `registry/` provides runtime job-key lookup used by worker composition roots.
- `stack.sh` + `domains/*/docker-compose.yml` form local deployment orchestration.

## Layering Inferred From Dependencies

### Worker Runtime (primary runtime path)
- Composition roots: `domains/worker_*/src/app.py`
- Application service layer: `domains/worker_*/src/services/*`
- Startup/application wiring layer: `domains/worker_*/src/startup/*` + `pipeline_common.startup`
- Infrastructure adapters: `pipeline_common.gateways.*`
- External drivers: DataHub SDK, boto3/S3, pika/RabbitMQ, Weaviate HTTP

### Governance Apply Tool (separate path)
- Composition root: `domains/gov_governance/src/apply.py`
- Orchestration/use-case style: `orchestration/governance_applier.py`
- Adapter-heavy managers: `entities/*/manager.py`
- Driver coupling: direct DataHub SDK usage in orchestration/managers

### App Domains (RAG API / Vector UI)
- Thin Flask composition and route wiring in `app.py` / `routes.py`
- Service/client classes are colocated and directly use HTTP clients
- Less layered than worker runtime; pragmatic module-level separation

## Layer Mapping (Observed)
| Area | Files / Modules | Observed Layer | Notes |
| --- | --- | --- | --- |
| Worker entrypoints | `domains/worker_*/src/app.py` | Composition Root | Wires settings, runtime factory, launcher, extractor, service factory. |
| Worker startup adapters | `domains/worker_*/src/startup/*` | Application Wiring | Converts generic runtime context into worker-specific services. |
| Worker services | `domains/worker_*/src/services/*` | Application Service | Implements long-running stage behavior. |
| Shared startup contracts | `pipeline_common.startup.contracts` | Application Boundary | Abstract contracts for extractor/factory/service. |
| Shared runtime assembly | `pipeline_common.startup.runtime_factory` | Composition/Wiring | Builds runtime context and shared gateways. |
| Shared gateways | `pipeline_common.gateways.*` | Infrastructure Adapter | External system wrappers and protocol facades. |
| Settings loader | `pipeline_common.settings.provider` | Infrastructure Config Adapter | Env-backed capability-scoped settings loading. |
| Governance managers | `domains/gov_governance/src/entities/*` | Mixed App+Adapter | Business-ish orchestration plus direct DataHub client calls. |

## Major Subsystems
- Worker Runtime Framework (`libs/pipeline-common/src/pipeline_common/startup`)
- Gateway Adapters (`libs/pipeline-common/src/pipeline_common/gateways`)
- Runtime Settings (`libs/pipeline-common/src/pipeline_common/settings`)
- Worker Domains (`domains/worker_*`)
- Governance Apply (`domains/gov_governance`)
- App Domains (`domains/app_rag_api`, `domains/app_vector_ui`)

## Dependency Flow
```text
domains/worker_*/app.py
  -> pipeline_common.settings
  -> pipeline_common.startup
      -> pipeline_common.gateways.factories
          -> pipeline_common.gateways.{lineage,object_storage,queue}
              -> external SDKs/services
```

```text
domains/gov_governance/apply.py
  -> orchestration/governance_applier.py
      -> entities/*/manager.py
          -> DataHub SDK / DataHub Graph
```

## Recurring Patterns Actually Used
- Composition Root: worker `app.py` modules, governance `apply.py`, Flask `create_app`.
- Factory: worker `*ServiceFactory`, gateway factories, runtime context factory.
- Adapter/Facade: `ObjectStorageGateway`, `StageQueue`, `DataHubGraphClient`.
- Strategy-style extension point: `WorkerConfigExtractor` implementations per worker.
- Registry: parser registry in parse worker; DataHub job key registry in `registry/`.

## Architectural Friction / Ambiguities
- Some constructors perform I/O (`StageQueue.__init__`, governance applier initialization), making object construction side-effectful.
- Governance domain intentionally mixes orchestration with SDK concerns; there is no strict app/infra split there yet.
- Runtime lineage has an internal architecture document with stricter critique:
  - `libs/pipeline-common/src/pipeline_common/gateways/lineage/ARCHITECTURE.md`

## Subsystem Architecture Map
```text
docs/ARCHITECTURE.md
|- domains/ARCHITECTURE.md
|- libs/pipeline-common/src/pipeline_common/gateways/ARCHITECTURE.md
|  `- libs/pipeline-common/src/pipeline_common/gateways/lineage/ARCHITECTURE.md
|- libs/pipeline-common/src/pipeline_common/startup/ARCHITECTURE.md
`- libs/pipeline-common/src/pipeline_common/settings/ARCHITECTURE.md
```
