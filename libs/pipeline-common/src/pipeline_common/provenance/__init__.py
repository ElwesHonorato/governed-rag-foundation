"""Chunk and embedding provenance registry primitives."""

from pipeline_common.provenance.contracts import (
    ChunkRegistryRow,
    ChunkRegistryStatus,
    EmbeddingRegistryRow,
    EmbeddingRegistryStatus,
)
from pipeline_common.provenance.envelope import build_chunk_envelope, build_embedding_envelope
from pipeline_common.provenance.identifiers import (
    build_chunk_id,
    build_embedding_id,
    canonical_json,
    chunk_params_hash,
    embedding_params_hash,
    sha256_hex,
    source_content_hash,
)
from pipeline_common.provenance.registry import ProvenanceRegistryGateway

__all__ = [
    "ChunkRegistryRow",
    "ChunkRegistryStatus",
    "EmbeddingRegistryRow",
    "EmbeddingRegistryStatus",
    "ProvenanceRegistryGateway",
    "build_chunk_envelope",
    "build_embedding_envelope",
    "build_chunk_id",
    "build_embedding_id",
    "canonical_json",
    "chunk_params_hash",
    "embedding_params_hash",
    "sha256_hex",
    "source_content_hash",
]
