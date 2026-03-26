# worker_index_elasticsearch domain

Queue-driven worker that indexes `StageArtifact` chunk payloads into Elasticsearch.

## Deep Dive

### Stage responsibility
- Consumes `q.index_elasticsearch` messages.
- Reads chunk artifacts from `04_chunks/`.
- Maps `StageArtifact` payloads into Elasticsearch documents.
- Upserts those documents into the configured Elasticsearch index.

### Runtime dependencies
- Queue: `BROKER_URL`.
- Storage: `S3_ENDPOINT`, `S3_ACCESS_KEY`, `S3_SECRET_KEY`.
- Elasticsearch: `ELASTICSEARCH_URL`.

### Operational notes
- Service container: `pipeline-worker-index-elasticsearch`.
- Queue contract stage: `index_elasticsearch`.
