"""Unified worker_chunk_text contracts, ordered high-level to low-level."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any

from pipeline_common.stages_contracts import StageArtifact
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
    chunk_entries: list[str]
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
class ProcessResult:
    run_id: str
    source_metadata: SourceDocumentMetadata
    source_uri: str
    processor_context: ProcessorContext
    params: list[dict[str, Any]]
    processor: ProcessorMetadata
    result: ChunkingExecutionResult


@dataclass(frozen=True)
class ProcessorContext:
    params_hash: str
    params: list[dict[str, Any]]


@dataclass(frozen=True)
class ChunkMetadata:
    index: int
    chunk_id: str
    offsets_start: int
    offsets_end: int
    chunk_text_hash: str

    @property
    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class StorageStageArtifact:
    artifact: StageArtifact[Any]
    destination_key: str

    @property
    def to_payload(self) -> dict[str, Any]:
        return self.artifact.content_metadata.to_dict

    @property
    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(
        cls,
        payload: dict[str, Any],
        *,
        destination_key: str,
        artifact: StageArtifact[Any],
    ) -> StorageStageArtifact:
        _ = payload
        return cls(
            artifact=artifact,
            destination_key=destination_key,
        )
