"""Numbered stage contracts for cross-worker payloads."""

from pipeline_common.stages_contracts.step_00_common import (
    PROCESSED_DOCUMENT_SCHEMA_VERSION,
    ProcessorMetadata,
    SourceDocumentMetadata,
    RegistryRowContract,
)
from pipeline_common.stages_contracts.base_processor import BaseProcessor
from pipeline_common.stages_contracts.step_10_artifact_payloads import ArtifactPayload, ParsedTextPayload
from pipeline_common.stages_contracts.step_20_chunk import (
    ChunkRegistryStatus,
)
from pipeline_common.stages_contracts.step_30_embed import (
    EmbeddingProvenanceEnvelope,
    EmbeddingRegistryRow,
    EmbeddingRegistryStatus,
)

__all__ = [
    "PROCESSED_DOCUMENT_SCHEMA_VERSION",
    "SourceDocumentMetadata",
    "ProcessorMetadata",
    "ParsedTextPayload",
    "ArtifactPayload",
    "RegistryRowContract",
    "BaseProcessor",
    "ChunkRegistryStatus",
    "EmbeddingRegistryRow",
    "EmbeddingRegistryStatus",
    "EmbeddingProvenanceEnvelope",
]
