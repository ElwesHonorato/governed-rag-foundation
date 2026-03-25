# Elasticsearch Flow

The Elasticsearch retrieval path now follows the existing worker architecture:

`worker_chunk_text -> q.index_elasticsearch -> worker_index_elasticsearch -> Elasticsearch -> app_elasticsearch /retrieve -> RAG caller`

Notes:
- `worker_chunk_text` still publishes to `q.embed_chunks` for the vector path.
- Elasticsearch indexing consumes the same chunk-stage `StageArtifact` contract written to `DEV/04_chunks/...`.
- Retrieval stays lexical/BM25-only for now.
- This path is additive and does not replace the current Weaviate-backed retrieval flow.
