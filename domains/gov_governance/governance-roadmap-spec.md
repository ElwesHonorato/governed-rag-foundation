# DataHub Governance-as-Code Platform Tool

## Purpose
Provide a safe, repeatable, auditable way to manage **DataHub static governance entities** as code (Domains, Owners, Tags/Terms, Datasets, Flows/Jobs, Lineage Contracts), using a **GitOps-style** workflow:
- **Plan**: compute changes (read-only)
- **Approve**: human gate in CI
- **Apply**: reconcile desired state into DataHub (write)

This tool is intentionally **not** responsible for runtime lineage (DataProcessInstance/OpenLineage runs). It manages the **static contract layer**.

---

## Scope

### In scope
- Declarative governance definitions (YAML) as the source of truth
- Entity assembly into an immutable in-memory snapshot
- Validation and linting of governance definitions
- Diff/plan generation against current DataHub state (scoped)
- Apply/reconcile: upserts + safe deprecation of removed entities
- Reporting, CI integration, and audit-friendly output

### Out of scope
- Runtime execution telemetry (DataProcessInstance) emission
- Data quality/assertions execution (can integrate later, but not owned here)
- Ingesting metadata from external sources (dbt/spark/airflow connectors)
- Managing access policies (optional later module; not required for MVP)

---

## Core Concepts

### Desired State
A version-controlled set of YAML definitions that describes what should exist in DataHub.

### Actual State
What currently exists in DataHub for a **scoped subset** of entities managed by this tool.

### Reconciliation
A deterministic process that brings DataHub closer to desired state, via:
- Create (missing entities)
- Update (changed aspects)
- Deprecate (present in DataHub, removed from YAML) — optional and guarded
- No-op (no changes)

### Managed Scope
To avoid impacting other teams, the tool MUST operate on an explicit scope boundary:
- Entities tagged `managed-by:governance-code` (recommended), and/or
- Domain subtree (e.g., `rag-platform/*`), and/or
- Namespace prefixes (dataset name prefixes, flow name prefixes)

---

## Responsibilities and Boundaries

### 1) Definitions Layer (Inputs)
**Responsibility:** Provide a stable declarative format for governance definitions.

- Owns: YAML schema, directory layout, naming conventions, IDs
- Does not own: DataHub connectivity, diffing, apply logic

### 2) Discovery Layer
**Responsibility:** Find definition files and classify them.

- Input: `domains/gov_governance/definitions/**/*.yaml`
- Output: discovered standalone + relational files (with paths + raw dicts)
- No validation beyond structural parse

### 3) Assembly Layer
**Responsibility:** Convert discovered YAML into a normalized in-memory snapshot.

- Aggregates standalone types (domains, groups, tags, terms, datasets)
- Composes relational types (flows + jobs + lineage_contract)
- Output: immutable `GovernanceDefinitionSnapshot`

### 4) Validation Layer
**Responsibility:** Enforce correctness, completeness, and governance rules.

Examples:
- IDs unique
- All referenced IDs exist
- All assets have required fields (domain + owners)
- Lineage contracts reference known datasets/jobs/flows
- Environment/platform naming conventions

Validation must fail fast before any write operation.

### 5) State Adapter (DataHub API)
**Responsibility:** Read and write DataHub state in a controlled way.

- Reads: current aspects for scoped entities
- Writes: MCP upserts for aspects
- Optional: emits deprecation aspect when configured

This layer must be the only boundary that talks to DataHub.

### 6) Diff / Plan Engine
**Responsibility:** Compare desired snapshot vs actual scoped state and produce a plan.

Plan must be:
- deterministic
- human-reviewable
- machine-readable (JSON artifact)
- grouped by entity type and action (create/update/deprecate/no-op)

### 7) Apply Engine
**Responsibility:** Execute a plan safely.

Rules:
- Apply requires explicit flags for destructive actions (deprecations/deletes)
- Apply re-validates desired state
- Apply re-checks scope restrictions
- Apply emits in dependency order (domains → tags/terms → datasets → flows/jobs → lineage)

### 8) CLI + CI Integration
**Responsibility:** Provide user entrypoints for local and CI workflows.

Commands:
- `validate`
- `plan`
- `apply`

Outputs:
- markdown summary for PR review
- json plan artifact for automation

---

## Repo Layout (Suggested)

### Governance definitions (source of truth)

domains/gov_governance/
definitions/
domains.yaml
groups.yaml
tags.yaml
glossary.yaml
datasets/
s3.yaml
postgres.yaml
rabbitmq.yaml # optional
pipelines/
governed-rag.yaml
transforms/
mapping_rules.yaml # optional


### Tool implementation

domains/gov_governance/
src/
common/
core.py # snapshot model + assembly entrypoint
types.py # typed definitions
validation.py # validators + rules
fs.py # filesystem helpers (generic)
discovery/
discoverer.py # scans yaml, classifies
classification.py
datahub/
client.py # DataHub adapter
aspects.py # aspect builders
read.py # read scoped state
write.py # emit MCPs
plan/
diff.py # desired vs actual comparison
render.py # markdown + json output
types.py # plan model
apply/
engine.py # apply plan with ordering and guards
safeguards.py # allowlists, deprecation guards
cli/
main.py # entrypoint: validate/plan/apply


---

## Entity Model Coverage

### Supported entity types (static contract)
1. Domains
2. Groups/Owners
3. Tags + Glossary Terms
4. Datasets
5. DataFlows + DataJobs
6. Lineage contract edges (job ↔ dataset)

### Not supported (by this tool)
- DataProcessInstance (runtime runs)
- Assertions / tests execution
- External ingestion orchestration

---

## DataHub Aspects: What We Write (Production Minimum)

### Domains
- properties: name, description
- parent linkage (domain hierarchy) if applicable
- ownership (optional but recommended)

### Groups / Owners
- group info: name, description
- memberships (optional)
- ownership aspects attached to target entities

### Tags
- tag properties: name, description

### Glossary Terms
- term properties: name, definition, related terms (optional)

### Datasets
- dataset properties: name, description
- domain assignment
- ownership
- tags
- glossary terms
- schema (if known)
- custom properties: retention, SLA tier, classification notes, etc.

### Flows + Jobs
- flow info: name, description, platform, env
- job info: name, description
- ownership + domain assignment for both
- tags/terms (optional)
- custom properties (queue names, schedule, runtime tech, etc.)

### Lineage Contract Edges
- job consumes dataset(s)
- job produces dataset(s)
- optional: dataset-to-dataset edges (only if you explicitly want them)

---

## Ordering Rules (Dependency-safe Apply)
Apply in this strict order:
1) Domains
2) Groups/Owners (as entities, if you manage them)
3) Tags + Glossary Terms
4) Datasets
5) Flows + Jobs
6) Lineage contract edges

Rationale:
- Tags/Terms must exist before attaching them
- Domains should exist before assigning
- Datasets should exist before lineage edges reference them

---

## Plan / Apply Workflow

### Plan
Plan is read-only and produces:
- Markdown summary (for PR review)
- JSON plan artifact (for tooling)

Plan computes:
- Create: entity absent in DataHub scope
- Update: entity present but aspects differ
- Deprecate: entity in DataHub scope but removed from YAML (guarded)
- No-op: identical

### Approval Gate (CI)
- Plan runs on every PR
- Plan output posted as PR comment / artifact
- Apply is blocked until approval:
  - Merge approval (simple), or
  - GitHub Environments required reviewers (recommended), or
  - Manual workflow dispatch (optional)

### Apply
Apply:
- re-loads snapshot
- re-validates
- re-fetches actual scoped state
- recomputes plan (or verifies plan artifact matches)
- applies changes in dependency order

---

## Safety Requirements (Non-negotiable)

### Scope enforcement
Tool must operate ONLY on managed entities, defined by:
- required tag `managed-by:governance-code` OR
- allowlisted domain subtree OR
- allowlisted prefixes (datasets/flows)

### Destructive changes guarded
- Deprecation requires `--allow-deprecations`
- Bulk deprecation requires an additional `--allow-bulk-deprecations` or threshold override
- Hard delete is disabled by default (recommended)

### Idempotency
- Re-running apply with unchanged YAML results in no net change
- All writes are aspect upserts and should be safe to repeat

### Drift handling
Because DataHub can be changed outside the tool:
- plan/apply should detect unmanaged edits
- optionally re-attach `managed-by` tag if missing (if in scope)

---

## CLI Design

### `governance validate`
- Parses YAML
- Assembles snapshot
- Runs validation rules
- Outputs: errors and warnings

### `governance plan --env DEV --scope rag-platform`
- Reads YAML snapshot
- Fetches scoped DataHub state
- Produces plan summary + plan.json
- Exit codes:
  - 0: no changes
  - 2: changes present
  - 1: error

### `governance apply --env DEV --scope rag-platform [--allow-deprecations]`
- Runs validate + plan
- Executes plan with safeguards
- Outputs summary and applied changes

---

## Output Format (Plan Summary)

Example:
- Domains: 1 create, 0 update, 0 deprecate
- Tags: 0 create, 2 update
- Datasets: 3 create, 1 update
- Flows/Jobs: 0 create, 1 update
- Lineage: 2 edge additions, 1 edge removal (guarded)

Each change includes:
- entity urn/id
- action
- changed aspects/fields (owners/tags/domain/properties/schema)
- rationale if generated (e.g., removed from YAML)

---

## Implementation Notes (Practical Choices)

### YAML vs typed classes
- YAML is the declarative interface for humans and governance review
- Internally convert YAML to typed dataclasses for validation and apply

### Managed-by marker
Strong recommendation:
- Attach tag `managed-by:governance-code` to every entity you manage
- This becomes your safe scoping key for reads and deprecations

### Deprecation vs deletion
Default:
- Deprecate missing entities
- Never hard delete
Reason:
- preserves lineage history
- preserves auditability
- avoids breaking dependencies

---

## Future Extensions (Optional)
- Access policies as code (RBAC/ABAC) scoped by domains
- Schema evolution checks (contracts)
- Integrations:
  - dbt / Airflow / Spark ingestion consistency checks
  - OpenLineage runtime runs (separate module)
- Automated documentation enforcement (required fields per domain)

---

## Definition of Done (Current State)
- `domains/gov_governance/src/apply.py` applies governance entities: domains, groups, tags, glossary terms, datasets, flows/jobs, and lineage contract edges.
- Environment selection for apply is resolved from `DATAHUB_ENV` (operationally provided as `DEV` or `PROD`).
- CI apply workflow runs `domains/gov_governance/src/apply.py` with `DATAHUB_ENV=PROD` on pushes to `main` that touch `domains/gov_governance/**`.
- Governance definitions are loaded from YAML and assembled deterministically into a snapshot before apply.
- Re-running apply with unchanged definitions is expected to be idempotent via upsert semantics.

Not currently implemented:
- Dedicated `validate` command.
- Dedicated `plan` command and plan artifact output in CI.
- Scoped reads/writes enforced via `managed-by:governance-code`.
- Deprecation workflow behind explicit flags.

---

## Design Principles
- Declarative inputs, deterministic outputs
- Safe by default (no destructive changes without explicit intent)
- Clear boundaries between concerns
- Auditable and reviewable changes
- Scoped operation (never global)
