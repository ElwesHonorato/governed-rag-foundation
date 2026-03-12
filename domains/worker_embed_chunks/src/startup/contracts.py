"""Startup-specific contracts for worker_embed_chunks."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class RawEmbedChunksStorageConfig:
    """Storage config declared in job properties."""

    bucket: str
    output_prefix: str

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> RawEmbedChunksStorageConfig:
        """Build storage config from a dictionary payload."""
        return cls(**payload)


@dataclass(frozen=True)
class RuntimeEmbedChunksStorageConfig:
    """Runtime storage config consumed by the embed worker."""

    bucket: str
    output_prefix: str

    @classmethod
    def from_raw(
        cls,
        raw: RawEmbedChunksStorageConfig,
        *,
        env: str | None,
    ) -> RuntimeEmbedChunksStorageConfig:
        """Build runtime storage config from raw startup config."""
        return cls(
            bucket=raw.bucket,
            output_prefix=f"{env}/{raw.output_prefix}",
        )


@dataclass(frozen=True)
class RawEmbedChunksJobConfig:
    """Raw embed_chunks job config parsed directly from job properties."""

    storage: RawEmbedChunksStorageConfig
    poll_interval_seconds: int
    dimension: int

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> RawEmbedChunksJobConfig:
        """Build raw embed_chunks job config from a dictionary payload."""
        return cls(
            storage=RawEmbedChunksStorageConfig.from_dict(payload["storage"]),
            poll_interval_seconds=int(payload["poll_interval_seconds"]),
            dimension=int(payload["dimension"]),
        )


@dataclass(frozen=True)
class RuntimeEmbedChunksJobConfig:
    """Runtime embed_chunks job config consumed by service wiring."""

    storage: RuntimeEmbedChunksStorageConfig
    poll_interval_seconds: int
    dimension: int
