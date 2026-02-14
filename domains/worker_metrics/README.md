# worker_metrics domain

This domain emits pipeline throughput counters. It is the lightweight observability loop that tells you how many artifacts exist at each stage.

## Deep Dive

### Stage responsibility
- Periodically lists objects in stage prefixes:
  - `03_processed/`
  - `04_chunks/`
  - `05_embeddings/`
  - `06_indexes/`
- Computes stage counts (processed docs, chunks, embedding artifacts, indexed artifacts).
- Emits counters through shared observability utilities.

### Runtime dependencies
- Storage only: `S3_ENDPOINT`, `S3_ACCESS_KEY`, `S3_SECRET_KEY`.

### Operational notes
- Service container: `pipeline-worker-metrics`.
- Polling interval configured in `domains/worker_metrics/src/configs/constants.py`.
