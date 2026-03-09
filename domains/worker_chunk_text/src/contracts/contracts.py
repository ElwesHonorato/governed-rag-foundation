"""Unified worker_chunk_text contracts, ordered high-level to low-level."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Literal, Mapping

from pipeline_common.stages_contracts import ChunkArtifactPayload
from pipeline_common.stages_contracts.step_00_common import ProcessorMetadata, SourceDocumentMetadata

CHUNK_MANIFEST_SCHEMA_VERSION = "1.0"
RunStatus = Literal["partial", "complete", "failed"]


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
class ChunkManifestProcessing:
    run_id: str
    stage: str
    timestamp: str
    chunker_version: str
    run_status: RunStatus

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "ChunkManifestProcessing":
        return cls(
            run_id=str(data["run_id"]),
            stage=str(data["stage"]),
            timestamp=str(data["timestamp"]),
            chunker_version=str(data["chunker_version"]),
            run_status=data["run_status"],
        )


@dataclass(frozen=True)
class ChunkManifestOutput:
    chunk_count_expected: int
    chunk_count_written: int

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "ChunkManifestOutput":
        return cls(
            chunk_count_expected=int(data["chunk_count_expected"]),
            chunk_count_written=int(data["chunk_count_written"]),
        )


@dataclass(frozen=True)
class ChunkManifestEntry:
    chunk_id: str
    chunk_index: int
    chunk_hash: str
    path: str

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "ChunkManifestEntry":
        return cls(
            chunk_id=str(data["chunk_id"]),
            chunk_index=int(data["chunk_index"]),
            chunk_hash=str(data["chunk_hash"]),
            path=str(data["path"]),
        )


@dataclass(frozen=True)
class ChunkManifest:
    schema_version: str
    doc_id: str
    processing: ChunkManifestProcessing
    output: ChunkManifestOutput
    chunks: list[ChunkManifestEntry]

    @classmethod
    def build(
        cls,
        doc_id: str,
        processing: ChunkManifestProcessing,
        output: ChunkManifestOutput,
        chunks: list[ChunkManifestEntry],
    ) -> "ChunkManifest":
        return cls(
            schema_version=CHUNK_MANIFEST_SCHEMA_VERSION,
            doc_id=str(doc_id),
            processing=processing,
            output=output,
            chunks=list(chunks),
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "ChunkManifest":
        return cls(
            schema_version=str(data["schema_version"]),
            doc_id=str(data["doc_id"]),
            processing=ChunkManifestProcessing.from_dict(data["processing"]),
            output=ChunkManifestOutput.from_dict(data["output"]),
            chunks=[ChunkManifestEntry.from_dict(item) for item in data["chunks"]],
        )


@dataclass(frozen=True)
class ChunkProcessOutput:
    chunk_count_expected: int
    chunk_count_written: int
    chunk_entries: list[ChunkManifestEntry]
    chunking_params: dict[str, Any]


@dataclass(frozen=True)
class ChunkArtifactRecord:
    payload: ChunkArtifactPayload
    destination_key: str
    chunk_id: str
    chunk_index: int
    chunk_text_hash: str


@dataclass(frozen=True)
class ChunkProcessResult:
    run_id: str
    source_metadata: SourceDocumentMetadata
    source_uri: str
    input_content_hash: str
    processor_metadata: ProcessorMetadata
    output: ChunkProcessOutput


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
