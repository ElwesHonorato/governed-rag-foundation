# Composition Root

## Intent
Centralize concrete wiring in one place so startup behavior is predictable and testable.

## When To Use
- Any worker/domain entrypoint (`domains/worker_*/src/<worker_package>/app.py`).
- Any place that reads env/config and constructs runtime dependencies.

## How To Apply
1. Keep `app.py` limited to orchestration (`run()` plus `main()`).
2. Keep package-level `__main__.py` limited to a guarded delegate to `app.main()`.
3. Build settings/config in the entrypoint.
4. Construct shared runtime factory/context.
5. Inject extractor/factory/service collaborators.
6. Extract config, build the service, and start it.

## Example
Good shape:
- `run()` creates `RuntimeContextFactory(...)` from env settings.
- `run()` extracts typed config, builds the worker service, and calls `serve()`.
- Business logic remains in `services/` and `startup/` modules, not in `app.py`.

## Anti-Patterns
- Parsing job config directly inside the worker loop.
- Building queue/storage/lineage clients deep inside service methods.
- Duplicating startup wiring logic across multiple files.

## Notes
- If startup signatures change in `libs/pipeline-common`, all worker composition roots must be updated together.
