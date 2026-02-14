# worker_scan domain

This domain is the pipeline starter. It watches incoming documents, moves valid files into the raw stage, and kicks off asynchronous processing.

## Deep Dive

### Stage responsibility
- Reads from `01_incoming/`.
- Moves accepted files to `02_raw/`.
- Enqueues parse jobs to `q.parse_document`.

### File selection behavior
- Only processes keys matching configured extensions (default `.html`).
- Skips keys that do not match prefix/suffix rules.

### Runtime dependencies
- `BROKER_URL` for queue publishing.
- `S3_ENDPOINT`, `S3_ACCESS_KEY`, `S3_SECRET_KEY` for object storage operations.
- Config constants in `domains/worker_scan/src/configs/constants.py`.

### Operational notes
- Service container: `pipeline-worker-scan`.
- Queue contract stage: `scan`.
