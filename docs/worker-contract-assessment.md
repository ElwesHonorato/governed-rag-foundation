# Worker Contract Assessment

## Scope

This assessment covers the current contracts used across:

- `domains/worker_parse_document`
- `domains/worker_chunk_text`
- `domains/worker_embed_chunks`
- `domains/worker_index_weaviate`
- `libs/pipeline-common/src/pipeline_common/stages_contracts`

The review focuses on:

- contract naming conventions
- responsibility boundaries
- duplication and schema drift
- serialization patterns
- stage artifact consistency across workers
- metadata handling
- typing quality
- alignment between persisted artifacts and their reader/writer contracts

## Findings

### 1. High: persisted artifact contracts and execution/runtime helpers still share one package

`StageArtifact`, `ProcessResult`, `ProcessorContext`, and `StorageStageArtifact` still live together in `pipeline_common/stages_contracts` even though they do not represent the same kind of boundary.

Current impact:

- persisted artifact schemas and runtime helper payloads are described as if they were one contract layer
- the package boundary encourages implementation helpers to look more canonical than they really are
- future workers are likely to keep adding runtime wrappers to the same shared namespace

### 2. Medium: shared stage contracts are still under-typed in stage-specific payload sections

Two shared contracts still rely on `Any` in places where stage-specific payload structure matters:

- `StageArtifactMetadata.content_metadata`

`ProcessResult.result` is now consistently serialized as a dict, which is better, but stage-specific artifact metadata is still weakly typed in the shared envelope.

### 3. Low: startup contract naming is now aligned, but the contract package boundary is still muddy

The startup config contracts are now aligned on `*Config`, which removed the most obvious naming drift. The remaining issue is not naming but placement: execution/result helper contracts still sit beside persisted artifact contracts in the same shared package.

### 4. Low: explicit write contracts now exist even for write-only index status payloads

`IndexStatusArtifact` is now a real write contract instead of an ad hoc dict. That is an improvement, but the repository still does not have a concise shared rule explaining when a write-only payload should stay local versus when it should graduate into a canonical cross-stage artifact.

### 5. Low: execution helpers still live in the shared contract package

`ProcessResult`, `ProcessorContext`, and `StorageStageArtifact` are runtime/execution helpers, not inter-worker artifact schemas. Keeping them in the same shared contract package as persisted artifacts still blurs the boundary.

## Contract Inventory

## Shared Stage Contracts

### Metadata Contracts

- `FileMetadata`
- `ProcessorMetadata`

Location:

- `libs/pipeline-common/src/pipeline_common/stages_contracts/step_00_common.py`

Role:

- canonical shared metadata for persisted stage artifacts and process results

### Stage / Artifact Contracts

- `Content`
- `StageArtifactMetadata`
- `StageArtifact`

Location:

- `libs/pipeline-common/src/pipeline_common/stages_contracts/step_10_artifact_payloads.py`

Role:

- canonical cross-stage persisted artifact contract

### Execution / Manifest Contracts

- `ExecutionStatus`
- `ProcessorContext`
- `ProcessResult`
- `StorageStageArtifact`

Location:

- `libs/pipeline-common/src/pipeline_common/stages_contracts/execution.py`

Role:

- runtime execution summary contracts and stage-artifact wrapper for storage writes

## Worker-Local Contracts

### Parse Worker

Location:

- `domains/worker_parse_document/src/startup/contracts.py`
- `domains/worker_parse_document/src/services/parse_output.py`

Contracts:

- `RawParseStorageConfig`
- `RuntimeParseStorageConfig`
- `RuntimeParseSecurityConfig`
- `RawParseJobConfig`
- `RuntimeParseJobConfig`
- `ParseWorkItem`

Role:

- startup/config extraction contracts
- queue transport contract

### Chunk Worker

Location:

- `domains/worker_chunk_text/src/startup/contracts.py`
- `domains/worker_chunk_text/src/processor/metadata.py`

Contracts:

- `RawChunkStorageConfig`
- `RuntimeChunkStorageConfig`
- `RawChunkJobConfig`
- `RuntimeChunkJobConfig`
- `ChunkingExecutionMetadata`
- `ChunkMetadata`

Role:

- startup config contracts
- chunk processor-local metadata/result contracts

### Embed Worker

Location:

- `domains/worker_embed_chunks/src/startup/contracts.py`
- `domains/worker_embed_chunks/src/services/embed_flow.py`

Contracts:

- `RawEmbedChunksStorageConfig`
- `RuntimeEmbedChunksStorageConfig`
- `RawEmbedChunksJobConfig`
- `RuntimeEmbedChunksJobConfig`
- `EmbedWorkItem`
- `EmbeddingArtifactMetadata`
- `EmbeddingArtifact`

Role:

- startup config contracts
- queue transport contract
- canonical persisted embedding artifact contract

### Index Worker

Location:

- `domains/worker_index_weaviate/src/startup/contracts.py`
- `domains/worker_index_weaviate/src/services/index_flow.py`

Contracts:

- `RawIndexWeaviateStorageConfig`
- `RuntimeIndexWeaviateStorageConfig`
- `RawIndexWeaviateJobConfig`
- `RuntimeIndexWeaviateJobConfig`
- `IndexWorkItem`

Role:

- startup config contracts
- queue transport contract

Note:

- `IndexStatusWriter` lives beside the transport contract, but it is a helper/writer, not a schema contract.

## Classification By Responsibility

### Payload Contracts

- `Content`
- `EmbeddingArtifact`
- `EmbeddingArtifactMetadata`

### Metadata Contracts

- `FileMetadata`
- `ProcessorMetadata`
- `ChunkMetadata`
- `ChunkingExecutionMetadata`

### Execution / Result Contracts

- `ProcessorContext`
- `ProcessResult`
- `StorageStageArtifact`

### Configuration Contracts

- all `Raw*JobConfig`
- all `Runtime*JobConfig`
- all `Raw*StorageConfig` / `Runtime*StorageConfig`
- `RuntimeParseSecurityConfig`

### Stage / Artifact Contracts

- `StageArtifact`
- `StageArtifactMetadata`

### Transport Contracts

- `ParseWorkItem`
- `EmbedWorkItem`
- `IndexWorkItem`

## Serialization Review

## What is working well

- `FileMetadata` uses explicit `from_dict()` and `to_dict`.
- `StageArtifact` uses explicit `from_dict()` and `to_dict`.
- `ProcessResult` uses explicit `to_dict`.
- `StorageStageArtifact.to_payload` now writes the full canonical `StageArtifact`.
- `EmbeddingArtifact` now has explicit `from_dict()` and `to_dict()`.

## Current inconsistencies

- Stage-specific artifact metadata still flows through `Any` in the shared stage envelope, which weakens predictability.
- Execution/result helpers remain colocated with persisted artifact contracts in `pipeline_common/stages_contracts`.

## Stage Artifact Alignment

### Parse Artifact

Canonical contract:

- `StageArtifact`

Write path:

- `DocumentParserProcessor` builds and serializes `StageArtifact`

Read path:

- `WorkerChunkingService` reads with `StageArtifact.from_dict(...)`

Status:

- aligned

### Chunk Artifact

Canonical contract:

- `StageArtifact`

Write path:

- `ChunkTextProcessor` writes chunk artifacts via `StorageStageArtifact.to_payload`

Read path:

- `EmbedChunksProcessor` reads with `StageArtifact.from_dict(...)`

Status:

- aligned after fixing `StorageStageArtifact.to_payload` to persist the full artifact

### Embedding Artifact

Canonical contract:

- `EmbeddingArtifact`

Write path:

- `EmbedChunksProcessor` writes `EmbeddingArtifact.to_dict`

Read path:

- `IndexWeaviateProcessor` reads `EmbeddingArtifact.from_dict(...)`

Status:

- aligned

### Index Status Artifact

Canonical contract:

- `IndexStatusArtifact`

Write path:

- `IndexWeaviateProcessor.build_index_status_payload()`

Read path:

- none in the current worker pipeline

Status:

- aligned on an explicit write contract
- still write-only in the current pipeline

## Optimization Opportunities

### Immediate

1. Treat `StageArtifactMetadata.content_metadata` as the remaining weakly typed shared seam and tighten it only if multiple workers can agree on a real shared shape.
2. Clarify the package boundary between persisted artifact contracts and execution/runtime helper contracts.

### Near-term

3. Continue simplifying stage-local result payloads by replacing ad hoc dict construction with worker-local result contracts where it materially improves readability.
4. Simplify `EmbeddingArtifactMetadata` by removing duplicated fields already present in:
   - `root_doc_metadata`
   - `stage_doc_metadata`
5. Keep startup config naming aligned across workers as new workers are added.

### Longer-term

6. Replace `Any` in stage-specific artifact metadata sections with worker-local typed dataclasses where practical.

## Recommended Refactors

### 1. Reduce duplication in embedding artifact metadata

Preferred direction:

- keep:
  - `run_id`
  - embedder fields
  - `root_doc_metadata`
  - `stage_doc_metadata`
- drop:
  - `source_type`
  - `timestamp`
  - `security_clearance`
  - `doc_id`
  - `source_uri`

Those values can be derived from the nested metadata contracts instead of being duplicated.

### 2. Keep startup config naming aligned

The chunk worker is now on the same `*Config` naming style as parse/embed/index. Preserve that standard as the worker set grows.

### 3. Keep execution helpers distinct from artifact schemas

`ProcessResult`, `ProcessorContext`, and `StorageStageArtifact` should continue to be described as execution/runtime helpers, not as canonical persisted artifact contracts.

## Example Improved Contract Direction

For embedding artifacts, the cleaner metadata shape is:

```python
@dataclass(frozen=True)
class EmbeddingArtifactMetadata:
    run_id: str
    embedder_name: str
    embedder_version: str
    embedding_params_hash: str
    embedding_run_id: str
    root_doc_metadata: FileMetadata
    stage_doc_metadata: FileMetadata

@dataclass(frozen=True)
class EmbeddingArtifact:
    doc_id: str
    chunk_id: str
    chunk_text: str
    vector: list[float]
    metadata: EmbeddingArtifactMetadata
```

This keeps one source of truth for document metadata and one source of truth for embedder/runtime metadata.

## Summary

The contract layer is substantially cleaner than it was:

- `StageArtifact` is the canonical persisted contract for parse and chunk stages
- `EmbeddingArtifact` is the canonical persisted contract for the embedding stage
- `IndexStatusArtifact` is the canonical write contract for index status payloads
- writer and reader contracts are aligned across the stage chain for persisted artifacts

The main remaining maintainability problems are now narrower:

- persisted artifact schemas and execution/runtime helpers still share one package
- `StageArtifactMetadata.content_metadata` remains weakly typed
- the repository still lacks a concise rule for where write-only contracts should live

The highest-value next step is to clarify the package boundary between persisted artifact contracts and execution/runtime helpers before more workers copy the current mixed model.
