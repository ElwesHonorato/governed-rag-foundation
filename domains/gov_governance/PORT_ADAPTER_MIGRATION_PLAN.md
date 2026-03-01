# Governance Port/Adapter Migration Plan

## Goal
Migrate governance apply code to a cleaner application/infrastructure split without behavior changes.

## Scope
- `domains/gov_governance/src`
- Composition root: `src/apply.py`
- Orchestration: `src/orchestration/governance_applier.py`
- Managers: `src/entities/*/manager.py`
- New adapters: `src/infrastructure/datahub/*`

## Target Architecture

```text
apply.py (composition root)
    -> GovernanceApplier (application orchestration)
        -> Ports (application contracts)
            -> DataHub adapters (infrastructure)
                -> DataHub SDK
```

## Safe Migration Path

### 1. Define governance ports (application-side interfaces)
Create application contracts under `src/application/ports/` (or `src/entities/*/ports.py` during transition):

- `GovernanceCatalogWriterPort`
  - upsert domain/group/tag/term/dataset/flow/job/lineage-related writes
- `GovernanceGraphReaderPort` (only if a manager/orchestrator needs graph reads)

Notes:
- Keep port signatures based on primitive/domain DTO values.
- Do not expose DataHub SDK types in port interfaces.

### 2. Move DataHub SDK code behind adapters
Create/expand:
- `domains/gov_governance/src/infrastructure/datahub/*`

Adapters implement ports using:
- `DataHubClient`
- `DataHubGraph`
- URN classes
- MCP wrappers/schema classes

Rule:
- All `datahub.*` imports live in `infrastructure/datahub/*` only.

### 3. Keep orchestration pure
`GovernanceApplier` should:
- depend on ports + domain DTOs/context models
- avoid direct imports from `datahub.*`
- coordinate managers and context wiring only

### 4. Split manager responsibilities
Managers become application services:
- Input: typed definitions + context maps
- Dependency: ports only
- No direct DataHub SDK payload construction in managers

Move to adapters:
- URN construction
- MCP aspect shaping
- SDK entity object construction

### 5. Make composition root wire concrete adapters
`src/apply.py` should:
- instantiate concrete DataHub adapters
- inject adapters into `GovernanceApplier` / manager contexts

Composition root owns concrete implementation choice.

### 6. Keep behavior unchanged during migration
Migration strategy:
1. Introduce ports first.
2. Add adapters mirroring current behavior exactly.
3. Migrate one manager at a time.
4. Keep outputs and side effects identical.

Verification after each slice:
- compile success
- same apply ordering
- same upsert semantics
- same printed/logged checkpoints (if relied on)

## Incremental Rollout Plan

### Slice A (done/started)
- Domain manager via `DomainCatalogWriter` + `DataHubDomainWriter`.

### Slice B
- Group manager port + DataHub group writer adapter.

### Slice C
- Taxonomy manager split:
  - tag writer + glossary writer ports/adapters.

### Slice D
- Dataset manager port + DataHub dataset writer adapter.

### Slice E
- Flow/job manager port + DataHub flow/job writer adapter.

### Slice F
- Lineage contract manager port + DataHub lineage contract adapter.

### Slice G
- Optional graph read port if any manager still does read-through operations.

## Definition of Done
- `GovernanceApplier` has no `datahub.*` imports.
- Managers in `entities/*/manager.py` have no `datahub.*` imports.
- DataHub SDK usage is isolated to `infrastructure/datahub/*`.
- Composition root wires concrete adapters.
- Runtime behavior unchanged.

## Non-Goals
- No redesign of governance definition schema.
- No change to governance apply ordering.
- No broad refactor of unrelated worker/runtime modules.
