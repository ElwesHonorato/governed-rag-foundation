# infra_storage domain

This domain is the artifact backbone of the RAG pipeline. Every worker reads and writes document artifacts here as processing advances through stages.

## Deep Dive

### What runs here
- `minio` (`minio/minio@sha256:14cea493d9a34af32f524e538b8346cf79f3321eff8e708c1e2960462bd8936e`)

### How it contributes to RAG
- Stores stage artifacts in object storage, including:
  - `01_incoming/`
  - `02_raw/`
  - `03_processed/`
  - `04_chunks/`
  - `05_embeddings/`
  - `06_indexes/`
  - `07_metadata/`
- Serves as the persistent handoff medium across workers.

### Runtime dependencies
- Credentials via `MINIO_ROOT_USER`, `MINIO_ROOT_PASSWORD`.
- Persistent local data under `localdata/minio`.

### Interface
- S3-compatible API on `${MINIO_API_PORT}:9000`.
- MinIO console on `${MINIO_CONSOLE_PORT}:9001`.
