"""Deterministic provenance identity builders."""

from __future__ import annotations

import hashlib
import json
from typing import Any


def canonical_json(value: Any) -> str:
    """Return stable JSON encoding for hashing."""
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def sha256_hex(payload: bytes | str) -> str:
    """Return SHA-256 hex digest for bytes or UTF-8 text payloads."""
    if isinstance(payload, str):
        payload = payload.encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def source_content_hash(source_bytes: bytes) -> str:
    """Hash source bytes for deterministic source version identity."""
    return sha256_hex(source_bytes)


def chunk_params_hash(chunker_params: dict[str, Any]) -> str:
    """Hash canonical chunker params."""
    return sha256_hex(canonical_json(chunker_params))


def embedding_params_hash(embedder_params: dict[str, Any]) -> str:
    """Hash canonical embedder params."""
    return sha256_hex(canonical_json(embedder_params))


def build_chunk_id(
    *,
    source_dataset_urn: str,
    source_content_hash_value: str,
    chunker_version: str,
    chunk_params_hash_value: str,
    offsets_start: int,
    offsets_end: int,
) -> str:
    """Build deterministic chunk identifier."""
    payload = "|".join(
        [
            source_dataset_urn,
            source_content_hash_value,
            chunker_version,
            chunk_params_hash_value,
            str(offsets_start),
            str(offsets_end),
        ]
    )
    return sha256_hex(payload)


def build_embedding_id(
    *,
    chunk_id: str,
    embedder_name: str,
    embedder_version: str,
    embedding_params_hash_value: str,
    index_target: str,
) -> str:
    """Build deterministic embedding identifier."""
    payload = "|".join(
        [
            chunk_id,
            embedder_name,
            embedder_version,
            embedding_params_hash_value,
            index_target,
        ]
    )
    return sha256_hex(payload)
