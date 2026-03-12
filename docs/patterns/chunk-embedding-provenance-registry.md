# Chunk + Embedding Provenance Registry

## Storage choice
- Storage backend: object storage (S3-compatible) through `ObjectStorageGateway`.
- Write model: overwrite `latest` state objects only (golden path).
- Location:
  - `07_metadata/provenance/chunking/latest/...`
  - `07_metadata/provenance/embedding/latest/...`
  - `07_metadata/provenance/embedding/latest_by_pair/...` (lookup helper for `(chunk_id, index_target)`)

## Deterministic identities
- Chunk identity uses source dataset/version + chunker config/version + byte offsets.
- Embedding identity uses chunk identity + embedder config/version + index target.
- Functions live in `pipeline_common.provenance.identifiers`.

## Runtime flow
1. `worker_chunk_text` computes deterministic chunk envelopes and writes chunk artifacts.
2. Chunk rows are upserted into chunk registry (`ACTIVE` latest state).
3. `worker_embed_chunks` propagates provenance metadata into embedding artifacts.
4. `worker_index_weaviate` upserts vectors and writes embedding registry `SUCCEEDED` latest state.

## Provenance tracing
- `get_chunk_provenance(chunk_id)` resolves source dataset hash, chunk object path, and chunker metadata.
- `get_embedding_provenance(chunk_id, index_target)` resolves latest embedding row for that target.
- `trace_from_vector_result(chunk_id, index_target)` joins chunk + embedding chain for deterministic traceability.

## DataHub readability
- DataHub lineage remains dataset-level.
- Registry datasets are represented as shared dataset prefixes, not per chunk entities.
