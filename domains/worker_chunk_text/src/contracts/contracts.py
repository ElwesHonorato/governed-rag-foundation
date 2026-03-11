"""Unified worker_chunk_text contracts, ordered high-level to low-level."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, ClassVar

from pipeline_common.stages_contracts import StageArtifact
from pipeline_common.stages_contracts.step_00_common import ProcessorMetadata, SourceDocumentMetadata


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

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> ChunkTextQueueConfigContract:
        normalized_payload = dict(payload)
        normalized_payload["queue_pop_timeout_seconds"] = int(normalized_payload["queue_pop_timeout_seconds"])
        normalized_payload["pop_timeout_seconds"] = int(normalized_payload["pop_timeout_seconds"])
        return cls(**normalized_payload)


@dataclass(frozen=True)
class ChunkTextJobConfigContract:
    storage: ChunkTextStorageConfigContract
    poll_interval_seconds: int

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> ChunkTextJobConfigContract:
        return cls(
            storage=ChunkTextStorageConfigContract.from_dict(payload["storage"]),
            poll_interval_seconds=int(payload["poll_interval_seconds"]),
        )


@dataclass(frozen=True)
class ChunkTextStorageConfigContract:
    bucket: str
    output_prefix: str
    manifest_prefix: str

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> ChunkTextStorageConfigContract:
        return cls(**payload)


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

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> ChunkTextWorkerConfigContract:
        return cls(
            storage=ChunkTextStorageConfigContract.from_dict(payload["storage"]),
            poll_interval_seconds=int(payload["poll_interval_seconds"]),
            queue_config=ChunkTextQueueConfigContract.from_dict(payload["queue_config"]),
        )


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
    SCHEMA_VERSION: ClassVar[str] = "1.0"
    schema_version: str = field(init=False)
    run_id: str
    source_metadata: SourceDocumentMetadata
    source_uri: str
    processor_context: ProcessorContext
    params: list[dict[str, Any]]
    processor: ProcessorMetadata
    result: ChunkingExecutionResult

    def __post_init__(self) -> None:
        object.__setattr__(self, "schema_version", self.SCHEMA_VERSION)

    @property
    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


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
    artifact: StageArtifact
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
        artifact: StageArtifact,
    ) -> StorageStageArtifact:
        _ = payload
        return cls(
            artifact=artifact,
            destination_key=destination_key,
        )
