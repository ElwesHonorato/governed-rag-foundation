"""Startup-specific contracts for worker_embed_chunks."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class EmbedChunksStorageConfigContract:
    """Typed storage contract for embed_chunks processing runtime."""

    bucket: str
    output_prefix: str

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> EmbedChunksStorageConfigContract:
        """Build embed_chunks storage config from a dictionary payload."""
        return cls(**payload)


@dataclass(frozen=True)
class RawEmbedChunksJobConfig:
    """Raw embed_chunks job config parsed directly from job properties."""

    storage: EmbedChunksStorageConfigContract
    poll_interval_seconds: int
    dimension: int

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> RawEmbedChunksJobConfig:
        """Build raw embed_chunks job config from a dictionary payload."""
        return cls(
            storage=EmbedChunksStorageConfigContract.from_dict(payload["storage"]),
            poll_interval_seconds=int(payload["poll_interval_seconds"]),
            dimension=int(payload["dimension"]),
        )


@dataclass(frozen=True)
class RuntimeEmbedChunksJobConfig:
    """Runtime embed_chunks job config consumed by service wiring."""

    storage: EmbedChunksStorageConfigContract
    poll_interval_seconds: int
    dimension: int
