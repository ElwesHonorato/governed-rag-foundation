# worker_index_weaviate domain

This domain is the final indexing hop into the vector database. It pushes embeddings into Weaviate so retrieval can happen in real prompts.

## Deep Dive

### Stage responsibility
- Consumes `q.index_weaviate` messages (`embeddings_key`, `doc_id`).
- Reads embeddings from `05_embeddings/`.
- Upserts chunk vectors and metadata into Weaviate.
- Writes index status objects to `06_indexes/`.
- Sends failures to `q.index_weaviate.dlq`.

### Indexed metadata
- Upserts include `chunk_id`, `doc_id`, `chunk_text`, `source_key`, and `security_clearance`.

### Runtime dependencies
- `WEAVIATE_URL` for vector upserts/verification.
- Queue: `BROKER_URL`.
- Storage: `S3_ENDPOINT`, `S3_ACCESS_KEY`, `S3_SECRET_KEY`.

### Operational notes
- Service container: `pipeline-worker-index-weaviate`.
- Queue contract stage: `index_weaviate`.
