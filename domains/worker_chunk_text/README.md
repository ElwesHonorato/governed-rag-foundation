# worker_chunk_text domain

This domain breaks processed documents into retrieval-friendly chunks. It is where large parsed text becomes indexed units.

## Deep Dive

### Stage responsibility
- Consumes `q.chunk_text` messages.
- Reads processed objects from `03_processed/`.
- Splits text into deterministic chunks.
- Writes one artifact per chunk to `04_chunks/{doc_id}/{chunk_id}.chunk.json`.
- Publishes each chunk key to `q.embed_chunks`.
- Sends failures to `q.chunk_text.dlq`.

### Payload characteristics
- Chunk records include `chunk_id`, `doc_id`, `chunk_index`, `chunk_text`, `source_key`, and security metadata.

### Runtime dependencies
- Queue: `BROKER_URL`.
- Storage: `S3_ENDPOINT`, `S3_ACCESS_KEY`, `S3_SECRET_KEY`.

### Operational notes
- Service container: `pipeline-worker-chunk-text`.
- Queue contract stage: `chunk_text`.
