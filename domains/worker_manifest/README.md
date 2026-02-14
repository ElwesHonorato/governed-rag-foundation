# worker_manifest domain

This domain creates per-document status snapshots. It gives you a clear view of which pipeline stages have produced artifacts for each document.

## Deep Dive

### Stage responsibility
- Scans processed documents in `03_processed/`.
- Checks stage artifact existence across:
  - `03_processed/`
  - `04_chunks/`
  - `05_embeddings/`
  - `06_indexes/`
- Writes manifest status to `07_metadata/manifest/{doc_id}.json`.

### Manifest output
- Includes `doc_id`, stage booleans, `attempts`, and `last_error`.

### Runtime dependencies
- Storage only: `S3_ENDPOINT`, `S3_ACCESS_KEY`, `S3_SECRET_KEY`.

### Operational notes
- Service container: `pipeline-worker-manifest`.
- Polling interval configured in `domains/worker_manifest/src/configs/constants.py`.
