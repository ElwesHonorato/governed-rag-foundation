# DataHub Lineage Emitter Implementation Guide

## Purpose
Define a DataHub lineage emitter class that follows the same public contract, organization, and style as `open_lineage/lineage.py`, so workers can switch backends without changing call sites.

## Patterns Observed in `open_lineage/lineage.py`
1. Public API is worker-oriented and stateful per run.
2. Input validation is explicit and early (`ValueError` for bad config or payload shape).
3. Emission is best-effort: network/IO failures are logged as warnings, not raised.
4. Helpers are separated by responsibility:
   - init helpers (`_init_*`)
   - payload/data normalization helpers (`_dataset`, `_run_facets`, namespace canonicalization)
   - transport helper (`_post`)
5. Naming is explicit and consistent (`start_run`, `complete_run`, `fail_run`, `add_input`, `add_output`).
6. Types are concrete (`TypedDict`, `Mapping[str, Any]`, `dict[str, Any]`, `list[...]`).
7. JSON serialization is deterministic (`sort_keys=True`, `ensure_ascii=True`).

## Required Compatibility Contract
The DataHub class should preserve these methods and semantics:
- `start_run(job_stage=None, run_facets=None)`
- `complete_run()`
- `fail_run(error_message, run_id=None)`
- `reset_io()`
- `set_run_facets(run_facets)`
- `add_input(dataset)`
- `add_output(dataset)`
- `producer` attribute must remain available (workers reference it when building facets).

This ensures existing worker code in `domains/*/services/*` remains unchanged.

## Proposed File Organization
Inside `libs/pipeline-common/src/pipeline_common/lineage/data_hub/`:
1. `constants.py`
2. `contracts.py`
3. `lineage.py`
4. `__init__.py`

Keep the same separation style used by `open_lineage`.

## Class Design
`DataHubLineageEmitter` ( within `data_hub/lineage.py`)
Responsibilities:
1. Maintain per-run in-memory state (`run_id`, `inputs`, `outputs`, `run_facets`).
2. Normalize dataset descriptors and facet metadata.
3. Translate in-memory state into DataHub SDK calls.
4. Emit lifecycle events in a best-effort way.

Suggested state:
- `server` or `lineage_url`
- `namespace`
- `producer`
- `timeout_seconds`
- `job_stage`
- `dataset_namespace`
- `run_id`
- `run_facets`
- `inputs`
- `outputs`

## DataHub Emission Model
Unlike OpenLineage event POSTs, DataHub SDK lineage updates are entity/aspect updates.

Recommended flow:
1. `start_run(...)`
   - set `job_stage` if provided
   - generate `run_id`
   - store run facets
2. `add_input(...)` / `add_output(...)`
   - collect normalized datasets
3. `complete_run()`
   - ensure all involved datasets exist using SDK `Dataset` + `client.entities.upsert(...)`
   - add lineage edges from each input to each output via `client.lineage.add_lineage(...)`
   - optional: write run metadata aspect/facets if required
4. `fail_run(...)`
   - best-effort logging and optional failure annotation for the run/job

For initial parity with current worker expectations, input->output edge creation on `complete_run()` is the critical behavior.

## Normalization Rules to Mirror
1. Dataset namespace fallback:
   - use dataset-provided namespace when present
   - otherwise use configured `dataset_namespace`
   - raise if still missing
2. Dataset name must be non-empty.
3. Preserve canonicalization behavior for S3-style namespaces (`rstrip('/')`).
4. Validate `run_facets` payload shape similarly to existing implementation.

## Error Handling Rules
1. Configuration/data contract violations raise `ValueError`.
2. Network/DataHub client failures during emit are logged with `logger.warning` and do not crash worker loops.
3. Keep warnings actionable (include operation and key identifiers).

## Style Requirements
1. Use dataclass with explicit init path (`@dataclass(init=False)`) if mirroring exactly.
2. Keep methods small and single-purpose.
3. Keep helper names private with `_` prefix.
4. Keep docstrings brief and operational.
5. Keep typing precise and consistent with current package.

## Suggested Incremental Implementation Plan
1. Create `data_hub/contracts.py` with a config dataclass matching existing fields.
2. Implement `data_hub/lineage.py` with same public API as OpenLineage class.
3. Add internal DataHub SDK client initialization from settings.
4. Implement dataset upsert + edge creation path on `complete_run()`.
5. Keep `open_lineage` and `data_hub` importable independently.
6. Add compatibility export in `pipeline_common/lineage` layer only after DataHub emitter is stable.

## Tests to Add
1. Unit tests for config and dataset validation.
2. Unit tests ensuring `start_run` resets state and generates `run_id`.
3. Unit tests for `complete_run` creating expected edge pairs.
4. Unit tests for best-effort behavior when DataHub client raises exceptions.
5. Regression tests confirming existing worker service calls still function against the same method names.

## Done Criteria
1. Workers can instantiate and use DataHub emitter without code changes to service logic.
2. One input to N outputs and fanout chaining scenarios emit correct lineage edges.
3. Failures in DataHub emission do not break worker processing loops.
4. Tests cover public API contract and edge emission behavior.
