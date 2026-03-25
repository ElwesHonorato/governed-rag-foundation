# Elasticsearch POC Architecture

This domain provides a small HTTP retrieval API plus local Elasticsearch utility commands.

Current responsibilities:
- serve a local WSGI retrieval endpoint over Elasticsearch
- create a local index
- bulk seed sample chunk-like documents
- import real chunk artifacts from MinIO object storage
- run simple text searches
- provide a demo runner for local exploration

Key runtime wiring:
- `src/elasticsearch_poc/app.py` is the composition root for the HTTP process.
- `src/elasticsearch_poc/adapters/http/` contains the WSGI application boundary, request normalization, routing, response rendering, and HTTP handlers.
- `src/elasticsearch_poc/common.py` owns shared Elasticsearch client and helper functions for the local utility commands.
- `src/elasticsearch_poc/create_index.py` creates the index and mapping.
- `src/elasticsearch_poc/seed_documents.py` bulk indexes sample documents.
- `src/elasticsearch_poc/import_minio_chunks.py` reads `rag-data/DEV/04_chunks/` stage artifacts from MinIO and indexes them into Elasticsearch.
- `src/elasticsearch_poc/search_documents.py` runs a simple match query.
- `src/elasticsearch_poc/demo.py` orchestrates local infra startup and the demo flow.

Deployment shape:
- standalone Python domain with one long-running HTTP process and several local utility commands
- separate infra packaging in `domains/infra_app_elasticsearch`
- local Elasticsearch infra lives separately in `domains/infra_elasticsearch`
- optional MinIO read path uses the repo's existing local S3-compatible storage env convention
- intentionally not integrated with current workers or retrieval runtime
