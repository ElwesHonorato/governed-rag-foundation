# Logging and Tracing

## Intent
Provide actionable operational visibility through structured logs and lineage events.

## When To Use
- Every worker service loop and processing path.
- Any stage that reads/writes storage objects or pushes queue messages.

## How To Apply
1. Use module-level `logger = logging.getLogger(__name__)`.
2. Log key identifiers (`storage_key`, `doc_id`, `stage`) at meaningful boundaries.
3. Emit lineage input/output datasets for each processing unit.
4. Record completion/failure in lineage consistently.

## Example
- `start_run()` before processing.
- `add_input()` and `add_output()` around storage transitions.
- `complete_run()` on success; `fail_run()`/`abort_run()` on failure.

## Anti-Patterns
- Logging without identifiers.
- Emitting lineage only on success paths.
- Duplicating verbose logs on hot paths without value.

## Notes
- Log format is not globally standardized yet. TODO: define a repo-wide structured logging schema.
