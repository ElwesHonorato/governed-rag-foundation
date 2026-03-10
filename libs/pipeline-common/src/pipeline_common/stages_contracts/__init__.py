"""Numbered stage contracts for cross-worker payloads."""

from pipeline_common.stages_contracts.step_00_common import (
    PROCESSED_DOCUMENT_SCHEMA_VERSION,
    ProcessorMetadata,
    SourceDocumentMetadata,
)
from pipeline_common.stages_contracts.base_processor import BaseProcessor
from pipeline_common.stages_contracts.step_10_artifact_payloads import (
    StageArtifact,
    ParsedTextPayload,
)

__all__ = [
    "PROCESSED_DOCUMENT_SCHEMA_VERSION",
    "SourceDocumentMetadata",
    "ProcessorMetadata",
    "ParsedTextPayload",
    "StageArtifact",
    "BaseProcessor",
]
