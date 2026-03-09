"""Numbered stage contracts for cross-worker payloads."""

from pipeline_common.stages_contracts.base import (
    PROCESSED_DOCUMENT_SCHEMA_VERSION,
    ProcessorMetadata,
    SourceDocumentMetadata,
    RegistryRowContract,
)
from pipeline_common.stages_contracts.base_processor import BaseProcessor
from pipeline_common.stages_contracts.stage_20_parser import ProcessedDocumentPayload
from pipeline_common.stages_contracts.stage_20_parser import ParsedTextPayload
from pipeline_common.stages_contracts.stage_30_chunking import (
    ChunkArtifactPayload,
    ChunkRegistryRow,
    ChunkRegistryStatus,
    ChunkProvenanceEnvelope,
)
from pipeline_common.stages_contracts.stage_40_embedding import (
    EmbeddingProvenanceEnvelope,
    EmbeddingRegistryRow,
    EmbeddingRegistryStatus,
)

__all__ = [
    "PROCESSED_DOCUMENT_SCHEMA_VERSION",
    "SourceDocumentMetadata",
    "ProcessorMetadata",
    "ParsedTextPayload",
    "ProcessedDocumentPayload",
    "RegistryRowContract",
    "BaseProcessor",
    "ChunkArtifactPayload",
    "ChunkRegistryRow",
    "ChunkRegistryStatus",
    "ChunkProvenanceEnvelope",
    "EmbeddingRegistryRow",
    "EmbeddingRegistryStatus",
    "EmbeddingProvenanceEnvelope",
]
