# worker_chunk_text domain

This domain reads processed document artifacts, splits their text into retrieval-friendly chunks, writes one object per chunk, and writes a manifest for the run.

## Deep Dive

### Stage responsibility
- Consumes queue messages whose payload is the input artifact URI.
- Reads the processed artifact from object storage.
- Resolves chunking stages from `root_metadata.source_type`.
- Splits text into deterministic chunks using LangChain splitters.
- Writes one artifact per chunk to `{doc_id}/runs/{run_id}/chunks/{chunk_id}.json`.
- Publishes each chunk URI to the downstream queue.
- Writes a manifest summarizing the processing result.
- Marks lineage runs as complete or failed.

### Payload characteristics
- Input payloads are queue envelopes whose inner payload is a storage URI.
- Output chunk artifacts contain stage metadata plus the chunk text in `content.data`.
- Chunk metadata includes `source_doc_uri`, `chunk_id`, `ordinal`, and `characters`.

### Runtime dependencies
- Queue: `BROKER_URL`.
- Storage: `S3_ENDPOINT`, `S3_ACCESS_KEY`, `S3_SECRET_KEY`.
- Lineage: runtime lineage gateway configured through shared startup settings.

### Operational notes
- Service container: `pipeline-worker-chunk-text`.
- Queue contract stage: `chunk_text`.
- Composition root: `src/app.py`.
