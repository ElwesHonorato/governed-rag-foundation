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

## How To Use Lineage

### Required worker settings
- `MARQUEZ_LINEAGE_URL` must point to Marquez lineage endpoint, usually `http://marquez:5000/api/v1/lineage`.
- Job namespace is defined per worker in `*_LINEAGE_CONFIG.namespace` (commonly `governed-rag`).
- Dataset namespace should be defined once per worker in `*_LINEAGE_CONFIG.dataset_namespace` (for example `s3://rag-data`).
- Each worker defines a typed lineage config object (`*_LINEAGE_CONFIG`) and passes it to `LineageEmitter`:
  - `job_stage`
  - `producer`

### Important Marquez Dataset Namespace Bug
- Do not use dataset namespaces containing `://` (for example `s3://rag-data`) when you need dataset-root lineage pages in Marquez UI.
- In this stack, Marquez can return `500` for dataset lineage queries with such namespaces (`IllegalStateException: No match available`), even when ingestion succeeds.
- Use a canonical plain namespace string instead (for example `rag-data`), and keep object keys in dataset `name`.
- Safe pattern:
  - `namespace`: `rag-data`
  - `name`: `01_incoming/...`, `02_raw/...`, `03_processed/...`
- If old history exists under `s3://...`, those dataset URLs may keep failing. Re-emit lineage under the canonical namespace.

### UI usage
- Open Marquez Web UI (usually `http://localhost:${MARQUEZ_WEB_PORT}`).
- For jobs and runs, use the namespace configured in `*_LINEAGE_CONFIG.namespace`.
- For datasets, use the configured worker lineage dataset namespace.

### Known fan-out lineage investigation
- Investigation docs and replay payloads:
  - `domains/lineage/docs/marquez_fanout_lineage_bug_investigation`
- Focus: multi-run fan-out behavior where earlier chunk lineage may appear disconnected after later chunk runs.
- Upstream issue opened after investigation:
  - https://github.com/MarquezProject/marquez/issues/3093

Reason:
- Job namespace comes from each worker lineage config object (`*_LINEAGE_CONFIG.namespace`).
- Dataset namespace should come from one canonical worker config value (`*_LINEAGE_CONFIG.dataset_namespace`).
  - Dataset entries may provide only `name` when they use the canonical namespace.
  - Use explicit `namespace` only for intentional cross-namespace lineage (for example S3 input to Postgres output).

### Cross-namespace dataset example
```python
lineage.start_run()
lineage.add_input({"namespace": "s3://rag-data", "name": "02_raw/html/"})
lineage.add_output(
    {
        "namespace": "postgres://pg-prod:5432",
        "name": "rag.parsed_documents",
        "facets": {
            "schema": {
                "_producer": "https://github.com/ElwesHonorato/governed-rag-foundation",
                "_schemaURL": "https://openlineage.io/spec/facets/1-0-0/SchemaDatasetFacet.json",
                "fields": [{"name": "doc_id", "type": "VARCHAR"}],
            }
        },
    }
)
```

### API usage
- List namespaces:
```bash
curl -fsS "http://localhost:${MARQUEZ_API_PORT}/api/v1/namespaces"
```
- List jobs in lineage namespace:
```bash
curl -fsS "http://localhost:${MARQUEZ_API_PORT}/api/v1/namespaces/governed-rag/jobs"
```
- Search by chunk hash:
```bash
curl -fsS "http://localhost:${MARQUEZ_API_PORT}/api/v1/search?q=<chunk_hash>"
```

### Lineage query tooling (Marquez-only)
- Script entrypoint:
```bash
python3 scripts/lineage/lineage.py --help
```
- Make targets:
```bash
make lineage-help
make lineage-namespaces
make lineage-jobs
make lineage-datasets
make lineage-search q=<text>
make lineage-chunk q=<chunk_id>
```

### Query a specific chunk
- Query via script:
```bash
python3 scripts/lineage/lineage.py chunk <chunk_hash>
```
- Or:
```bash
make lineage-chunk q=<chunk_hash>
```
- If search returns no results, that chunk hash is not present in Marquez lineage metadata for the queried namespaces.
