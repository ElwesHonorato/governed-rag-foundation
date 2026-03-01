# Runtime DataHub Lineage – Architecture Review (Purist Clean Architecture Critique)

This document intentionally applies a **strict / purist** Clean Architecture lens. It highlights what a “Clean Architecture purist” would criticize in the current design and in the proposed refactor, even if some choices are pragmatic for production.

---

## 1. Current Responsibilities

This module currently:
- Builds DataHub URNs for flows, jobs, datasets, and process instances.
- Reads DataJob metadata (`DataJobInfo`) from DataHub to resolve runtime config.
- Emits runtime lineage MCPs (`DataProcessInstance*` + run event).
- Tracks per-run state (inputs, outputs, status transitions).
- Exposes a factory used by workers to construct the lineage gateway.

**Purist critique (high level):**
- The module mixes **Use Case orchestration** (“run session lifecycle”) with **Framework/Driver details** (DataHub SDK types and MCP aspects).
- There is no explicit **port boundary** between Application and Infrastructure; callers risk depending on DataHub-centric behaviors and types.

---

## 2. Dependency Rule (Purist Version)

**Clean Architecture dependency rule:**
- Source code dependencies must point **inward**.
- **Entities (Domain)** should depend on nothing outside Domain.
- **Use Cases (Application)** should depend only on Domain + Ports (interfaces).
- **Interface Adapters / Infrastructure** depend on SDKs, HTTP clients, and frameworks.
- Frameworks and drivers (DataHub SDK, requests) must be isolated at the boundary.

**Purist critique:**
- Any Domain or Application code importing DataHub schema classes, URNs, MCP wrappers, `requests`, or the DataHub graph client is a violation.
- “Helper methods” in Domain that rely on infra factories—even if they return strings—still violate dependency direction.

---

## 3. Layer Mapping (Purist)

| Class / Component | Current Layer | Should Be Layer | Purist Reason |
| --- | --- | --- | --- |
| `DatasetPlatform` | Domain | Domain | Value object. |
| `DataHubDataJobKey` | Domain | Domain | Identity object; must be infra-agnostic. |
| `ResolvedDataHubFlowConfig` | Domain | Domain | Must be pure; must not call URN factories or DataHub helpers. |
| `CustomProperties` | Domain | Domain | Value object. |
| `RunSpec` | Domain | Domain | Domain/application DTO; must remain infra-free. |
| `ActiveRunContext` | Domain | Application (or Domain) | Purist may argue “active context” is use-case state, not an entity. |
| `DataHubRuntimeConnectionSettings` | Domain | Infrastructure (or Application config) | Purist: connection settings are *drivers* concerns, not domain. |
| `DataHubLineageRuntimeConfig` | Application | Application | Use-case wiring config. |
| `DataHubSettings` | Infrastructure | Infrastructure | Environment/config adapter. |
| `DataHubUrnFactory` | Infrastructure | Infrastructure | DataHub URNs are driver details; must not leak inward. |
| `DataProcessInstanceMcpFactory` | Infrastructure | Infrastructure | Builds DataHub-specific payloads. |
| `DataHubGraphClient` | Infrastructure | Infrastructure | SDK facade. |
| `DataHubJobMetadataResolver` | Mixed | Application + Port | Should use a port for reads; must not do IO in `__init__`. |
| `DataHubRuntimeLineage` | Mixed | Split: Application session + Infra writer | Current class mixes use-case state with SDK emission. |
| `DataHubLineageGatewayFactory` | Infrastructure | Composition Root / Bootstrap | Purist: factories that wire dependencies belong at the edge, not shared core libs unless explicitly “bootstrap”. |

**Key purist point:**
- Anything that contains **server/token/timeouts** is not Domain. It belongs to **Infrastructure** or “Frameworks & Drivers config”.

---

## 4. Design Pattern Audit (Purist)

### `DataProcessInstanceMcpFactory`
- Current Pattern: Builder/Assembler of MCP batches.
- Purist critique: The name “Builder” is okay, but this is purely an **Infrastructure assembler** and must not be referenced by Application code. If Application references it, it leaks driver details.
- Proposed Pattern: Keep as **Assembler** or rename to `DataProcessInstanceMcpAssembler` (purist preference: name describes domain action rather than GoF term).
- Proposed Rename: `DataProcessInstanceMcpAssembler` (optional).

### `DataHubGraphClient`
- Current Pattern: Facade over DataHub SDK.
- Purist critique: Still fine, but it must implement ports rather than be depended upon directly by Application services.
- Proposed Pattern: Adapter implementing `LineageReadPort` / `LineageWritePort`.

### `DataHubJobMetadataResolver`
- Current Pattern: Resolver (Application service).
- Purist critique:
  - Must not do network IO in `__init__`.
  - Should depend on `JobMetadataPort` (read port), not on `DataHubGraphClient`.
- Proposed Pattern: Use-case interactor reading from a port.

### `DataHubRuntimeLineage`
- Current Pattern: Stateful session + adapter.
- Purist critique (strong):
  - This is doing two jobs: Use-case/session state and Infrastructure writes.
  - It leaks driver vocabulary (DataHub) into the Application API.
  - It constructs its own dependencies (graph client, resolver) rather than receiving ports (violates DIP).
- Proposed Pattern:
  - Application: `LineageRunSession` (stateful use-case/session)
  - Infrastructure: `DataHubLineageWriter` (stateless adapter emitting events)

### `DataHubUrnFactory`
- Current Pattern: Factory.
- Purist critique:
  - If Domain objects call this, it’s a hard dependency inversion violation.
  - URN construction belongs in Infrastructure adapter.
- Proposed Pattern: Keep as Infra-only helper.

### “Factory used by workers”
- Purist critique:
  - Any “factory” that wires concrete implementations is **composition root** work.
  - Composition root should be in the worker entrypoint, not deep inside shared libs (unless clearly a `bootstrap` package).
- Purist preference: Replace `DataHubLineageGatewayFactory` with a composition-root function in `domains/worker_x/app.py`.

---

## 5. Anti-Patterns Identified (Purist Severity)

### S1 — Dependency Direction Violations (DIP broken)
- Domain or Application objects calling `DataHubUrnFactory` or using DataHub SDK types (even indirectly).
- Application-level runtime orchestration importing DataHub schema classes.

### S2 — Hidden IO in Constructors
- `DataHubJobMetadataResolver.__init__` triggers network reads.
- `DataHubRuntimeLineage.__init__` triggers resolution/graph interactions.

### S2 — Mixed Responsibilities (God Class tendencies)
- `DataHubRuntimeLineage` does: lifecycle, state, URN creation, dataset property emission, MCP assembly, and graph emissions.

### S3 — Leaky Public API
- `add_input/add_output` returning `DatasetUrn` ties callers to DataHub SDK.
- Public API should return primitives or domain value objects not tied to a vendor SDK.

---

## 6. Purist “Ideal” Clean Architecture Structure

A strict Clean Architecture split would look like this:

### Domain (Entities / Value Objects)
- `DatasetPlatform`
- `DataHubDataJobKey` (purist might rename to `JobKey` and move DataHub naming outward)
- `ResolvedFlowConfig` (vendor-neutral)
- `RunSpec`, `CustomProperties`

**Rule:** Domain must not know “DataHub”, “MCP”, “URN”.

### Application (Use Cases)
- `LineageRunSession` (state machine: start/add/complete/fail)
- `ResolveJobMetadataUseCase` (explicit call)

**Ports (interfaces) defined here:**
- `LineageWriterPort` (emit run events + IO edges)
- `JobMetadataReaderPort` (fetch custom properties/config)
- `UrnTranslatorPort` (optional, if you want URN building as a service)

### Infrastructure (Adapters)
- `DataHubLineageWriterAdapter` implements `LineageWriterPort`
- `DataHubJobMetadataReaderAdapter` implements `JobMetadataReaderPort`
- `DataHubUrnFactory` stays here
- `DataProcessInstanceMcpAssembler` stays here
- `DataHubGraphClient` stays here

### Composition Root (Worker Entrypoint)
- Reads env settings
- Instantiates adapters
- Injects them into use cases
- Starts worker loop

---

## 7. Minimal Refactor vs Purist Refactor

### Minimal Refactor (Pragmatic)
- Add `LineageRuntimeGateway` port.
- Keep `DataHubRuntimeLineage` as adapter implementing the port.
- Remove IO from constructors where possible (explicit `.resolve()`).
- Stop returning SDK types in public API (`DatasetUrn` → `str`).

**Purist critique:** Still couples use-case/session to vendor naming and may keep some driver assumptions in the gateway.

### Purist Refactor (Strict)
- Split `DataHubRuntimeLineage` into:
  - Application: `LineageRunSession`
  - Infrastructure: `DataHubLineageWriterAdapter`
- Move all URN/MCP/SDK concerns exclusively into Infra.
- Composition root wires everything.

**Purist benefit:** Perfect DIP and layer boundaries.

**Purist cost:** More files, more indirection, bigger diff.

---

## 8. Revised Proposed Clean Architecture Structure (Purist-Compatible, Still Minimal)

This is a compromise that satisfies purists on the biggest violations while keeping changes reasonable:

1) Rename and constrain infra types:
- `DataHubRuntimeLineage` → `DataHubRuntimeLineageAdapter`
- `DataProcessInstanceMcpFactory` → `DataProcessInstanceMcpAssembler` (optional)

2) Introduce ports in Application:
- `JobMetadataReaderPort`
- `LineageRuntimePort` (or `LineageWriterPort` + session use-case)

3) Make IO explicit:
- `DataHubJobMetadataResolver.resolve()` instead of doing work in `__init__`.

4) Remove SDK types from outward-facing methods:
- `add_input/add_output` return `str` URNs only (or a domain `DatasetRef` value object that is vendor-neutral).

---

## 9. Dependency Diagram (Purist)

```text
[Worker Entrypoint / Composition Root]
        |
        v
[Application Use Cases / Session]
  |                 |
  v                 v
[Ports: JobMetadataReaderPort, LineageWriterPort]
        |
        v
[Infrastructure Adapters]
  |                 |
  v                 v
DataHubGraphClient  MCP Assembler / URN Factory
        |
        v
      DataHub SDK / HTTP
```

## 10. What Must Not Change (Stability Promise)

Even under a purist refactor, preserve:

MCP ordering and aspect semantics

Run lifecycle semantics (STARTED, COMPLETE, FAILURE)

Dataset properties emission behavior (if relied upon)

URN formats

Error handling behavior (warnings vs hard-fail) unless explicitly justified

## 11. Summary of Purist Criticism

A strict Clean Architecture purist would say:

“Your domain and application layers still speak DataHub.”

“IO in constructors is unacceptable.”

“A stateful session class must not import SDK types.”

“The composition root should be the only place wiring concrete implementations.”

The revised structure above addresses the major violations while allowing a pragmatic path forward.
