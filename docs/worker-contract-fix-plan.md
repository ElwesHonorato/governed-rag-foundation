# Worker Contract Fix Plan

## Purpose

This document turns the worker contract assessment into a concrete remediation plan.

Scope:

- `domains/worker_parse_document`
- `domains/worker_chunk_text`
- `domains/worker_embed_chunks`
- `domains/worker_index_weaviate`
- `libs/pipeline-common/src/pipeline_common/stages_contracts`

Primary goal:

- make declared contracts match actual persisted artifacts and runtime usage
- reduce contract duplication and schema drift
- improve clarity without changing business behavior

## Principles

- Fix correctness before improving style.
- Preserve persisted payload compatibility unless a coordinated contract break is explicitly chosen.
- Prefer one canonical contract per persisted artifact.
- Keep transport contracts small and stage-owned.
- Avoid adding new generic shared abstractions unless multiple workers truly need them.

## Workstreams

## 1. Repair Invalid Chunk-Text Contracts

### Problem

This issue is completed.

`domains/worker_chunk_text/src/processor/metadata.py` now matches the fields actually produced and consumed by `domains/worker_chunk_text/src/processor/chunk_text.py`.

Current impact:

- the declared contract cannot be trusted as the canonical schema
- docs and code can drift independently
- downstream reasoning about the chunk artifact is weakened

### Action

Reconcile the contract definitions with runtime usage.

Choose one of two directions:

1. Update the dataclasses to match the actual runtime payload fields.
2. Change the runtime code to emit the currently declared schema.

Recommended direction:

- update the dataclasses to match runtime usage, because the current runtime shape is already the one flowing through the worker pipeline

### Deliverables

- aligned `ChunkMetadata`
- aligned `ChunkingExecutionMetadata`
- updated docs in:
  - `domains/worker_chunk_text/docs/CONTRACT_INVENTORY.md`
  - `domains/worker_chunk_text/README.md`

### Acceptance criteria

- the declared dataclass fields exactly match the runtime constructor usage
- no worker code refers to stale field names
- documentation uses the same field names as the code

## 2. Simplify Embedding Artifact Metadata

### Problem

`EmbeddingArtifactMetadata` currently duplicates values already present in:

- `root_doc_metadata`
- `stage_doc_metadata`

Duplicated fields:

- `source_type`
- `timestamp`
- `security_clearance`
- `doc_id`
- `source_uri`

This creates two sources of truth.

### Action

Reduce `EmbeddingArtifactMetadata` to fields that are truly embedding-specific.

Recommended retained fields:

- `run_id`
- `embedder_name`
- `embedder_version`
- `embedding_params_hash`
- `embedding_run_id`
- `root_doc_metadata`
- `stage_doc_metadata`

Recommended top-level artifact fields:

- `doc_id`
- `chunk_id`
- `chunk_text`
- `vector`

### Compatibility note

This is a serialized contract change.

Do not do it silently.

Choose one of:

1. Keep current payload compatibility and postpone the cleanup.
2. Make a coordinated contract break and update both writer and reader together.

Recommended direction:

- treat this as a planned follow-up contract change, not an opportunistic refactor

### Deliverables

- updated `EmbeddingArtifactMetadata`
- updated embed writer
- updated index reader
- explicit note in docs that the embedding artifact schema changed

## 3. Remove Misleading Deserialization APIs

### Problem

This issue is completed.

`StorageStageArtifact.from_dict()` has been removed.

### Action

Completed direction:

- removed it because no real read path exists

### Deliverables

- deleted `StorageStageArtifact.from_dict()`
- no remaining call sites depending on the fake parser

## 4. Clarify Execution vs Artifact Contracts

### Problem

The current shared contract layer mixes:

- persisted artifact contracts
- runtime execution bookkeeping
- storage-write helper wrappers

Examples:

- `StageArtifact`
- `ProcessResult`
- `StorageStageArtifact`
- `ProcessorContext`

### Action

Separate concerns conceptually, even if files are not moved immediately.

Short-term:

- document the distinction clearly
- stop describing execution/result types as artifact schemas

Mid-term:

- consider moving execution/result types closer to manifest/runtime handling if shared reuse remains weak

### Deliverables

- updated docs
- tighter naming and descriptions for execution/result contracts

## 5. Standardize Startup Contract Naming

### Problem

This issue is completed.

Chunk startup contracts now use `*Config`, matching parse/embed/index.

### Action

Completed direction:

- standardized on `*Config`

### Compatibility note

This is an internal code cleanup, not a serialized payload change.

### Deliverables

- renamed startup config contracts
- aligned imports and docs

## 6. Tighten Shared Contract Typing

### Problem

The shared contract layer still relies on `Any` in one key place:

- `StageArtifactMetadata.content_metadata`

This weakens the claim that the system has strong contracts.

### Action

Do not rush to generic-heavy abstractions.

Instead:

1. keep shared contracts minimal
2. move stage-specific payload typing into worker-local dataclasses
3. narrow the remaining `Any` usage by convention and local adapters first

Recommended direction:

- keep `ProcessResult.result` serialized as a dict
- introduce worker-local typed payload/result dataclasses before considering shared generics

### Deliverables

- explicit stage-local payload/result dataclasses where high-value
- reduced informal dict usage in worker-local result payloads

## 7. Formalize Write-Only Artifact Strategy

### Problem

This issue is completed.

The index status object now has an explicit `IndexStatusArtifact` write contract, even though it remains write-only.

### Action

Completed direction:

- the write-only status payload now uses an explicit contract

### Deliverables

- documentation note in contract guidance
- explicit `IndexStatusArtifact` contract

## Recommended Order

### Completed

1. Repaired `worker_chunk_text` metadata contracts.
2. Removed `StorageStageArtifact.from_dict()`.
3. Standardized startup contract naming.
4. Simplified `EmbeddingArtifactMetadata`.
5. Added `IndexStatusArtifact`.
6. Renamed `StageArtifactMetadata.content` to `content_metadata`.
7. Kept `ProcessResult.result` serialized as a dict.

### Remaining

1. Clarify execution vs artifact contracts in docs and package boundaries.
2. Introduce more stage-local typed payload/result contracts where they pay for themselves.

## Risks

### Low risk

- contract documentation cleanup

### Medium risk

- tightening the remaining shared `content_metadata` typing if downstream workers diverge

### High risk

- changing shared stage contract field names

## Definition of Done

- declared contracts match actual runtime usage
- each persisted stage artifact has one canonical writer and one canonical reader contract
- no duplicated metadata fields remain without explicit justification
- no misleading deserialization APIs remain
- worker docs and contract docs match the implemented schemas

## Proposed Follow-Up Tasks

1. Keep `EmbeddingArtifactMetadata` simplified and aligned if new fields are proposed.
2. Tighten `StageArtifactMetadata.content_metadata` only when a real shared shape emerges.
3. Add a short contract policy doc for:
   - persisted artifact contracts
   - write-only payloads
   - transport-only work-item contracts
