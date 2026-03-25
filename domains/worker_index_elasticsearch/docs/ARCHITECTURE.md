# worker_index_elasticsearch Architecture

Purpose:
- Consume chunk-stage artifacts from a dedicated queue and project them into Elasticsearch for lexical retrieval.

Flow:
- queue message -> object storage read -> `StageArtifact.from_dict(...)` -> document mapper -> `ElasticsearchGateway.index_chunk(...)`

Boundaries:
- Startup/composition stays in `startup/`.
- The worker loop stays in `services/worker_index_elasticsearch_service.py`.
- Elasticsearch document mapping stays in `services/index_elasticsearch_processor.py`.
