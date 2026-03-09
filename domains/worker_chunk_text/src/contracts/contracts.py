"""Unified worker_chunk_text contracts, ordered high-level to low-level."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from pipeline_common.stages_contracts import ChunkArtifactPayload
from pipeline_common.stages_contracts.step_00_common import ProcessorMetadata, SourceDocumentMetadata

CHUNK_MANIFEST_SCHEMA_VERSION = "1.0"


class ChunkExecutionStatus(str, Enum):
    FAIL = "fail"
    SUCCESS = "success"
    PARTIAL = "partial"


@dataclass(frozen=True)
class ChunkTextQueueConfigContract:
    stage: str
    queue_pop_timeout_seconds: int
    pop_timeout_seconds: int
    consume: str
    produce: str
    dlq: str


@dataclass(frozen=True)
class ChunkTextJobConfigContract:
    bucket: str
    input_prefix: str
    output_prefix: str
    poll_interval_seconds: int


@dataclass(frozen=True)
class ChunkTextStorageConfigContract:
    bucket: str
    input_prefix: str
    output_prefix: str


@dataclass(frozen=True)
class ChunkTextProcessingConfigContract:
    poll_interval_seconds: int
    queue: ChunkTextQueueConfigContract
    storage: ChunkTextStorageConfigContract


@dataclass(frozen=True)
class ChunkTextWorkerConfigContract:
    storage: ChunkTextStorageConfigContract
    poll_interval_seconds: int
    queue_config: ChunkTextQueueConfigContract


@dataclass(frozen=True)
class ChunkingExecutionResult:
    chunk_count_expected: int
    chunk_count_written: int
    chunk_entries: list[dict[str, Any]]
    chunking_params: dict[str, Any]
    status: ChunkExecutionStatus = field(init=False)

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "status",
            self.resolve_status(
                chunk_count_expected=self.chunk_count_expected,
                chunk_count_written=self.chunk_count_written,
            ),
        )

    @classmethod
    def resolve_status(cls, *, chunk_count_expected: int, chunk_count_written: int) -> ChunkExecutionStatus:
        if chunk_count_written == chunk_count_expected:
            return ChunkExecutionStatus.SUCCESS
        if chunk_count_written > 0:
            return ChunkExecutionStatus.PARTIAL
        return ChunkExecutionStatus.FAIL


@dataclass(frozen=True)
class ChunkArtifactRecord:
    payload: ChunkArtifactPayload
    destination_key: str
    chunk_id: str
    chunk_index: int
    chunk_text_hash: str


@dataclass(frozen=True)
class ProcessResult:
    run_id: str
    source_metadata: SourceDocumentMetadata
    source_uri: str
    input_content_hash: str
    processor: ProcessorMetadata
    result: ChunkingExecutionResult


@dataclass(frozen=True)
class ChunkBuildContext:
    run_id: str
    chunk_params_hash: str
    chunking_params: dict[str, Any]


@dataclass(frozen=True)
class ResolvedChunkContent:
    chunk_id: str
    chunk_text: str
    offsets_start: int
    offsets_end: int
    chunk_text_hash: str
