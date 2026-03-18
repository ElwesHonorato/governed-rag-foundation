# app_elasticsearch domain

This domain is a standalone Elasticsearch spike/prototype.

It exists to give you a minimal local proof of concept for:
- starting Elasticsearch
- creating an index
- seeding chunk-like documents
- importing real chunk artifacts from MinIO
- searching those documents from the command line

It is intentionally isolated from the current production architecture.

## What This Is

- A small CLI-oriented Elasticsearch playground.
- A local interview-prep sandbox for understanding indexing, mappings, bulk ingest, and simple text search.
- A domain-scoped prototype that follows the repository's `domains/` layout without integrating into current runtime flows.

## What This Is Not

- Not integrated with current gateways, factories, workers, DI, or startup flow.
- Not part of the existing retrieval path.
- Not a production Elasticsearch architecture.
- Not implementing custom analyzers, vectors, hybrid retrieval, or advanced relevance tuning.

## Files Of Interest

- `domains/app_elasticsearch/docker-compose.yml`
- `domains/app_elasticsearch/Dockerfile`
- `domains/infra_elasticsearch/docker-compose.yml`
- `domains/app_elasticsearch/src/elasticsearch_poc/create_index.py`
- `domains/app_elasticsearch/src/elasticsearch_poc/seed_documents.py`
- `domains/app_elasticsearch/src/elasticsearch_poc/import_minio_chunks.py`
- `domains/app_elasticsearch/src/elasticsearch_poc/search_documents.py`
- `domains/app_elasticsearch/src/elasticsearch_poc/demo.py`
- `domains/app_elasticsearch/sample_data/rag_chunks.json`

## Local Setup

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

This domain also has its own container packaging:

```bash
docker compose -f domains/app_elasticsearch/docker-compose.yml build
docker compose -f domains/app_elasticsearch/docker-compose.yml run --rm app-elasticsearch poetry run elasticsearch-poc
```

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
docker compose -f domains/app_elasticsearch/docker-compose.yml run --rm app-elasticsearch poetry run elasticsearch-poc-create-index
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
docker compose -f domains/app_elasticsearch/docker-compose.yml run --rm app-elasticsearch poetry run elasticsearch-poc-seed
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
docker compose -f domains/app_elasticsearch/docker-compose.yml run --rm app-elasticsearch poetry run elasticsearch-poc-import-minio
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
docker compose -f domains/app_elasticsearch/docker-compose.yml run --rm app-elasticsearch poetry run elasticsearch-poc-search "lineage runtime"
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
