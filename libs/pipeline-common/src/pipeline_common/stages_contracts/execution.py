"""Shared execution and process result contracts."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, ClassVar

from pipeline_common.stages_contracts.step_00_common import FileMetadata, ProcessorMetadata
from pipeline_common.stages_contracts.step_10_artifact_payloads import StageArtifact


class ExecutionStatus(str, Enum):
    """Shared execution status values."""

    FAIL = "fail"
    SUCCESS = "success"
    PARTIAL = "partial"


@dataclass(frozen=True)
class ProcessorContext:
    """Processor parameter context captured for one execution."""

    params_hash: str
    params: list[dict[str, Any]]


@dataclass(frozen=True)
class ProcessResult:
    """Serializable result for one processing run.

    Attributes:
        schema_version: Serialized schema version for the result payload.
        run_id: Deterministic run identifier for this processing execution.
        root_doc_metadata: Root/original file metadata associated with the lineage chain.
        stage_doc_metadata: Metadata for the concrete input file consumed by this stage.
        input_uri: Fully qualified storage URI for the input artifact.
        processor_context: Serialized processor parameter context.
        processor: Processor metadata emitted for this run.
        result: Stage-specific serialized execution summary payload.
    """

    SCHEMA_VERSION: ClassVar[str] = "1.0"
    schema_version: str = field(init=False)
    run_id: str
    root_doc_metadata: FileMetadata
    stage_doc_metadata: FileMetadata
    input_uri: str
    processor_context: ProcessorContext
    processor: ProcessorMetadata
    result: dict[str, Any]

    def __post_init__(self) -> None:
        object.__setattr__(self, "schema_version", self.SCHEMA_VERSION)

    @property
    def to_dict(self) -> dict[str, Any]:
        """Build the manifest-ready dictionary representation.

        Returns:
            dict[str, Any]: Serialized form of the process result.
        """
        return asdict(self)


@dataclass(frozen=True)
class StorageStageArtifact:
    """Stage artifact plus storage destination metadata."""

    artifact: StageArtifact
    destination_key: str

    @property
    def to_payload(self) -> dict[str, Any]:
        """Serialize the full stage artifact payload for storage persistence."""
        return self.artifact.to_dict

    @property
    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
