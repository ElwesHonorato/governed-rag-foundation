Refactor the Elasticsearch integration to follow the existing queue-driven worker architecture in this repo.

Target behavior:
- `/home/sultan/repos/governed-rag-foundation/domains/worker_chunk_text`, create one queue and post generated chunks to it.
- Add a long-running Elasticsearch worker that continuously consumes from that queue
- The Elasticsearch worker should index the consumed `StageArtifact` payloads into Elasticsearch
- Expose a query endpoint for retrieval
- Keep everything compatible with the existing RAG pipeline, domain structure, startup conventions, and clean architecture boundaries

Requirements:
- Assess the current implementation patterns from `/home/sultan/repos/governed-rag-foundation/domains` and extend them instead of introducing a parallel architecture
- Reuse the existing queue, settings, runtime-context, factory, and worker-service patterns where appropriate
- Keep orchestration/startup concerns separate from business logic
- Prefer narrow interfaces, explicit contracts, and strong typing
- Follow the existing naming and Google-style docstring conventions already used in the repo
- Do not overengineer

Implementation goals:
1. Update `worker_chunk_text` so it publishes `StageArtifact` URI to a dedicated Elasticsearch indexing queue
2. Define the queue contract/envelope clearly for the Elasticsearch indexing flow
3. Add a dedicated long-running Elasticsearch worker under the appropriate domain structure
4. The new worker must:
   - consume messages from the queue in a loop
   - Reads from the URI, deserialize the `StageArtifact` payload
   - transform it into an Elasticsearch document
   - index it into Elasticsearch
5. Expose a retrieval/query service for BM25-style search
6. Expose that retrieval through an endpoint consumable by the existing RAG pipeline
7. Add only the minimum config/env surface needed for local development
8. Keep the design easy to extend later for retries, DLQ, and hybrid retrieval

Indexing expectations:
- Index the output of `StageArtifact` from `worker_chunk_text`
- Preserve retrieval metadata for downstream RAG usage
- Include stable identifiers where available so re-indexing can be controlled cleanly
- Keep the Elasticsearch document shape aligned with current contracts and metadata already present in the pipeline

Constraints:
- Do not redesign the whole ingestion pipeline
- Do not replace the current vector retrieval path
- Do not add hybrid retrieval yet
- Do not introduce unnecessary frameworks or infrastructure
- Keep the implementation lean, testable, and consistent with the repo’s worker patterns

Deliverables:
- Refactor of `worker_chunk_text` to publish to the Elasticsearch indexing queue
- New Elasticsearch worker domain/package wired through the existing startup/factory/runtime patterns
- Elasticsearch gateway/client abstraction
- Mapping from `StageArtifact` to Elasticsearch document shape
- Query service and query endpoint for retrieval
- Minimal settings/env additions
- A short markdown note explaining the flow:
  `worker_chunk_text -> queue -> elasticsearch worker -> Elasticsearch -> query endpoint -> RAG`