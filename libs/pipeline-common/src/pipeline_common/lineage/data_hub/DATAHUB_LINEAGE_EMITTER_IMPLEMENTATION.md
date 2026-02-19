# DataHub Lineage Emitter Implementation Guide

## Goal
Implement a DataHub emitter in `pipeline_common/lineage/data_hub` using the working model in `datahub_migration/minimal_datahub_test.py`.

Reference implementation model:
- `datahub_migration/minimal_datahub_test.py`

## Scope Clarification
This implementation does not need to preserve the legacy OpenLineage worker method contract.
Primary objective: refactor the tested DataHub run-emission model into a reusable class that workers can adopt.

## Pattern to Follow From `minimal_datahub_test.py`
The implementation model that currently works against local DataHub is:
1. Upsert datasets before run/lineage updates.
2. Upsert static templates (`DataFlow`, `DataJob`).
3. Emit one `DataProcessInstance` per run via MCPs.
4. Attach per-run inputs/outputs on DPI aspects.
5. Emit run events (`STARTED`, `COMPLETE`; `FAILED` on failure path).

## DataHub Entity Mapping
Use these mappings in `data_hub/lineage.py`:
1. Emitter runtime job identity -> `DataFlow` + `DataJob`.
2. One call to `start_run`/`complete_run` -> one `DataProcessInstance` URN.
3. `add_input` / `add_output` datasets -> `DataProcessInstanceInput` / `DataProcessInstanceOutput` edges.
4. `complete_run` -> `DataProcessInstanceRunEvent(status=COMPLETE)`.
5. `fail_run` -> `DataProcessInstanceRunEvent(status=FAILED)` and include error metadata in properties/custom facets where appropriate.

## SDK Constraints (Critical)
These are required with the currently installed SDK and must be implemented exactly:
1. `DataProcessInstancePropertiesClass` requires `created=AuditStampClass(...)`.
2. `DataProcessInstanceRelationshipsClass` requires `upstreamInstances` (use `[]` when none).
3. `dataProcessInstanceInput` and `dataProcessInstanceOutput` aspects must be class instances:
   - `DataProcessInstanceInput`
   - `DataProcessInstanceOutput`
   Do not pass raw dicts as MCP aspects.
4. Dataset lineage mutation can fail if dataset entities do not exist; upsert first.

## Run ID Rules
Follow the proven uniqueness pattern from the test:
1. Include current timestamp (ms).
2. Include UUID suffix.

Example shape:
- `{timestamp_ms}-{stage}-{uuid4}`

## Recommended Internal Structure
Inside `libs/pipeline-common/src/pipeline_common/lineage/data_hub/`:
1. `contracts.py`
2. `constants.py`
3. `lineage.py`
4. `__init__.py`

Suggested helpers inside `lineage.py`:
1. `_init_lineage_settings(...)`
2. `_init_lineage_config(...)`
3. `_init_run_state()`
4. `_ensure_datasets_exist(...)`
5. `_ensure_flow_and_job(...)`
6. `_emit_dpi_aspects(...)`
7. `_run_event(status, ...)`

## Separation of Responsibilities
Match the existing style in `open_lineage/lineage.py`:
1. Public methods manage workflow/state transitions.
2. Private helpers perform validation, normalization, and external I/O.
3. Validation errors raise `ValueError`.
4. External emission failures are best-effort and logged as warnings.

## Implementation Notes for Future Worker Adoption
1. Provide a class-oriented API centered on explicit run specs and job identity.
2. Keep DataHub concerns explicit: dataset upsert, DataFlow/DataJob template upsert, DPI aspect emission.
3. Keep the class importable from worker domains without requiring CLI behavior.
4. Keep CLI wrapper thin; business logic should live in class methods.

## Validation Strategy
Use `datahub_migration/minimal_datahub_test.py` behavior as baseline acceptance:
1. Fanout producer run emits two chunk outputs from one input.
2. Same consumer job emits two distinct runs with different IO sets.
3. All runs are represented as separate `DataProcessInstance` entities.
4. No constructor/aspect runtime errors from SDK types.

## Done Criteria
1. DataHub emitter can be swapped into workers without changing worker service code.
2. Fanout multi-run scenario remains represented as separate run-level records.
3. SDK-required fields and types are handled correctly.
4. Emission failures do not break worker processing loops.
