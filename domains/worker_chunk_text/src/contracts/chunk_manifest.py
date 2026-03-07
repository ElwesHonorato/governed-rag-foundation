"""Typed chunk manifest contract for worker_chunk_text outputs."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Literal, Mapping

CHUNK_MANIFEST_SCHEMA_VERSION = "1.0"
RunStatus = Literal["partial", "complete", "failed"]


@dataclass(frozen=True)
class ChunkManifestLineage:
    source_asset_id: str
    source_hash: str
    content_type: str
    document_hash: str
    parser_version: str

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "ChunkManifestLineage":
        return cls(**data)


@dataclass(frozen=True)
class ChunkerConfig:
    class_name: str
    params: dict[str, Any]

    @classmethod
    def from_chunking_params(cls, chunking_params: Mapping[str, Any]) -> "ChunkerConfig":
        chunker = chunking_params["chunker"]
        class_name = getattr(chunker, "__name__", str(chunker))
        return cls(
            class_name=str(class_name),
            params=dict(chunking_params["params"]),
        )

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "ChunkerConfig":
        return cls(
            class_name=str(data["class_name"]),
            params=dict(data["params"]),
        )


@dataclass(frozen=True)
class ChunkManifestProcessing:
    run_id: str
    stage: str
    timestamp: str
    chunker_version: str
    run_status: RunStatus
    chunker: ChunkerConfig

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "ChunkManifestProcessing":
        return cls(
            run_id=str(data["run_id"]),
            stage=str(data["stage"]),
            timestamp=str(data["timestamp"]),
            chunker_version=str(data["chunker_version"]),
            run_status=data["run_status"],
            chunker=ChunkerConfig.from_dict(data["chunker"]),
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
    lineage: ChunkManifestLineage
    processing: ChunkManifestProcessing
    output: ChunkManifestOutput
    chunks: list[ChunkManifestEntry]

    @classmethod
    def build(
        cls,
        doc_id: str,
        lineage: ChunkManifestLineage,
        processing: ChunkManifestProcessing,
        output: ChunkManifestOutput,
        chunks: list[ChunkManifestEntry],
    ) -> "ChunkManifest":
        return cls(
            schema_version=CHUNK_MANIFEST_SCHEMA_VERSION,
            doc_id=str(doc_id),
            lineage=lineage,
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
            lineage=ChunkManifestLineage.from_dict(data["lineage"]),
            processing=ChunkManifestProcessing.from_dict(data["processing"]),
            output=ChunkManifestOutput.from_dict(data["output"]),
            chunks=[ChunkManifestEntry.from_dict(item) for item in data["chunks"]],
        )
