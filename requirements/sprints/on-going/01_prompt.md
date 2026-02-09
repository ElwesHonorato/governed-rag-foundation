## Implementation Plan: Multi-Worker Pipeline (Clear Read/Write Boundaries)

### 1. Goal
Replace the single monolithic pipeline worker process with fully isolated worker applications, one codebase and one container image per stage worker, with one explicit read source and one explicit write target per stage, aligned to `requirements/sprints/on-going/01_html-s3-weaviate-vertical-slice-epic.md`.

### 2. Stage-by-Stage Data Flow (Source -> Destination)

| Stage | Worker | Reads From | Writes To | Next Queue |
|---|---|---|---|---|
| 1 | `worker_scan` | `s3://<bucket>/01_incoming/*.html` | `s3://<bucket>/02_raw/<filename>.html` | `q.parse_document` |
| 2 | `worker_parse_document` | `s3://<bucket>/02_raw/*.html` | `s3://<bucket>/03_processed/<doc_id>.json` | `q.chunk_text` |
| 3 | `worker_chunk_text` | `s3://<bucket>/03_processed/*.json` | `s3://<bucket>/04_chunks/<doc_id>.chunks.json` | `q.embed_chunks` |
| 4 | `worker_embed_chunks` | `s3://<bucket>/04_chunks/*.chunks.json` | `s3://<bucket>/05_embeddings/<doc_id>.embeddings.json` | `q.index_weaviate` |
| 5 | `worker_index_weaviate` | `s3://<bucket>/05_embeddings/*.embeddings.json` | Weaviate upsert by `chunk_id` | optional `q.verify_index` |
| 6 | `worker_manifest` | stage events + existing manifest | `s3://<bucket>/07_metadata/manifest/<doc_id>.json` | none |
| 7 | `worker_metrics` | counters/events from workers | metrics/log sink | none |

### 2.1 Container Isolation Rule
Each worker runs as its own dedicated container service from its own dedicated codebase and Docker image. One container service maps to one worker only, and no service executes multiple worker roles.

### 2.2 Container Service Mapping

| Container Service | Worker App Path | Image | Consumes Queue | Reads From | Writes To |
|---|---|---|---|---|---|
| `pipeline-worker-scan` | `domains/worker_scan` | `governed-rag/worker-scan` | none (polling) | `s3://<bucket>/01_incoming/*.html` | `s3://<bucket>/02_raw/<filename>.html` |
| `pipeline-worker-parse-document` | `domains/worker_parse_document` | `governed-rag/worker-parse-document` | `q.parse_document` | `s3://<bucket>/02_raw/*.html` | `s3://<bucket>/03_processed/<doc_id>.json` |
| `pipeline-worker-chunk-text` | `domains/worker_chunk_text` | `governed-rag/worker-chunk-text` | `q.chunk_text` | `s3://<bucket>/03_processed/*.json` | `s3://<bucket>/04_chunks/<doc_id>.chunks.json` |
| `pipeline-worker-embed-chunks` | `domains/worker_embed_chunks` | `governed-rag/worker-embed-chunks` | `q.embed_chunks` | `s3://<bucket>/04_chunks/*.chunks.json` | `s3://<bucket>/05_embeddings/<doc_id>.embeddings.json` |
| `pipeline-worker-index-weaviate` | `domains/worker_index_weaviate` | `governed-rag/worker-index-weaviate` | `q.index_weaviate` | `s3://<bucket>/05_embeddings/*.embeddings.json` | Weaviate upsert by `chunk_id` |
| `pipeline-worker-manifest` | `domains/worker_manifest` | `governed-rag/worker-manifest` | stage event stream | stage events + existing manifest | `s3://<bucket>/07_metadata/manifest/<doc_id>.json` |
| `pipeline-worker-metrics` | `domains/worker_metrics` | `governed-rag/worker-metrics` | metrics event stream | counters/events from workers | metrics/log sink |

### 3. Single-Writer Ownership Rules
1. Only `worker_scan` writes `02_raw/`.
2. Only `worker_parse_document` writes `03_processed/`.
3. Only `worker_chunk_text` writes `04_chunks/`.
4. Only `worker_embed_chunks` writes `05_embeddings/`.
5. Only `worker_index_weaviate` writes Weaviate.
6. Only `worker_manifest` writes `07_metadata/manifest/`.

### 4. Generic Parsing Design (Future File Types)
1. Name parsing stage worker `worker_parse_document` (not HTML-specific).
2. Add parser registry in `domains/worker_parse_document/src/parsing/registry.py` to select parser by extension/content-type.
3. Implement `domains/worker_parse_document/src/parsing/html_parser.py` now.
4. Add future parsers later (`pdf_parser.py`, `docx_parser.py`, `txt_parser.py`) without changing stage flow.
5. Output from parsing remains the same canonical contract in `03_processed/`.

### 5. Contracts
1. Document contract (`03_processed`): `doc_id`, `source_key`, `source_type`, `timestamp`, `security_clearance`, `title`, `text`.
2. Chunk contract (`04_chunks`): `chunk_id`, `doc_id`, `chunk_index`, `chunk_text`, metadata.
3. Embedding contract (`05_embeddings`): `chunk_id`, `vector`, metadata (`source_type`, `timestamp`, `security_clearance`, `doc_id`, `source_key`, `chunk_index`).
4. Deterministic ID: `chunk_id = hash(doc_id + chunk_index + chunk_text)`.

### 6. Repository Layout
```text
domains/app/
  docker-compose.yml
  app/
    Dockerfile
    pyproject.toml
    src/
    tests/

domains/worker_scan/
  docker-compose.yml
  app/
    Dockerfile
    pyproject.toml
    src/
    tests/

domains/worker_parse_document/
  docker-compose.yml
  app/
    Dockerfile
    pyproject.toml
    src/
      parsing/
        base.py
        registry.py
        html_parser.py
    tests/

domains/worker_chunk_text/
  docker-compose.yml
  app/
    Dockerfile
    pyproject.toml
    src/
    tests/

domains/worker_embed_chunks/
  docker-compose.yml
  app/
    Dockerfile
    pyproject.toml
    src/
    tests/

domains/worker_index_weaviate/
  docker-compose.yml
  app/
    Dockerfile
    pyproject.toml
    src/
    tests/

domains/worker_manifest/
  docker-compose.yml
  app/
    Dockerfile
    pyproject.toml
    src/
    tests/

domains/worker_metrics/
  docker-compose.yml
  app/
    Dockerfile
    pyproject.toml
    src/
    tests/

libs/pipeline-common/
  pyproject.toml
  src/pipeline_common/
    s3/
    queue/
    contracts/
    observability/
    weaviate/
  tests/
```

### 7. Runtime and Compose Changes
1. Create one compose file per domain:
- `domains/app/docker-compose.yml`
- `domains/worker_scan/docker-compose.yml`
- `domains/worker_parse_document/docker-compose.yml`
- `domains/worker_chunk_text/docker-compose.yml`
- `domains/worker_embed_chunks/docker-compose.yml`
- `domains/worker_index_weaviate/docker-compose.yml`
- `domains/worker_manifest/docker-compose.yml`
- `domains/worker_metrics/docker-compose.yml`
2. Each worker compose defines only one service (its own worker) built from `domains/worker_<name>/Dockerfile`.
3. App compose (`domains/app/docker-compose.yml`) is fully separate from worker domains and must not include worker services.
4. No `depends_on` links from `domains/app` to worker domains, and no worker domain compose may require app domain startup.
5. Run each worker with its own Poetry command (example: `poetry run python -m app`).
6. Keep shared infra env vars consistent across domains; keep stage-specific queue/env vars local to each worker domain.
7. Scaling and lifecycle control must be per worker domain (examples: `docker compose -f domains/worker_chunk_text/docker-compose.yml up -d --scale pipeline-worker-chunk-text=3` and `docker compose -f domains/worker_chunk_text/docker-compose.yml down`).
8. Review and update `/home/sultan/repos/governed-rag-foundation/stack.sh` to account for the new domain layout (`domains/app` and `domains/worker_*`) so stack commands correctly target app and individual worker domains.

### 8. Manifest and Retry Policy
1. Manifest file: `07_metadata/manifest/<doc_id>.json`.
2. Track: current stage, status per stage, attempts, timestamps, last error.
3. Skip completed stages on retry.
4. Use deterministic keys and idempotent Weaviate upserts to prevent duplicates.

### 9. Observability and Acceptance
1. Counters: `files_processed`, `chunks_created`, `embedding_artifacts`, `index_upserts`, `failures`.
2. Acceptance criteria:
- file exists in `03_processed/`
- file exists in `04_chunks/`
- file exists in `05_embeddings/`
- chunks retrievable from Weaviate query

### 10. Delivery Phases
1. Phase 1: scaffold `libs/pipeline-common`, `domains/app`, `domains/worker_scan`, and `domains/worker_parse_document`.
2. Phase 2: scaffold `domains/worker_chunk_text`, implement deterministic chunk IDs and `04_chunks` artifacts.
3. Phase 3: scaffold `domains/worker_embed_chunks` and `domains/worker_index_weaviate`, implement verification query.
4. Phase 4: scaffold `domains/worker_manifest` and `domains/worker_metrics`, implement retries/failure handling/metrics.
5. Phase 5: wire each `domains/<worker>/docker-compose.yml`, review/update `/home/sultan/repos/governed-rag-foundation/stack.sh`, and run end-to-end smoke tests using independently started worker domains.
