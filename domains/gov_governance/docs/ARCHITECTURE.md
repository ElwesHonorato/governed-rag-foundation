# Governance Domain Architecture (`domains/gov_governance`)

## Scope
This document describes the current implemented architecture for:
- `domains/gov_governance/src/*`
- `domains/gov_governance/definitions/*`
- `domains/gov_governance/docs/*`

It intentionally reflects code as-is (not target-state design).

## What This Domain Does
`gov_governance` applies governance metadata-as-code into DataHub.

At runtime it:
1. Loads DataHub runtime settings through shared settings (`SettingsProvider(SettingsRequest(datahub=True))`).
2. Loads governance YAML definitions from `definitions/**/*.yaml`.
3. Builds an in-memory snapshot (`GovernanceDefinitionSnapshot`).
4. Resolves ID-to-URN maps (`ResolvedRefs`) for cross-entity linking.
5. Applies governance entities in deterministic order through managers.
6. Persists through a single adapter (`DataHubGovernanceCatalogWriter`) using DataHub SDK + MCP.

Entrypoint:
- [`src/apply.py`](../src/apply.py)

## Current Layering (Observed)

### Composition Root
- File: [`src/apply.py`](../src/apply.py)
- Responsibilities:
  - Load DataHub settings from environment.
  - Instantiate `GovernanceStateLoader`.
  - Instantiate `DataHubClient` + `DataHubGraph`.
  - Wire `GovernanceApplier` with concrete writer adapter.

### State Loading and Definition Discovery
- File: [`src/state_loader/governance_definitions_state.py`](../src/state_loader/governance_definitions_state.py)
- Responsibilities:
  - Discover/parse YAML definitions.
  - Classify definition file types (`DefinitionType`).
  - Build normalized pipeline payloads from flow/jobs/lineage-contract files.
  - Build `ResolvedRefs` URN maps for domain/group/tag/term/dataset IDs.

### Application Orchestration
- File: [`src/orchestration/governance_applier.py`](../src/orchestration/governance_applier.py)
- Responsibilities:
  - Split runtime state into manager-specific contexts.
  - Enforce apply order.
  - Convert raw payload mappings into typed definitions.

### Entity Managers (Use-Case Units)
- Files: [`src/entities/*/manager.py`](../src/entities)
- Responsibilities:
  - Domain, group, taxonomy, dataset, flow/job, and lineage-contract apply operations.
  - Resolve references via context maps and invoke writer port.

### Port and Infrastructure Adapter
- Port: [`src/entities/shared/ports.py`](../src/entities/shared/ports.py)
- Adapter: [`src/infrastructure/datahub/catalog_writer.py`](../src/infrastructure/datahub/catalog_writer.py)
- Responsibilities:
  - Keep managers SDK-agnostic (port surface).
  - Translate write calls into DataHub SDK entities and MCP aspects.

## Runtime Flow

```text
Environment vars
  └─> SettingsProvider(SettingsRequest(datahub=True)).bundle.datahub
       └─> apply.py
            ├─> GovernanceStateLoader(env).state
            │    ├─> GovernanceDefinitionDiscoverer(definitions/**/*.yaml)
            │    ├─> StandaloneDefinitions + RelationalDefinitions
            │    └─> ResolvedRefs (URN maps)
            ├─> DataHubClient + DataHubGraph
            └─> GovernanceApplier.apply()
                 ├─ static: Domain -> Group -> Taxonomy
                 └─ dynamic: Dataset -> Flow/Job -> Lineage
                      └─> GovernanceCatalogWriterPort
                           └─> DataHubGovernanceCatalogWriter
                                └─> DataHub
```

## Deterministic Ordering Rules
- Static entities:
  1. Domains
  2. Groups
  3. Tags/Terms
- Dynamic entities:
  1. Datasets
  2. Flows/Jobs
  3. Lineage contracts

`RelationalDefinitions._assemble_pipelines()` sorts by `flow_id`, making flow-based execution deterministic.

## Core Data Contracts
- `GovernanceDefinitionSnapshot`:
  - `domains`, `groups`, `tags`, `terms`, `datasets`, `pipelines`
- `GovernanceState`:
  - `governance_definitions_snapshot`
  - `refs: ResolvedRefs`
- `ResolvedRefs`:
  - `domain_urns`, `group_urns`, `tag_urns`, `term_urns`, `dataset_urns`

## Dependency Direction

```text
apply.py
  ├─> state_loader
  ├─> orchestration
  └─> infrastructure.datahub

orchestration
  ├─> entities managers
  ├─> entities definitions/context
  └─> entities ports

infrastructure.datahub
  └─> datahub SDK + MCP
```

No manager imports DataHub SDK directly; SDK coupling is concentrated in `infrastructure/datahub`.

## Architectural Friction / Ambiguities

### 1) Loader has side effects in constructor (accepted)
- Current behavior:
  - `GovernanceStateLoader.__init__` immediately executes `_load()` and stores `.state`.
- Friction:
  - Instantiation triggers disk I/O and validation.
  - This reduces clarity and test ergonomics (construction vs execution lifecycle are merged).
- Decision:
  - Keep eager-init behavior.

### 2) Double-write behavior for jobs is explicit (accepted)
- Current behavior:
  - `FlowJobManager` upserts jobs first (without lineage).
  - `LineageContractManager` upserts the same jobs again (with inlets/outlets).
- Rationale:
  - Separates job template upsert concerns from lineage edge attachment concerns.
  - Allows jobs to exist even when lineage contracts are intentionally partial or delayed.
- Decision:
  - Keep as explicit two-phase strategy.

### 3) CLI observability uses `print` across layers
- Current behavior:
  - Managers and applier print progress directly.
- Friction:
  - No structured log levels, correlation IDs, or consistent sink strategy.
  - Harder to integrate with CI/ops telemetry standards.
- Decision needed:
  - Standardize on logging interface (aligned with repo logging/tracing patterns).

## Extension Guide

### Add a new governance entity type
1. Add YAML definitions under `definitions/`.
2. Extend `DefinitionType` and discovery wiring in [`state_loader/governance_definitions_state.py`](../src/state_loader/governance_definitions_state.py).
3. Add typed model in [`entities/shared/definitions.py`](../src/entities/shared/definitions.py).
4. Add/extend manager context in [`entities/shared/context.py`](../src/entities/shared/context.py).
5. Add manager implementation in `entities/<new_entity>/manager.py`.
6. Extend port in [`entities/shared/ports.py`](../src/entities/shared/ports.py).
7. Implement adapter behavior in [`infrastructure/datahub/catalog_writer.py`](../src/infrastructure/datahub/catalog_writer.py).
8. Wire manager call ordering in [`orchestration/governance_applier.py`](../src/orchestration/governance_applier.py).

### Add new fields to existing entities
1. Extend typed dataclass and `from_mapping`.
2. Thread through manager and context as needed.
3. Extend port + adapter signatures.
4. Update YAML payloads.

## External References (Design and Refactoring Heuristics)
- Refactoring Guru - Adapter: https://refactoring.guru/design-patterns/adapter
- Refactoring Guru - Facade: https://refactoring.guru/design-patterns/facade
- Refactoring Guru - Factory Method: https://refactoring.guru/design-patterns/factory-method
- Refactoring Guru - Shotgun Surgery: https://refactoring.guru/smells/shotgun-surgery
- Refactoring Guru - Feature Envy: https://refactoring.guru/smells/feature-envy
- Refactoring Guru - Long Method: https://refactoring.guru/smells/long-method

These references are used as shared vocabulary for the friction items above, not as strict prescriptions.
