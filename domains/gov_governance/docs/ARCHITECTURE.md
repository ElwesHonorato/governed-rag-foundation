# Governance Domain Architecture (`domains/gov_governance`)

## Scope
This document describes only `domains/gov_governance`, inferred from code under:
- `domains/gov_governance/src/*`
- `domains/gov_governance/definitions/*`
- `domains/gov_governance/configs/*`
- `domains/gov_governance/ci/github/workflows/governance-apply.yml`

## 1) What the governance domain does
`gov_governance` is a metadata-as-code apply tool for DataHub. It:
1. Loads environment config (`configs/dev.yaml`, `configs/prod.yaml`).
2. Discovers and parses governance YAML definitions (`definitions/**.yaml`).
3. Builds an in-memory snapshot (`GovernanceDefinitionSnapshot`).
4. Resolves ID -> DataHub URN maps (`ResolvedRefs`).
5. Applies entities in deterministic order via managers:
   - Static: domains, groups, tags, glossary terms
   - Dynamic: datasets, flows/jobs, lineage contracts
6. Emits DataHub writes via a single adapter (`DataHubGovernanceCatalogWriter`) using DataHub SDK + MCP aspects.

Primary entrypoint:
- [`src/apply.py`](../src/apply.py) -> `main()`

## 2) Key components and responsibilities

| Component | Path | Key symbols | Responsibility |
|---|---|---|---|
| Composition root / CLI | `src/apply.py` | `main()` | Wires env, state loader, DataHub client/graph, concrete writer adapter, and applier. |
| Orchestration service | `src/orchestration/governance_applier.py` | `GovernanceApplier` | Coordinates apply order, converts raw snapshot payloads to typed definitions, builds per-manager contexts. |
| Definition/state loading | `src/state_loader/governance_definitions_state.py` | `GovernanceStateLoader`, `GovernanceDefinitionDiscoverer`, `RelationalDefinitions`, `StandaloneDefinitions`, `resolve_env` | Loads config and definitions, classifies YAML types, assembles pipelines by `flow_id`, validates references. |
| Application managers | `src/entities/*/manager.py` | `DomainManager`, `GroupManager`, `TaxonomyManager`, `DatasetManager`, `FlowJobManager`, `LineageContractManager` | Apply one concern each using typed definitions + context maps + writer port. |
| Typed definition models | `src/entities/shared/definitions.py` | `DomainDefinition`, `GroupDefinition`, `DatasetDefinition`, `PipelineDefinition`, etc. | Converts untyped YAML mappings into typed application inputs. |
| Manager context model | `src/entities/shared/context.py` | `ResolvedRefs`, `*ManagerContext`, `ManagerContexts` | Holds cross-manager runtime context and resolved URN maps. |
| Port contract | `src/entities/shared/ports.py` | `GovernanceCatalogWriterPort` | Defines writes managers can request without SDK coupling. |
| DataHub adapter (write) | `src/infrastructure/datahub/catalog_writer.py` | `DataHubGovernanceCatalogWriter` | Implements port using DataHub SDK entities and MCP aspect emissions. |
| Ref mapping | `src/state_loader/governance_definitions_state.py` | `GovernanceStateLoader.resolve_refs()` | Converts IDs from snapshot into DataHub URNs. |

## 3) Main workflows / data flow

### 3.1 Apply execution flow
1. `apply.py:main()` resolves environment via `state_loader.resolve_env()`.
2. `GovernanceStateLoader.load(env)` loads:
   - DataHub connection settings from `configs/<env>.yaml`
   - Definitions snapshot from `definitions/**.yaml`
   - `ResolvedRefs` maps (`state.refs`) via internal `resolve_refs(...)`
4. `apply.py` creates DataHub clients:
   - `DataHubClient(...)`
   - `DataHubGraph(DatahubClientConfig(...))`
5. `DataHubGovernanceCatalogWriter(graph, client)` is instantiated.
6. `GovernanceApplier(...).apply()` runs:
   - `_apply_static(...)`: domain -> group -> taxonomy
   - `_apply_dynamic(...)`: dataset -> flow/job -> lineage contract
7. Managers call `GovernanceCatalogWriterPort` methods.
8. `DataHubGovernanceCatalogWriter` emits SDK/MCP operations to DataHub.

### 3.2 Definition discovery flow
`GovernanceDefinitionDiscoverer.load()`:
- Scans `definitions/**/*.yaml`.
- Classifies each file by top-level keys (`DefinitionType`).
- Stores standalone entities (`domains`, `groups`, `tags`, `terms`, `datasets`) in `StandaloneDefinitions`.
- Stores relational entities (`flow`, `jobs`, `lineage_contract`) in `RelationalDefinitions`.
- `RelationalDefinitions` validates `flow_id` references and assembles deterministic `pipelines` sorted by flow id.

## 4) Inferred layer model (from dependencies)

The code does not label layers explicitly, but import direction shows these practical layers.

### Layer A: Definitions & Runtime State Loading
- Responsibilities:
  - Read configs and YAML definitions
  - Classify and aggregate definitions
  - Validate environment and relational references (`flow_id`)
  - Produce `GovernanceState`
  - Build `ResolvedRefs` URN maps
- Key files/classes:
  - [`src/state_loader/governance_definitions_state.py`](../src/state_loader/governance_definitions_state.py)
  - `GovernanceStateLoader`, `GovernanceDefinitionDiscoverer`, `RelationalDefinitions`
- Depends on:
  - `pipeline_common.helpers.file_reader.FileReader`
  - `pipeline_common.helpers.file_system_helper.FileSystemHelper`
  - `datahub.metadata.urns.*` (for `resolve_refs`)
  - `os`, `pathlib`, stdlib types

### Layer B: Application Orchestration & Use-Case Services
- Responsibilities:
  - Convert raw payloads to typed definitions
  - Enforce apply order and workflow
  - Resolve ID references via context maps during write requests
  - Express write intent via port interface (not SDK objects)
- Key files/classes:
  - [`src/orchestration/governance_applier.py`](../src/orchestration/governance_applier.py) (`GovernanceApplier`)
  - [`src/entities/*/manager.py`](../src/entities)
  - [`src/entities/shared/definitions.py`](../src/entities/shared/definitions.py)
  - [`src/entities/shared/context.py`](../src/entities/shared/context.py)
  - [`src/entities/shared/ports.py`](../src/entities/shared/ports.py)
- Depends on:
  - Layer A output (`GovernanceState`)
  - Port protocol (`GovernanceCatalogWriterPort`)
  - No direct `datahub.*` imports in managers/orchestration

### Layer C: Infrastructure Adapters (DataHub-specific)
- Responsibilities:
  - Translate port calls into DataHub SDK entities/aspects
  - Perform URN construction and normalization
  - Emit MCP upserts and SDK upserts
- Key files/classes:
  - [`src/infrastructure/datahub/catalog_writer.py`](../src/infrastructure/datahub/catalog_writer.py)
- Depends on:
  - `datahub.sdk` (`DataFlow`, `DataJob`, `Dataset`, `Tag`, `DataHubClient`)
  - `datahub.emitter.mcp.MetadataChangeProposalWrapper`
  - `datahub.metadata.schema_classes.*`
  - `datahub.metadata.urns.*`

### Layer D: Composition Root / Delivery
- Responsibilities:
  - Instantiate concrete adapter and external clients
  - Connect layers A, B, C together at runtime
- Key files/classes:
  - [`src/apply.py`](../src/apply.py)
- Depends on:
  - Layer A loader
  - Layer B orchestrator
  - Layer C adapters
  - DataHub connection classes (`DataHubGraph`, `DatahubClientConfig`, `DataHubClient`)

## 5) Dependency and boundary view

### 5.1 Compile-time dependency direction

```text
apply.py (composition root)
  ├─> state_loader (load GovernanceState)
  ├─> infrastructure.datahub.DataHubGovernanceCatalogWriter
  └─> orchestration.GovernanceApplier
         ├─> entities managers
         ├─> entities.shared.definitions/context
         └─> entities.shared.ports (GovernanceCatalogWriterPort)

infrastructure.datahub.*
  └─> datahub SDK + MCP + URN classes

state_loader
  └─> pipeline_common file helpers
```

### 5.2 Runtime call flow

```text
YAML files (configs + definitions)
   │
   ▼
GovernanceStateLoader.load()
   │   produces GovernanceState(snapshot + env settings + refs)
   ▼
GovernanceApplier.apply()
   ├─ static: DomainManager -> GroupManager -> TaxonomyManager
   └─ dynamic: DatasetManager -> FlowJobManager -> LineageContractManager
            each manager calls GovernanceCatalogWriterPort
                               │
                               ▼
                 DataHubGovernanceCatalogWriter (adapter)
                               │
                               ▼
                DataHubGraph.emit / DataHubClient.entities.upsert
                               │
                               ▼
                             DataHub
```

## 6) External systems and adapters
- External metadata system: DataHub (GMS server from `configs/*.yaml`).
- Adapter boundary:
  - Port: `GovernanceCatalogWriterPort` (`src/entities/shared/ports.py`)
  - Adapter: `DataHubGovernanceCatalogWriter` (`src/infrastructure/datahub/catalog_writer.py`)
- URN mapping is implemented in `GovernanceStateLoader.resolve_refs` (`src/state_loader/governance_definitions_state.py`).

## 7) Observed patterns from code
- Composition Root: `src/apply.py`
- Use-case orchestration service: `GovernanceApplier`
- Application service per concern: manager classes under `src/entities/*/manager.py`
- Port/Adapter boundary: `GovernanceCatalogWriterPort` -> `DataHubGovernanceCatalogWriter`
- Data Mapper / DTO conversion: `*.from_mapping()` in `src/entities/shared/definitions.py`

## 8) How to extend

### Add a new governance entity type (example: `assertions`)
1. Add YAML type and files under `definitions/`.
2. Extend `DefinitionType` and discovery/aggregation in [`state_loader/governance_definitions_state.py`](../src/state_loader/governance_definitions_state.py).
3. Add typed model in [`entities/shared/definitions.py`](../src/entities/shared/definitions.py).
4. Add manager + context (new `entities/<entity>/manager.py`, update `entities/shared/context.py`).
5. Add/extend port method in [`entities/shared/ports.py`](../src/entities/shared/ports.py).
6. Implement adapter behavior in [`infrastructure/datahub/catalog_writer.py`](../src/infrastructure/datahub/catalog_writer.py).
7. Wire new manager call in [`orchestration/governance_applier.py`](../src/orchestration/governance_applier.py) in correct ordering.

### Add new metadata fields to existing entities
1. Extend typed definition dataclass in `entities/shared/definitions.py`.
2. Thread field through manager call to port method.
3. Extend port signature and adapter implementation.
4. Update YAML definitions under `definitions/*`.

### Add new environment
1. Add config file under `configs/<env>.yaml`.
2. Add env name to `ALLOWED_ENVS` in `state_loader/governance_definitions_state.py`.
3. Provide required token env var in runtime/CI.
