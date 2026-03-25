# app_elasticsearch domain

HTTP retrieval app plus local utility commands for the Elasticsearch integration.

## Deep Dive

### Domain responsibility
- Exposes a retrieval endpoint over Elasticsearch for lexical chunk search.
- Creates and manages a local Elasticsearch index for local development.
- Seeds sample chunk-like documents for local exploration.
- Imports real chunk artifacts from MinIO under `DEV/04_chunks/`.
- Runs simple lexical searches against the Elasticsearch index.

### What this is
- A small HTTP app for Elasticsearch retrieval plus a few local utility commands.
- A local sandbox for indexing, bulk ingest, and simple BM25-style search.
- The query surface for the Elasticsearch indexing path.

### What this is not
- Not a queue-driven worker.
- Not integrated with current gateways, factories, workers, or startup flow.
- Not part of the existing retrieval path.
- Not implementing custom analyzers, vectors, hybrid retrieval, or advanced relevance tuning.

### Runtime dependencies
- `ELASTICSEARCH_POC_URL` for the target Elasticsearch endpoint.
- `ELASTICSEARCH_POC_INDEX` for the target index name.
- `ELASTICSEARCH_POC_S3_ENDPOINT`, `ELASTICSEARCH_POC_S3_BUCKET`, `ELASTICSEARCH_POC_S3_PREFIX` for MinIO chunk import.
- `ELASTICSEARCH_POC_S3_ACCESS_KEY`, `ELASTICSEARCH_POC_S3_SECRET_KEY` for MinIO credentials.

### Operational notes
- The primary runtime is a long-running HTTP process.
- Container packaging lives separately in `domains/infra_app_elasticsearch`.
- Elasticsearch itself runs separately in `domains/infra_elasticsearch`.

### Files of interest

- `domains/infra_app_elasticsearch/docker-compose.yml`
- `domains/infra_app_elasticsearch/Dockerfile`
- `domains/infra_elasticsearch/docker-compose.yml`
- `domains/app_elasticsearch/src/elasticsearch_poc/create_index.py`
- `domains/app_elasticsearch/src/elasticsearch_poc/seed_documents.py`
- `domains/app_elasticsearch/src/elasticsearch_poc/import_minio_chunks.py`
- `domains/app_elasticsearch/src/elasticsearch_poc/search_documents.py`
- `domains/app_elasticsearch/src/elasticsearch_poc/demo.py`
- `domains/app_elasticsearch/sample_data/rag_chunks.json`

### Local setup

Default runtime values:
- `ELASTICSEARCH_POC_URL=http://localhost:9201`
- `ELASTICSEARCH_POC_INDEX=rag_chunks`
- `ELASTICSEARCH_POC_S3_ENDPOINT=http://localhost:9000`
- `ELASTICSEARCH_POC_S3_BUCKET=rag-data`
- `ELASTICSEARCH_POC_S3_PREFIX=DEV/04_chunks/`
- `ELASTICSEARCH_POC_S3_ACCESS_KEY=minio`
- `ELASTICSEARCH_POC_S3_SECRET_KEY=minio123`

Install the Python package:

```bash
cd domains/app_elasticsearch
poetry install
```

Run the HTTP query API locally:

```bash
cd domains/app_elasticsearch
poetry run elasticsearch-poc-api
```

Query it:

```bash
curl -X POST http://localhost:8081/retrieve \
  -H 'Content-Type: application/json' \
  -d '{"query":"lineage runtime","limit":3}'
```

Container packaging for this app lives in `domains/infra_app_elasticsearch`:

```bash
docker compose -f domains/infra_app_elasticsearch/docker-compose.yml build
docker compose -f domains/infra_app_elasticsearch/docker-compose.yml run --rm app-elasticsearch poetry run elasticsearch-poc-api
```

Local env template:

- Copy `.env.example` to `.env` in this domain if you want a domain-scoped local CLI env file.

## Start Elasticsearch

```bash
docker compose -f domains/infra_elasticsearch/docker-compose.yml up -d
```

Check health:

```bash
curl http://localhost:9201/_cluster/health
```

## Create The Index

```bash
cd domains/app_elasticsearch
poetry run elasticsearch-poc-create-index
```

Container form:

```bash
docker compose -f domains/infra_app_elasticsearch/docker-compose.yml run --rm app-elasticsearch poetry run elasticsearch-poc-create-index
```

Expected behavior:
- creates the `rag_chunks` index with a simple mapping
- if the index already exists, prints a helpful message and exits cleanly

## Seed Sample Documents

```bash
cd domains/app_elasticsearch
poetry run elasticsearch-poc-seed
```

Container form:

```bash
docker compose -f domains/infra_app_elasticsearch/docker-compose.yml run --rm app-elasticsearch poetry run elasticsearch-poc-seed
```

Expected behavior:
- loads chunk-like sample documents from `sample_data/rag_chunks.json`
- bulk indexes them into Elasticsearch
- prints how many documents were indexed

## Import Real Chunk Artifacts From MinIO

This is the bridge between the existing object-storage pipeline artifacts and the isolated Elasticsearch spike.

It does not query MinIO directly with Elasticsearch. Instead it:
- lists JSON chunk artifacts under `rag-data/DEV/04_chunks/`
- reads each stage payload from MinIO
- extracts `chunk_id`, `doc_id`, `source_key`, chunk text, and selected metadata
- bulk indexes those records into `rag_chunks`

Command:

```bash
cd domains/app_elasticsearch
poetry run elasticsearch-poc-import-minio
```

Container form:

```bash
docker compose -f domains/infra_app_elasticsearch/docker-compose.yml run --rm app-elasticsearch poetry run elasticsearch-poc-import-minio
```

Expected behavior:
- creates the index if needed
- imports real chunk artifacts from MinIO
- prints how many chunk records were indexed

If your MinIO bucket or prefix differs, override the env values first:

```bash
export ELASTICSEARCH_POC_S3_ENDPOINT=http://localhost:9000
export ELASTICSEARCH_POC_S3_BUCKET=rag-data
export ELASTICSEARCH_POC_S3_PREFIX=DEV/04_chunks/
export ELASTICSEARCH_POC_S3_ACCESS_KEY=minio
export ELASTICSEARCH_POC_S3_SECRET_KEY=minio123
poetry run elasticsearch-poc-import-minio
```

## Run Searches

```bash
cd domains/app_elasticsearch
poetry run elasticsearch-poc-search "lineage runtime"
poetry run elasticsearch-poc-search "security clearance" --limit 3
```

Container form:

```bash
docker compose -f domains/infra_app_elasticsearch/docker-compose.yml run --rm app-elasticsearch poetry run elasticsearch-poc-search "lineage runtime"
```

Expected output shape:
- `chunk_id`
- `doc_id`
- `source_key`
- `_score`
- text preview

## Run The Demo

The demo runner:
- starts local Elasticsearch infra
- waits until Elasticsearch is ready
- creates the index
- seeds the sample documents
- runs example searches

```bash
cd domains/app_elasticsearch
poetry run elasticsearch-poc-demo
```

## Example Search Output

Example output will look like:

```text
[search] query='lineage runtime' hits=2

- chunk_id=chunk-002
  doc_id=lineage-ops
  source_key=07_metadata/lineage/runtime-ops.md
  score=1.2345
  text=Runtime lineage events record stage transitions, queue handoffs, and output datasets...
```

After importing MinIO chunks, searches will return real pipeline chunk artifacts instead of the bundled sample JSON.

## Intentionally Not Implemented

- No existing worker integration
- No existing retrieval integration
- No background indexing pipeline
- No automatic sync from MinIO to Elasticsearch
- No queueing or Kafka
- No vector search in Elasticsearch
- No custom analyzers or rank tuning
- No auth/security hardening
- No Kibana

## How This Could Evolve Later

A sensible next step toward a real architecture would be:
1. Introduce an isolated indexing worker that writes chunk artifacts into Elasticsearch.
2. Add a retrieval-side adapter that can query Elasticsearch for keyword search.
3. Decide whether Elasticsearch is:
   - a primary retrieval store,
   - a secondary lexical store alongside vectors,
   - or a debugging/ops search layer.
4. Only after that, decide how it should fit into the platform gateways and startup flow.

That later evolution is intentionally out of scope for this spike.
