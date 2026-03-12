# Worker Chunk Text Contract Inventory

This document lists the contracts used by `domains/worker_chunk_text`, grouped by use type.

## Startup And Worker Wiring

| Name | Brief Description | Location |
| --- | --- | --- |
| `ChunkTextJobConfigContract` | Raw job-level config parsed directly from `job_properties`. | `domains/worker_chunk_text/src/contracts/contracts.py` |
| `RawStoragePathsContract` | Raw storage paths declared in job properties before environment scoping. | `domains/worker_chunk_text/src/contracts/contracts.py` |
| `RuntimeStoragePathsContract` | Environment-dependent runtime storage paths built from raw storage paths during startup extraction. | `domains/worker_chunk_text/src/contracts/contracts.py` |
| `ChunkTextQueueConfigContract` | Queue timing and routing config for the worker. | `domains/worker_chunk_text/src/contracts/contracts.py` |
| `WorkerRuntimeContext` | Shared runtime dependency bundle injected into the service factory and built in `app.py`. | `libs/pipeline-common/src/pipeline_common/startup/runtime_context.py` |
| `WorkerServiceFactory` | Startup contract implemented by `ChunkTextServiceFactory` to build the concrete worker service. | `libs/pipeline-common/src/pipeline_common/startup/contracts.py` |

## Worker Service Contract

| Name | Brief Description | Location |
| --- | --- | --- |
| `WorkerService` | Shared lifecycle contract implemented by `WorkerChunkingService` via `serve()`. | `libs/pipeline-common/src/pipeline_common/startup/contracts.py` |

## Processing Output And Manifest Contracts

| Name | Brief Description | Location |
| --- | --- | --- |
| `ProcessResult` | Top-level result payload returned by `ChunkTextProcessor` and consumed by manifest writers and factories. | `domains/worker_chunk_text/src/contracts/contracts.py` |
| `ProcessorContext` | Captures processor parameter hash and normalized params for the run result. | `domains/worker_chunk_text/src/contracts/contracts.py` |
| `ChunkingExecutionResult` | Summarizes expected vs written chunks and derives execution status. | `domains/worker_chunk_text/src/contracts/contracts.py` |
| `ChunkExecutionStatus` | Enum for `success`, `partial`, and `fail`, used through `ChunkingExecutionResult.status`. | `domains/worker_chunk_text/src/contracts/contracts.py` |
| `ChunkMetadata` | Metadata attached to each persisted chunk artifact. | `domains/worker_chunk_text/src/contracts/contracts.py` |
| `StorageStageArtifact` | Wraps a chunk `StageArtifact` plus destination key before writing to storage. | `domains/worker_chunk_text/src/contracts/contracts.py` |

## Shared Stage And Content Contracts

| Name | Brief Description | Location |
| --- | --- | --- |
| `StageArtifact` | Shared artifact envelope read from input storage and written for chunk outputs. | `libs/pipeline-common/src/pipeline_common/stages_contracts` |
| `StageArtifactMetadata` | Metadata wrapper used when constructing new chunk artifacts. | `libs/pipeline-common/src/pipeline_common/stages_contracts` |
| `Content` | Content payload wrapper used when writing chunk artifacts. | `libs/pipeline-common/src/pipeline_common/stages_contracts` |
| `SourceDocumentMetadata` | Shared source-document metadata embedded in `ProcessResult` and reused from input artifacts. | `libs/pipeline-common/src/pipeline_common/stages_contracts/step_00_common.py` |
| `ProcessorMetadata` | Shared processor descriptor embedded in `ProcessResult` and artifact metadata. | `libs/pipeline-common/src/pipeline_common/stages_contracts/step_00_common.py` |

## Queue And Messaging Contracts

| Name | Brief Description | Location |
| --- | --- | --- |
| `ConsumedMessage` | Queue-consumer handle used by `WorkerChunkingService` for `ack()` and `nack()`. | `libs/pipeline-common/src/pipeline_common/gateways/queue` |
| `Envelope` | Queue message envelope used to parse incoming payloads and publish DLQ messages. | `libs/pipeline-common/src/pipeline_common/gateways/queue` |

## Defined But Not Used Directly In The Current Runtime Path

| Name | Brief Description | Location |
| --- | --- | --- |
| `ChunkTextProcessingConfigContract` | Runtime processing config returned by the extractor after environment scoping. | `domains/worker_chunk_text/src/contracts/contracts.py` |
| `ChunkingStrategy` | Exported by the contracts package, but not referenced in the current worker runtime path. | `domains/worker_chunk_text/src/contracts/chunking_strategy.py` |

## Summary

- Startup uses local config contracts plus shared startup contracts from `pipeline_common.startup`.
- Runtime processing uses local result and artifact contracts defined in `domains/worker_chunk_text/src/contracts/contracts.py`.
- The worker also depends on shared stage and queue contracts from `pipeline_common`.
