# app_elasticsearch_poc domain

This domain is a standalone Elasticsearch spike/prototype.

It exists to give you a minimal local proof of concept for:
- starting Elasticsearch
- creating an index
- seeding chunk-like documents
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

- `domains/infra_elasticsearch/docker-compose.yml`
- `domains/app_elasticsearch_poc/src/elasticsearch_poc/create_index.py`
- `domains/app_elasticsearch_poc/src/elasticsearch_poc/seed_documents.py`
- `domains/app_elasticsearch_poc/src/elasticsearch_poc/search_documents.py`
- `domains/app_elasticsearch_poc/src/elasticsearch_poc/demo.py`
- `domains/app_elasticsearch_poc/sample_data/rag_chunks.json`

## Local Setup

Default runtime values:
- `ELASTICSEARCH_URL=http://localhost:9201`
- `ELASTICSEARCH_INDEX=rag_chunks`

Install the Python package:

```bash
cd domains/app_elasticsearch_poc
poetry install
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
cd domains/app_elasticsearch_poc
poetry run elasticsearch-poc-create-index
```

Expected behavior:
- creates the `rag_chunks` index with a simple mapping
- if the index already exists, prints a helpful message and exits cleanly

## Seed Sample Documents

```bash
cd domains/app_elasticsearch_poc
poetry run elasticsearch-poc-seed
```

Expected behavior:
- loads chunk-like sample documents from `sample_data/rag_chunks.json`
- bulk indexes them into Elasticsearch
- prints how many documents were indexed

## Run Searches

```bash
cd domains/app_elasticsearch_poc
poetry run elasticsearch-poc-search "lineage runtime"
poetry run elasticsearch-poc-search "security clearance" --limit 3
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
cd domains/app_elasticsearch_poc
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

## Intentionally Not Implemented

- No existing worker integration
- No existing retrieval integration
- No background indexing pipeline
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
