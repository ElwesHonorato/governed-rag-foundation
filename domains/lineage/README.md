# lineage domain

This domain is the RAG system's memory for "what happened and when." It lets you inspect pipeline activity and understand data movement across stages.

## Deep Dive

### What runs here
- `postgres` (metadata database)
- `marquez` (lineage API)
- `marquez-web` (lineage UI)

### How it contributes to RAG
- Stores lineage records for pipeline operations.
- Helps trace document processing through stages.
- Supports debugging and governance audits.

### Runtime dependencies
- Postgres credentials and DB settings: `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`.
- Marquez config file: `domains/lineage/marquez.yml`.

### Interface
- Postgres on `${POSTGRES_PORT}:5432`.
- Marquez API on `${MARQUEZ_API_PORT}:5000`.
- Marquez Web UI on `${MARQUEZ_WEB_PORT}:3000`.
- Persists DB data under `localdata/postgres`.
