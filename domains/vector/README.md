# vector domain

This domain is the retrieval engine. It stores chunk vectors and metadata so the API can retrieve relevant context for user questions.

## Deep Dive

### What runs here
- `weaviate` (`cr.weaviate.io/semitechnologies/weaviate:1.27.7`)

### How it contributes to RAG
- Stores `DocumentChunk` vectors and metadata.
- Supports retrieval for grounded prompting in `rag-api`.
- Receives upserts from `worker_index_weaviate`.

### Runtime dependencies
- Uses `QUERY_DEFAULTS_LIMIT` from `WEAVIATE_QUERY_DEFAULTS_LIMIT`.
- Anonymous access is enabled in local mode.
- Persists vector data under `localdata/weaviate`.

### Interface
- HTTP API on `${WEAVIATE_PORT}:8080`.
