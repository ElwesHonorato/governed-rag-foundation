"""Canonical chunk and embedding provenance envelope builders."""

from __future__ import annotations

from typing import Any

from pipeline_common.provenance.identifiers import (
    build_chunk_id,
    build_embedding_id,
    chunk_params_hash,
    embedding_params_hash,
    sha256_hex,
)


def build_chunk_envelope(
    *,
    source_dataset_urn: str,
    source_s3_uri: str,
    source_content_hash: str,
    chunk_s3_uri: str,
    chunk_text: str,
    offsets_start: int,
    offsets_end: int,
    chunker_name: str,
    chunker_version: str,
    chunker_params: dict[str, Any],
    chunking_run_id: str,
    breadcrumb: str | None = None,
) -> dict[str, Any]:
    """Build canonical chunk provenance envelope."""
    chunk_params_hash_value = chunk_params_hash(chunker_params)
    chunk_id = build_chunk_id(
        source_dataset_urn=source_dataset_urn,
        source_content_hash_value=source_content_hash,
        chunker_name=chunker_name,
        chunker_version=chunker_version,
        chunk_params_hash_value=chunk_params_hash_value,
        offsets_start=offsets_start,
        offsets_end=offsets_end,
    )
    return {
        "chunk_id": chunk_id,
        "source_dataset_urn": source_dataset_urn,
        "source_s3_uri": source_s3_uri,
        "source_content_hash": source_content_hash,
        "chunk_s3_uri": chunk_s3_uri,
        "offsets_start": int(offsets_start),
        "offsets_end": int(offsets_end),
        "breadcrumb": breadcrumb,
        "chunk_text_hash": sha256_hex(chunk_text),
        "chunker_name": chunker_name,
        "chunker_version": chunker_version,
        "chunk_params_hash": chunk_params_hash_value,
        "chunking_run_id": chunking_run_id,
    }


def build_embedding_envelope(
    *,
    chunk_id: str,
    index_target: str,
    embedder_name: str,
    embedder_version: str,
    embedder_params: dict[str, Any],
    embedding_params_hash_value: str | None = None,
    embedding_dim: int,
    embedding_run_id: str,
    chunking_run_id: str,
    vector: list[float] | None,
    vector_record_id: str | None,
) -> dict[str, Any]:
    """Build canonical embedding provenance envelope."""
    resolved_embedding_params_hash = embedding_params_hash_value or embedding_params_hash(embedder_params)
    embedding_id = build_embedding_id(
        chunk_id=chunk_id,
        embedder_name=embedder_name,
        embedder_version=embedder_version,
        embedding_params_hash_value=resolved_embedding_params_hash,
        index_target=index_target,
    )
    vector_hash = sha256_hex(str(vector)) if vector is not None else None
    return {
        "embedding_id": embedding_id,
        "chunk_id": chunk_id,
        "index_target": index_target,
        "embedder_name": embedder_name,
        "embedder_version": embedder_version,
        "embedding_params_hash": resolved_embedding_params_hash,
        "embedding_dim": int(embedding_dim),
        "embedding_vector_hash": vector_hash,
        "embedding_run_id": embedding_run_id,
        "chunking_run_id": chunking_run_id,
        "vector_record_id": vector_record_id,
    }
