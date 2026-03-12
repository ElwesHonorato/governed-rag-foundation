# Worker Chunk Text Contract Inventory

This document lists the contracts used by `domains/worker_chunk_text`, grouped by use type.

## Startup And Worker Wiring

| Name | Brief Description | Location |
| --- | --- | --- |
| `RawChunkJobConfig` | Raw job-level config parsed directly from `job_properties`. | `domains/worker_chunk_text/src/startup/contracts.py` |
| `RawStoragePathsContract` | Raw storage paths declared in job properties before environment scoping. | `domains/worker_chunk_text/src/startup/contracts.py` |
| `RuntimeStoragePathsContract` | Environment-dependent runtime storage paths built from raw storage paths during startup extraction. | `domains/worker_chunk_text/src/startup/contracts.py` |
| `WorkerRuntimeContext` | Shared runtime dependency bundle injected into the service factory and built in `app.py`. | `libs/pipeline-common/src/pipeline_common/startup/runtime_context.py` |
| `WorkerServiceFactory` | Startup contract implemented by `ChunkTextServiceFactory` to build the concrete worker service. | `libs/pipeline-common/src/pipeline_common/startup/contracts.py` |

## Worker Service Contract

| Name | Brief Description | Location |
| --- | --- | --- |
| `WorkerService` | Shared lifecycle contract implemented by `WorkerChunkingService` via `serve()`. | `libs/pipeline-common/src/pipeline_common/startup/contracts.py` |

## Processing Output And Manifest Contracts

| Name | Brief Description | Location |
| --- | --- | --- |
| `ProcessResult` | Top-level result payload returned by `ChunkTextProcessor` and consumed by manifest writers and factories. | `libs/pipeline-common/src/pipeline_common/stages_contracts/execution.py` |
| `ProcessorContext` | Captures processor parameter hash and normalized params for the run result. | `libs/pipeline-common/src/pipeline_common/stages_contracts/execution.py` |
| `ChunkingExecutionMetadata` | Summarizes expected vs written chunks and derives execution status. | `domains/worker_chunk_text/src/processor/metadata.py` |
| `ExecutionStatus` | Enum for `success`, `partial`, and `fail`, used through `ChunkingExecutionMetadata.status`. | `libs/pipeline-common/src/pipeline_common/stages_contracts/execution.py` |
| `ChunkMetadata` | Metadata attached to each persisted chunk artifact, including source URI, ordinal, and character count. | `domains/worker_chunk_text/src/processor/metadata.py` |
| `StorageStageArtifact` | Wraps a chunk `StageArtifact` plus destination key before writing to storage. | `libs/pipeline-common/src/pipeline_common/stages_contracts/execution.py` |

## Shared Stage And Content Contracts

| Name | Brief Description | Location |
| --- | --- | --- |
| `StageArtifact` | Shared artifact envelope read from input storage and written for chunk outputs. | `libs/pipeline-common/src/pipeline_common/stages_contracts` |
| `StageArtifactMetadata` | Metadata wrapper used when constructing new chunk artifacts. | `libs/pipeline-common/src/pipeline_common/stages_contracts` |
| `Content` | Content payload wrapper used when writing chunk artifacts. | `libs/pipeline-common/src/pipeline_common/stages_contracts` |
| `RootDocumentMetadata` | Shared root-document metadata embedded in `ProcessResult` and reused from input artifacts. | `libs/pipeline-common/src/pipeline_common/stages_contracts/step_00_common.py` |
| `ProcessorMetadata` | Shared processor descriptor embedded in `ProcessResult` and artifact metadata. | `libs/pipeline-common/src/pipeline_common/stages_contracts/step_00_common.py` |

## Queue And Messaging Contracts

| Name | Brief Description | Location |
| --- | --- | --- |
| `ConsumedMessage` | Queue-consumer handle used by `WorkerChunkingService` for `ack()` and `nack()`. | `libs/pipeline-common/src/pipeline_common/gateways/queue` |
| `Envelope` | Queue message envelope used to parse incoming payloads and publish DLQ messages. | `libs/pipeline-common/src/pipeline_common/gateways/queue` |

## Defined But Not Used Directly In The Current Runtime Path

| Name | Brief Description | Location |
| --- | --- | --- |
| `RuntimeChunkJobConfig` | Runtime processing config returned by the extractor after environment scoping. | `domains/worker_chunk_text/src/startup/contracts.py` |

## Summary

- Startup uses local config contracts plus shared startup contracts from `pipeline_common.startup`.
- Runtime processing uses shared result and artifact contracts from `pipeline_common.stages_contracts` plus local chunk-text execution contracts.
- The worker also depends on shared stage and queue contracts from `pipeline_common`.
