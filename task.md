# Elasticsearch Implementation Plan

## Goal

Evolve the current isolated Elasticsearch spike into a realistic local indexing/search flow without refactoring the existing production architecture.

The target model is:

1. MinIO remains the system of record for pipeline artifacts.
2. Elasticsearch runs as a long-lived search service and stores its own indexes.
3. A separate indexing step consumes change events and writes searchable documents into Elasticsearch.
4. Search queries hit Elasticsearch directly, not MinIO.

This plan is intentionally incremental and should preserve the current repo shape:

- keep the existing workers
- avoid touching current agent/retrieval flows
- add new Elasticsearch-specific pieces in isolation

## Current State

What already exists:

- `domains/infra_elasticsearch`
  - standalone Elasticsearch service for the spike
- `domains/app_elasticsearch`
  - create-index script
  - seed script
  - search script
  - MinIO importer for `rag-data/DEV/04_chunks/`

What is missing:

- automatic indexing when new chunk artifacts land
- delete handling when source files are removed
- update handling when chunk artifacts are regenerated
- a long-running indexer process tied to queue-driven events

## Architecture Direction

Use Elasticsearch as a separate serving/search store.

Do not make Elasticsearch read the bucket directly.

Instead:

1. pipeline writes chunk artifacts to MinIO
2. queue emits indexing work
3. Elasticsearch indexer reads chunk artifacts from MinIO
4. indexer upserts or deletes Elasticsearch documents
5. queries run against Elasticsearch indexes

This keeps responsibilities clear:

- MinIO: artifact storage
- RabbitMQ: work notification
- Elasticsearch: persistent search index
- indexer: synchronization bridge

## Indexing Document Model

Base Elasticsearch document shape:

- `chunk_id`
- `doc_id`
- `source_key`
- `text`
- `content_type`
- `created_at`
- `metadata.security_clearance`
- `metadata.source_type`

Useful extra metadata for operational handling:

- `metadata.root_source_uri`
- `metadata.stage_source_key`
- `metadata.offsets_start`
- `metadata.offsets_end`
- `metadata.chunk_text_hash`

Deletion should key off one of:

- `doc_id`
- `metadata.root_source_uri`

Preferred document id:

- Elasticsearch `_id = chunk_id`

That makes re-indexing idempotent for the same chunk artifact.

## Phase 1: Keep The Spike Manual But Correct

Status:

- mostly done

Work:

1. Keep `infra_elasticsearch` as the isolated long-running Elasticsearch service.
2. Keep `app_elasticsearch` as a CLI domain for learning and local validation.
3. Use the importer to read `DEV/04_chunks/` from MinIO and populate Elasticsearch.
4. Keep all spike env keys prefixed with `ELASTICSEARCH_POC_*` so they do not collide with production stack env.

Why:

- validates the document model
- validates index mapping
- validates search behavior
- stays fully isolated

## Phase 2: Add Delete Support To The Spike

Add small CLI scripts to exercise lifecycle behavior.

Suggested commands:

- `elasticsearch-poc-delete-by-doc-id`
- `elasticsearch-poc-delete-by-root-source-uri`

Behavior:

- delete all indexed chunks for a logical document
- print deleted count
- keep implementation simple with `delete_by_query`

Why:

- makes add/update/delete behavior explicit
- lets local testing mirror real indexing lifecycle

## Phase 3: Introduce An Isolated Elasticsearch Index Worker

Add a new domain, separate from the current production retrieval path.

Suggested domain:

- `domains/worker_index_elasticsearch`

Responsibilities:

1. consume indexing work from RabbitMQ
2. fetch chunk artifacts from MinIO
3. transform chunk artifacts into Elasticsearch documents
4. upsert documents into Elasticsearch
5. handle delete events by removing matching Elasticsearch docs

Keep the worker aligned with existing repo conventions:

- composition root in `src/worker_index_elasticsearch/app.py`
- startup contracts local to the worker
- queue-driven service layer
- minimal service factory only if it matches current worker conventions

Do not integrate it into agent runtime or retrieval runtime yet.

## Phase 4: Define Queue Contract For Elasticsearch Indexing

There are two reasonable options.

### Option A: Reuse Current Stage Progression

Trigger Elasticsearch indexing from the existing chunk stage output.

Flow:

1. chunk artifact written to `DEV/04_chunks/`
2. queue message carries artifact URI
3. Elasticsearch worker consumes URI
4. worker reads the artifact and indexes it

Pros:

- minimal new concepts
- follows current governed pipeline style

Cons:

- only covers create/update unless deletion events are added separately

### Option B: Introduce Explicit Search Index Events

Create a dedicated queue contract for index mutations.

Example event types:

- `upsert_chunk`
- `delete_document`
- `delete_chunk`

Pros:

- cleaner long-term lifecycle model
- explicit delete semantics

Cons:

- slightly more upfront design work

Recommended next step:

- start with Option A for upserts
- add explicit delete events only when needed

## Phase 5: Handle File Removal Correctly

Elasticsearch must remove stale indexed records when source documents are removed.

Deletion flow:

1. source file deletion is detected upstream
2. pipeline emits delete work with stable identity
3. Elasticsearch worker runs delete-by-query

Preferred delete keys:

- first choice: `doc_id`
- second choice: `metadata.root_source_uri`

Reason:

- one source document usually maps to many chunks
- delete needs to remove all derived chunk documents together

## Phase 6: Support Update / Reindex

Updates should behave like:

1. source changes
2. chunks are regenerated
3. same logical document is reprocessed
4. Elasticsearch receives new upserts
5. stale chunks are removed if chunk ids changed

Two possible approaches:

### Simple approach

- delete all docs by `doc_id`
- reindex current chunk set

### Smarter approach

- upsert current chunk ids
- diff and delete stale chunk ids

Recommended first implementation:

- delete by `doc_id`
- then reindex current chunks

This is simpler and good enough for the first real worker.

## Phase 7: Keep Search Separate From Retrieval For Now

Do not wire Elasticsearch into:

- `agent_api`
- current retrieval gateways
- current grounded-response flow

Instead keep it as:

- separate searchable index
- separate CLI or test surface
- optional future retrieval source

Why:

- preserves current architecture
- avoids accidental refactor drift
- lets Elasticsearch mature independently

## Phase 8: Later Integration Options

Once the indexing worker is stable, choose one of these paths.

### Option 1: Lexical Retrieval Sidecar

Elasticsearch becomes a keyword search backend alongside Weaviate.

Use cases:

- exact phrase recall
- filters
- debugging retrieved corpus

### Option 2: Hybrid Retrieval Layer

Elasticsearch provides lexical recall while Weaviate provides vector recall.

Requires:

- ranking/fusion design
- query orchestration
- evaluation datasets

### Option 3: Ops / Inspection Search

Use Elasticsearch only as an engineering and governance search surface.

Use cases:

- inspect indexed chunks
- debug ingestion
- trace document presence

Recommended near-term path:

- Option 3 first
- Option 1 second
- hybrid only after evaluation proves it is worth the complexity

## Concrete Work Breakdown

### Task 1

Keep the current POC healthy:

- verify `infra_elasticsearch` starts cleanly
- verify `elasticsearch-poc-import-minio`
- verify `elasticsearch-poc-search`

### Task 2

Add delete scripts to `app_elasticsearch`:

- delete by `doc_id`
- delete by `root_source_uri`

### Task 3

Create `domains/worker_index_elasticsearch`:

- queue consumer
- MinIO reader
- Elasticsearch writer
- simple upsert behavior

### Task 4

Define queue contract for upsert events:

- likely artifact URI payload first
- typed contract later if needed

### Task 5

Add delete event handling:

- document deletion
- delete-by-query in Elasticsearch

### Task 6

Document the worker architecture:

- README
- `docs/ARCHITECTURE.md`
- env vars
- queue behavior

## Minimal Env Additions For A Real Worker

If a dedicated worker is added later, it will likely need:

- `ELASTICSEARCH_URL`
- `ELASTICSEARCH_INDEX`
- existing RabbitMQ env vars
- existing S3 env vars

Do not reuse the `ELASTICSEARCH_POC_*` names for the real worker.

Those prefixed keys should remain spike-only.

## Risks

1. Env collision between spike config and production stack config.
2. Duplicate indexing of the same chunk if queue semantics are not idempotent.
3. Stale documents in Elasticsearch if delete flow is skipped.
4. Update drift if regenerated chunks are indexed without removing old chunk docs.
5. Premature integration into agent retrieval before the indexing lifecycle is stable.

## Recommended Immediate Next Step

Build the smallest real next increment:

1. keep the current spike
2. add delete CLI scripts
3. create `worker_index_elasticsearch` as a separate queue-driven worker
4. feed it chunk artifact URIs
5. keep it out of the agent retrieval path until it is operationally stable

## Definition Of Done For The Next Increment

The next increment is done when:

1. Elasticsearch runs continuously as a local service.
2. A new chunk artifact can be indexed automatically through queue-driven flow.
3. A removed source document causes indexed Elasticsearch records to be deleted.
4. Search results reflect current MinIO-derived chunk state.
5. No existing agent runtime or retrieval flow was refactored to achieve this.
