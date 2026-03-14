"""Stage 10 parser contracts."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Mapping

from pipeline_common.stages_contracts.step_00_common import FileMetadata, ProcessorMetadata


@dataclass(frozen=True)
class Content:
    """Standard stage content contract with one data entry."""

    data: Any

    @property
    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class StageArtifactMetadata:
    processor: ProcessorMetadata
    root_doc_metadata: FileMetadata
    stage_doc_metadata: FileMetadata
    content_metadata: Any
    params: list[dict[str, Any]]


@dataclass(frozen=True)
class StageArtifact:
    """Shared base payload for cross-worker artifact contracts."""

    metadata: StageArtifactMetadata
    content: Content

    @property
    def root_doc_metadata(self) -> FileMetadata:
        return self.metadata.root_doc_metadata

    @property
    def stage_doc_metadata(self) -> FileMetadata:
        return self.metadata.stage_doc_metadata

    @property
    def processor_metadata(self) -> ProcessorMetadata:
        return self.metadata.processor

    @property
    def content_metadata(self) -> Any:
        return self.metadata.content_metadata

    @property
    def params(self) -> list[dict[str, Any]]:
        return self.metadata.params

    @classmethod
    def from_dict(
        cls,
        payload: Mapping[str, Any],
    ) -> "StageArtifact":
        """Parse payload dict into typed processed-document contract."""
        metadata_payload = payload["metadata"]
        return cls(
            metadata=StageArtifactMetadata(
                processor=ProcessorMetadata(**metadata_payload["processor"]),
                root_doc_metadata=FileMetadata.from_dict(metadata_payload["root_doc_metadata"]),
                stage_doc_metadata=FileMetadata.from_dict(metadata_payload["stage_doc_metadata"]),
                content_metadata=metadata_payload["content_metadata"],
                params=metadata_payload["params"],
            ),
            content=Content(**payload["content"]),
        )

    @property
    def to_dict(self) -> dict[str, Any]:
        """Serialize payload for object storage persistence."""
        return asdict(self)
