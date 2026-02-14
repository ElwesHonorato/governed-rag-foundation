# worker_embed_chunks domain

This domain converts text chunks into vector embeddings, preparing them for vector indexing.

## Deep Dive

### Stage responsibility
- Consumes `q.embed_chunks` messages.
- Reads chunk artifacts from `04_chunks/`.
- Builds embedding payloads and metadata.
- Writes embedding artifacts to `05_embeddings/{doc_id}/{chunk_id}.embedding.json`.
- Publishes index requests to `q.index_weaviate`.
- Sends failures to `q.embed_chunks.dlq`.

### Embedding behavior
- Uses deterministic pseudo-embeddings based on SHA-256 hashing.
- Embedding dimensionality controlled by `EMBEDDING_DIM`.

### Runtime dependencies
- Queue: `BROKER_URL`.
- Storage: `S3_ENDPOINT`, `S3_ACCESS_KEY`, `S3_SECRET_KEY`.
- Embedding dimension: `EMBEDDING_DIM`.

### Operational notes
- Service container: `pipeline-worker-embed-chunks`.
- Queue contract stage: `embed_chunks`.
