"""Stage 10 parser contracts."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Mapping

from pipeline_common.stages_contracts.step_00_common import ProcessorMetadata, RootDocumentMetadata


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
    root: RootDocumentMetadata
    content: Any
    params: list[dict[str, Any]]


@dataclass(frozen=True)
class StageArtifact:
    """Shared base payload for cross-worker artifact contracts."""

    metadata: StageArtifactMetadata
    content: Content

    @property
    def root_metadata(self) -> RootDocumentMetadata:
        return self.metadata.root

    @property
    def processor_metadata(self) -> ProcessorMetadata:
        return self.metadata.processor

    @property
    def content_metadata(self) -> Any:
        return self.metadata.content

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
                root=RootDocumentMetadata(**metadata_payload["root"]),
                content=metadata_payload["content"],
                params=metadata_payload["params"],
            ),
            content=Content(**payload["content"]),
        )

    @property
    def to_dict(self) -> dict[str, Any]:
        """Serialize payload for object storage persistence."""
        return asdict(self)
