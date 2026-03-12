# Task Plan: Chunking Registry + Embedding Registry (Enterprise RAG Lineage)

Source of truth:
- `task.md` prompt requirements.

Objective:
- Implement deterministic provenance registries for chunking and embedding while keeping DataHub lineage readable at dataset level.

---

## 0) Decisions and constraints

### 0.1 Storage strategy
- Default storage: S3-compatible object storage JSON append-only event objects + latest-state objects.
- Keep schema evolution explicit and backward-safe.

### 0.2 Deterministic identity functions
Implement shared canonical hashing helpers:
- `source_content_hash = sha256(source_bytes)`
- `chunk_params_hash = sha256(canonical_json(chunker_params))`
- `chunk_id = sha256(source_dataset_urn + source_content_hash + chunker_name + chunker_version + chunk_params_hash + offsets.start + offsets.end)`
- `embedding_params_hash = sha256(canonical_json(embedder_params))`
- `embedding_id = sha256(chunk_id + embedder_name + embedder_version + embedding_params_hash + index_target)`

Acceptance:
- Stable across retries.
- Same input produces same IDs in runtime behavior checks.

---

## 1) Registry data model and contracts

### 1.1 Create schemas/contracts
Create typed contracts/models for:
- Chunking Registry row
- Embedding Registry row
- Status enums:
  - Chunk: `ACTIVE`, `DELETED`, `SUPERSEDED`
  - Embedding: `STARTED`, `SUCCEEDED`, `FAILED`

### 1.2 Required chunking registry fields
- `chunk_id` (PK)
- `source_dataset_urn`
- `source_s3_uri`
- `source_content_hash`
- `chunk_s3_uri`
- `offsets_start`
- `offsets_end`
- `breadcrumb` (optional)
- `chunk_text_hash`
- `chunker_name`
- `chunker_version`
- `chunk_params_hash`
- `chunking_run_id`
- `created_at`
- `observed_at`
- `status`

### 1.3 Required embedding registry fields
- `embedding_id` (PK)
- `chunk_id` (FK logical)
- `index_target`
- `embedder_name`
- `embedder_version`
- `embedding_params_hash`
- `embedding_dim`
- `embedding_vector_hash` (optional)
- `embedding_run_id`
- `chunking_run_id`
- `attempt`
- `status`
- `error_message`
- `started_at`
- `finished_at`
- `upserted_at`
- `vector_record_id`

---

## 2) Canonical provenance envelope

### 2.1 Implement envelope builders
- `build_chunk_envelope(...) -> dict`
- `build_embedding_envelope(...) -> dict`

Requirements:
- Include fields needed to join both registries by `chunk_id`.
- Include run IDs and version/config hashes.

### 2.2 Envelope usage
- Persist envelope metadata with chunk objects in S3.
- Persist envelope fields in registry rows.
- Include envelope metadata in vector upsert payload metadata.

---

## 3) Registry writer implementation (idempotent + concurrency-safe)

### 3.1 Chunking registry writer
Capabilities:
- Upsert by `chunk_id` semantics.
- Append-only event write path (partitioned by `dt` + `chunking_run_id`).
- Compaction into latest-state table keyed by `chunk_id`.

### 3.2 Embedding registry writer
Capabilities:
- Upsert by deterministic key (`embedding_id`) + attempt events.
- Transition model: `STARTED -> SUCCEEDED/FAILED`.
- Retry-safe with `attempt` increments.
- Concurrent worker safety with append + compact strategy.

### 3.3 Query access layer
Implement lookups:
- By `chunk_id`
- By `source_dataset_urn + source_content_hash`
- By `chunking_run_id`
- Latest embedding by `(chunk_id, index_target)`

---

## 4) Pipeline integration

### 4.1 Chunking stage integration
For each source file:
- Compute `source_content_hash`
- Chunk content
- For each chunk:
  - Compute deterministic `chunk_id`
  - Write chunk object to `chunk_s3_uri` with envelope metadata
  - Write chunking registry record (idempotent)

### 4.2 Embedding stage integration (async)
For each work unit:
- Resolve chunk from chunking registry (or payload input)
- Mark embedding registry as `STARTED` (attempt increment)
- Compute embedding
- Upsert vector DB with metadata (`chunk_id`, `embedding_id`, versions, run IDs)
- Mark `SUCCEEDED` with timestamps
- On error: mark `FAILED` + `error_message`

---

## 5) DataHub modeling (dataset-level only)

### 5.1 Datasets
Model these datasets only:
- Source file datasets
- `chunk_store_dataset` (S3 prefix)
- `chunking_registry_dataset`
- `vector_index_dataset`
- `embedding_registry_dataset`

### 5.2 Static lineage
- source -> chunking_job -> chunk_store
- chunking_job -> chunking_registry
- chunking_registry -> embedding_job -> vector_index
- embedding_job -> embedding_registry

### 5.3 Runtime lineage (DPI)
- Chunking DPI: include partition/manifest reference + chunk count.
- Embedding DPI: include processed count, batch id, `chunking_run_id`.

Constraint:
- Never create DataHub Dataset per chunk.

---

## 6) Provenance query APIs

Implement functions:
- `get_chunk_provenance(chunk_id)`
- `get_embedding_provenance(chunk_id, index_target)`
- `trace_from_vector_result(chunk_id, index_target)`

Output contract:
- Must provide full trace chain from vector result back to source dataset/version and runs.

---

## 7) Validation (tests deferred for now)

Current policy for this task:
- Automated tests were removed per request.
- Validation relies on compile checks and runtime verification in worker flows.

Deferred test backlog (future):
- Deterministic `chunk_id`
- Deterministic `embedding_id`
- Upsert idempotency
- Status transitions (`STARTED -> SUCCEEDED`, retry + failure paths)
- Concurrency strategy correctness under parallel append events
- Chunking stage writes envelope + registry
- Embedding stage writes STARTED/SUCCEEDED/FAILED transitions
- Query APIs return expected trace chain

---

## 8) Documentation deliverables

### 8.1 README/update doc
Include:
- Storage choice rationale
- How to trace from vector DB result to source and runs
- Async embedding representation in registry
- Why DataHub lineage remains readable

### 8.2 File-by-file delivery format
- Provide final implementation as file-by-file output with paths.

---

## 9) Execution order (implementation sequence)

1. Shared deterministic hashing + canonical JSON helpers.
2. Registry row contracts + status enums.
3. Chunk/embedding envelope builders.
4. S3 object-storage JSON registry writer (append events + latest-state objects).
5. Chunking stage integration.
6. Embedding stage integration with STARTED/SUCCEEDED/FAILED lifecycle.
7. Query APIs.
8. DataHub lineage extensions.
9. Validation via compile and runtime checks (tests deferred).
10. README + docs.

---

## 10) Definition of done

- Deterministic IDs validated by deterministic function definitions and runtime behavior checks.
- Both registries operational and authoritative for provenance.
- Async embedding retries handled with idempotent, concurrency-safe writes.
- Query APIs resolve full provenance chain.
- DataHub lineage remains dataset-level and readable.
- Documentation updated with usage and tracing workflow.
- Automated tests intentionally deferred/removed for this iteration.
