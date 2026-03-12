# Prompt: Implement Chunking Registry + Embedding Registry (Enterprise RAG Lineage)

You are a senior platform engineer implementing enterprise-grade provenance for a RAG pipeline.
We persist chunks to S3 and index embeddings asynchronously in a vector DB.
We want TWO registries:
1) Chunking Registry: one row per chunk produced
2) Embedding Registry: one row per (chunk_id, embedder_version, index_target) produced (and optionally per attempt/run)

Goal: keep DataHub lineage UI readable (dataset-level), while allowing deterministic traceability:
vector_result(chunk_id) -> chunk registry -> embedding registry -> exact source file version + exact run(s) + exact code/config.

## Hard requirements

### Deterministic identity
- Define `source_content_hash = sha256(source_bytes)`
- Define `chunk_params_hash = sha256(canonical_json(chunker_params))`
- Define `chunk_id = sha256(
    source_dataset_urn
    + source_content_hash
    + chunker_name + chunker_version + chunk_params_hash
    + offsets.start + offsets.end
  )`
- Define `embedding_params_hash = sha256(canonical_json(embedder_params))`
- Define `embedding_id = sha256(
    chunk_id
    + embedder_name + embedder_version + embedding_params_hash
    + index_target
  )`

IDs must be stable across retries.

### Registries are authoritative
- Chunking Registry is the source of truth for “what chunks exist and where”.
- Embedding Registry is the source of truth for “what got embedded/indexed, with what model, when, and where”.

### Async embedding
Embedding workers run independently, out-of-order, with retries. Registry writes must be:
- idempotent
- safe under concurrency
- track status transitions (STARTED -> SUCCEEDED/FAILED), and allow multiple attempts.

## Deliverables

### 1) Data model (schemas)
Implement schemas and storage for both registries (choose one storage option; default: Parquet on S3 with partitioning by date and/or run_id, plus a compacted “latest” table; or Postgres if simpler).
Provide CREATE TABLE if using SQL.

#### Chunking Registry schema (minimum)
- chunk_id (PK)
- source_dataset_urn
- source_s3_uri (or canonical source uri)
- source_content_hash
- chunk_s3_uri (location of stored chunk object)
- offsets_start
- offsets_end
- breadcrumb (optional)
- chunk_text_hash (sha256)
- chunker_name
- chunker_version
- chunk_params_hash
- chunking_run_id
- created_at (timestamp)
- observed_at (timestamp)  # last time seen/verified
- status (ENUM: ACTIVE, DELETED, SUPERSEDED)  # choose minimal status semantics

#### Embedding Registry schema (minimum)
- embedding_id (PK)  # deterministic
- chunk_id (FK to chunking registry)
- index_target (e.g. "qdrant://collection=x" or "pgvector://schema.table")
- embedder_name
- embedder_version
- embedding_params_hash
- embedding_dim
- embedding_vector_hash (optional)  # hash of embedding bytes if you want
- embedding_run_id
- chunking_run_id (copied for convenience)
- attempt (int)
- status (ENUM: STARTED, SUCCEEDED, FAILED)
- error_message (nullable)
- started_at
- finished_at (nullable)
- upserted_at (timestamp)
- vector_record_id (id used in vector db, typically chunk_id or embedding_id)

Add any extra fields you need for your runtime (tenant, domain, namespace, etc).

### 2) Canonical provenance envelope
Implement:
- `build_chunk_envelope(...) -> dict` (for chunk objects and registry writes)
- `build_embedding_envelope(...) -> dict` (for vector records and embedding registry writes)
Ensure envelopes contain all fields to join across registries by chunk_id.

### 3) Writers with idempotency + concurrency safety
Implement registry writers that support:
- upsert semantics by PK
- status transitions with optimistic concurrency (if DB) or “append + compact” (if S3 parquet)
- ability to query:
  - by chunk_id
  - by source_dataset_urn + source_content_hash
  - by chunking_run_id
  - embedding latest for a chunk_id and index_target

If using S3 parquet:
- Write append-only partitions (e.g., dt=YYYY-MM-DD/run_id=...)
- Provide a compaction job that materializes “latest state” tables for fast lookup.

### 4) Pipeline integration
Update pipeline stages:

#### Chunking stage
For each input file:
- compute source_content_hash
- chunk into segments
- for each segment:
  - compute chunk_id deterministically
  - write chunk object to S3 at chunk_s3_uri (include envelope metadata in object)
  - write row to chunking registry (upsert/append)
At end of run:
- produce a run manifest (optional) OR rely on chunking_run_id partition in registry.

#### Embedding stage (async workers)
Each worker receives (chunking_run_id, batch_id) OR queries chunking registry for unembedded chunks:
- mark embedding registry row as STARTED with attempt increment
- compute embedding
- upsert embedding to vector DB with metadata including chunk_id + embedding_id + versions + run ids
- mark embedding registry row SUCCEEDED with finished_at
On error:
- mark FAILED with error_message

### 5) DataHub modeling (dataset-level only)
Emit DataHub entities and lineage:
- Dataset: source file datasets (already)
- Dataset: chunk_store_dataset (S3 prefix)
- Dataset: chunking_registry_dataset (table/prefix)
- Dataset: vector_index_dataset (vector collection)
- Dataset: embedding_registry_dataset (table/prefix)

Static lineage:
- source_file_dataset -> chunking_job -> chunk_store_dataset
- chunking_job -> chunking_registry_dataset
- chunking_registry_dataset -> embedding_job -> vector_index_dataset
- embedding_job -> embedding_registry_dataset

Runtime lineage (DPI):
- chunking DPI includes manifest/partition pointer and chunk_count
- embedding DPI includes processed_count, batch_id, and references to chunking_run_id

IMPORTANT: Do NOT create a DataHub Dataset per chunk.

### 6) Queries / APIs to implement
Provide functions:
- `get_chunk_provenance(chunk_id) -> {source_urn, source_hash, chunk_s3_uri, offsets, chunker...}`
- `get_embedding_provenance(chunk_id, index_target) -> {embedding_id, embedder..., status, run_ids, vector_record_id}`
- `trace_from_vector_result(chunk_id) -> full chain`

### 7) Testing
Add unit tests for:
- deterministic chunk_id
- deterministic embedding_id
- registry upsert/idempotency behavior
- status transition logic (STARTED->SUCCEEDED, retries)
- concurrency safety strategy (append+compact or db upsert)

## Output format
- Provide file-by-file code blocks with paths.
- Include a short README explaining:
  - registry storage choice
  - how to trace a chunk from vector DB back to source and runs
  - how async embedding is represented
  - how DataHub lineage remains readable