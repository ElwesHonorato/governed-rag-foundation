# Runtime DataHub Lineage - Architecture Review

## 1. Current Responsibilities
This module currently:
- Builds DataHub URNs for flows, jobs, datasets, and process instances.
- Reads DataJob metadata (`DataJobInfo`) from DataHub to resolve runtime config.
- Emits runtime lineage MCPs (`DataProcessInstance*` + run event).
- Tracks per-run state (inputs, outputs, status transitions).
- Exposes a factory used by workers to construct the lineage gateway.

Current class-to-layer interpretation:
- Infrastructure (Adapter): `DataHubGraphClient`, `DataProcessInstanceMcpBuilder` (actual behavior: factory), `DataHubRunTimeLineage`, `DataHubUrnFactory`, `DataHubSettings`, `DataHubLineageGatewayFactory`.
- Application: `DataHubJobMetadataResolver` (orchestration use-case, currently coupled to infra client).
- Domain DTO/value models: `DataHubDataJobKey`, `ResolvedDataHubFlowConfig`, `CustomProperties`, `RunSpec`, `ActiveRunContext`, `DataHubRuntimeConnectionSettings`, `DataHubLineageRuntimeConfig`, `DatasetPlatform`.

## 2. Layer Mapping
| Class | Current Layer | Should Be Layer | Reason |
| --- | --- | --- | --- |
| `DatasetPlatform` | Domain | Domain | Enum value object for platform names. |
| `DataHubDataJobKey` | Domain | Domain | Immutable key for identifying a DataHub job. |
| `ResolvedDataHubFlowConfig` | Domain | Domain | Pure resolved metadata model with no IO. |
| `CustomProperties` | Domain | Domain | Runtime metadata value object. |
| `RunSpec` | Domain | Domain | Runtime run payload model. |
| `ActiveRunContext` | Domain | Domain | In-memory run context aggregate. |
| `DataHubRuntimeConnectionSettings` | Domain | Domain | Connection settings DTO; no side effects. |
| `DataHubLineageRuntimeConfig` | Domain | Application | Application wiring config for a lineage use case. |
| `DataHubSettings` | Infrastructure (Adapter) | Infrastructure (Adapter) | Reads env variables; configuration adapter concern. |
| `DataHubUrnFactory` | Infrastructure (Adapter) | Infrastructure (Adapter) | Wraps DataHub SDK URN types. |
| `DataProcessInstanceMcpBuilder` | Infrastructure (Adapter) | Infrastructure (Adapter) | Constructs DataHub-specific MCP payloads. |
| `DataHubGraphClient` | Infrastructure (Adapter) | Infrastructure (Adapter) | Encapsulates DataHub SDK graph read/write calls. |
| `DataHubJobMetadataResolver` | Application | Application | Application service for resolving job metadata from a gateway. |
| `DataHubRunTimeLineage` | Infrastructure (Adapter) | Infrastructure (Adapter) | Concrete adapter implementing runtime lineage gateway. |
| `DataHubLineageGatewayFactory` | Infrastructure (Adapter) | Infrastructure (Adapter) | Composition/wiring factory for concrete adapter. |

## 3. Design Pattern Audit (Per Class)
### `DatasetPlatform`
- Current Pattern: Enum value object.
- Is the name correct? Yes.
- Problems: None.
- Proposed Pattern: Keep as value object enum.
- Proposed Rename: None.
- Justification: Clear and stable.

### `DataHubDataJobKey`
- Current Pattern: Immutable parameter object.
- Is the name correct? Yes.
- Problems: None.
- Proposed Pattern: Keep as domain key object.
- Proposed Rename: None.
- Justification: Explicit contract for job identity.

### `ResolvedDataHubFlowConfig`
- Current Pattern: Immutable DTO with helper methods.
- Is the name correct? Yes.
- Problems: Helper methods depend on infra URN factory, but still return primitives.
- Proposed Pattern: Keep as resolved config DTO.
- Proposed Rename: None.
- Justification: Adequate with minimal coupling impact.

### `CustomProperties`
- Current Pattern: Mutable value object for run metadata.
- Is the name correct? Yes.
- Problems: None.
- Proposed Pattern: Keep as runtime metadata value object.
- Proposed Rename: None.
- Justification: Matches usage.

### `RunSpec`
- Current Pattern: Runtime command/state DTO.
- Is the name correct? Yes.
- Problems: None.
- Proposed Pattern: Keep as run state DTO.
- Proposed Rename: None.
- Justification: Clear intent.

### `ActiveRunContext`
- Current Pattern: Context holder.
- Is the name correct? Yes.
- Problems: None.
- Proposed Pattern: Keep as in-memory context struct.
- Proposed Rename: None.
- Justification: Clear and minimal.

### `DataHubRuntimeConnectionSettings`
- Current Pattern: Config DTO.
- Is the name correct? Yes.
- Problems: None.
- Proposed Pattern: Keep as immutable settings model.
- Proposed Rename: None.
- Justification: Stable input contract.

### `DataHubLineageRuntimeConfig`
- Current Pattern: Application config bundle.
- Is the name correct? Yes.
- Problems: None.
- Proposed Pattern: Keep config bundle.
- Proposed Rename: None.
- Justification: Composition boundary input.

### `DataHubSettings`
- Current Pattern: Configuration adapter (`from_env`).
- Is the name correct? Yes.
- Problems: None.
- Proposed Pattern: Keep as environment-backed settings adapter.
- Proposed Rename: None.
- Justification: Correct placement in infra.

### `DataHubUrnFactory`
- Current Pattern: Static factory.
- Is the name correct? Yes.
- Problems: Exposes DataHub SDK type in one method (`DatasetUrn`) if consumed externally.
- Proposed Pattern: Keep static factory, confine SDK types internally.
- Proposed Rename: None.
- Justification: Good centralization point for SDK URN assembly.

### `DataProcessInstanceMcpBuilder`
- Current Pattern: Factory (not true builder from client perspective).
- Is the name correct? No.
- Problems: Misleading pattern name; client does not incrementally build.
- Proposed Pattern: Batch MCP factory.
- Proposed Rename: `DataProcessInstanceMcpFactory`.
- Justification: Name should reflect single-shot object creation.

### `DataHubGraphClient`
- Current Pattern: Gateway adapter.
- Is the name correct? Yes.
- Problems: None major.
- Proposed Pattern: Keep as SDK gateway adapter.
- Proposed Rename: None.
- Justification: Encapsulates SDK IO and error translation.

### `DataHubJobMetadataResolver`
- Current Pattern: Application service with hidden constructor side effects.
- Is the name correct? Partially.
- Problems: Resolves metadata in `__init__` (implicit IO), making lifecycle opaque.
- Proposed Pattern: Application service with explicit `resolve()` operation.
- Proposed Rename: Keep name.
- Justification: Preserve recognizability while removing hidden IO.

### `DataHubRunTimeLineage`
- Current Pattern: Stateful runtime adapter + orchestrator.
- Is the name correct? No (`RunTime` typo/casing).
- Problems: Constructor performs network resolution indirectly; public signatures leak DataHub SDK type (`DatasetUrn`); depends directly on concrete resolver flow.
- Proposed Pattern: Infrastructure adapter implementing an application port.
- Proposed Rename: `DataHubRuntimeLineage` (retain compatibility alias).
- Justification: Correct naming, explicit initialization, better DIP compliance.

### `DataHubLineageGatewayFactory`
- Current Pattern: Factory.
- Is the name correct? Yes.
- Problems: Currently returns concrete adapter type and does not make metadata resolution step explicit.
- Proposed Pattern: Composition root factory returning application port.
- Proposed Rename: None.
- Justification: Reduces application coupling to infrastructure details.

## 4. Anti-Patterns Identified
- Work done inside `__init__` (network calls):
  - `DataHubJobMetadataResolver.__init__` triggers metadata fetch.
  - `DataHubRunTimeLineage.__init__` triggers metadata resolution through resolver construction.
- Application logic mixed with SDK code:
  - Runtime orchestration and DataHub MCP/URN concerns are mixed in one adapter class.
- Builder that is actually a factory:
  - `DataProcessInstanceMcpBuilder` behaves as a one-shot factory.
- Stateful adapter leaking infra types:
  - `add_input`/`add_output` expose `DatasetUrn` type in adapter public API.
- Hidden coupling to DataHub SDK in application layer:
  - Application-facing usage currently depends on concrete `DataHubRunTimeLineage` class instead of an abstract port.

## 5. Proposed Clean Architecture Structure
Minimal, safe split:
- Application:
  - Add `LineageRuntimeGateway` port (interface/protocol) for worker runtime lineage operations.
  - Keep `DataHubJobMetadataResolver` as application service, but make resolution explicit (`resolve()`).
- Infrastructure (Adapter):
  - `DataHubRuntimeLineage`: concrete implementation of `LineageRuntimeGateway`.
  - `DataHubGraphClient`, `DataProcessInstanceMcpFactory`, `DataHubUrnFactory`, `DataHubSettings`, `DataHubLineageGatewayFactory`.
- Domain:
  - Existing DTOs/enums (`RunSpec`, `ResolvedDataHubFlowConfig`, etc.).

Port definition (application-facing):
- `resolve_job_metadata() -> ResolvedDataHubFlowConfig`
- `start_run() -> RunSpec`
- `add_input(name, platform) -> str`
- `add_output(name, platform) -> str`
- `complete_run() -> str`
- `fail_run(error_message) -> str`
- `abort_run() -> None`
- `resolved_job_config` read-only property

ASCII dependency diagram:

```text
Worker Services (Application)
        |
        v
LineageRuntimeGateway (Port)
        |
        v
DataHubRuntimeLineage (Infra Adapter)
   |                 |
   v                 v
DataHubGraphClient   DataProcessInstanceMcpFactory
        |
        v
      DataHub SDK
```
