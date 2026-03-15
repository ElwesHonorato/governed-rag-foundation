# Pipeline Common Agent Guide

Applies to `libs/pipeline-common/`.

## Local Rules
- Treat this package as shared infrastructure/runtime API for apps and workers.
- Preserve stable import paths; when moving modules, keep package exports aligned.
- Keep startup contracts (`WorkerService`, extractor/factory contracts, runtime context) minimal and framework-agnostic.

## If You Change X, Also Update Y
- If startup contracts or constructor signatures change, update all worker app composition roots under `domains/worker_*/src/<worker_package>/app.py`.
- If startup architecture changes, update:
  - `docs/ARCHITECTURE.md`
  - `docs/patterns/composition-root.md`
  - `docs/patterns/dependency-injection.md`

## Local Commands
- Install: `cd libs/pipeline-common && poetry install`
- Sanity compile: `python3 -m compileall libs/pipeline-common/src`
- Tests (when present): `cd libs/pipeline-common && poetry run pytest`
