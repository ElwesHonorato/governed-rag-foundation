"""Startup-specific contracts for worker_index_weaviate."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class RawIndexWeaviateStorageConfig:
    """Storage config declared in job properties."""

    bucket: str
    output_prefix: str

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> RawIndexWeaviateStorageConfig:
        """Build storage config from a dictionary payload."""
        return cls(**payload)


@dataclass(frozen=True)
class RuntimeIndexWeaviateStorageConfig:
    """Runtime storage config consumed by the index worker."""

    bucket: str
    output_prefix: str

    @classmethod
    def from_raw(cls, raw: RawIndexWeaviateStorageConfig) -> RuntimeIndexWeaviateStorageConfig:
        """Build runtime storage config from raw startup config."""
        return cls(
            bucket=raw.bucket,
            output_prefix=raw.output_prefix,
        )


@dataclass(frozen=True)
class RawIndexWeaviateJobConfig:
    """Raw index_weaviate job config parsed directly from job properties."""

    storage: RawIndexWeaviateStorageConfig
    poll_interval_seconds: int

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> RawIndexWeaviateJobConfig:
        """Build raw index_weaviate job config from a dictionary payload."""
        return cls(
            storage=RawIndexWeaviateStorageConfig.from_dict(payload["storage"]),
            poll_interval_seconds=int(payload["poll_interval_seconds"]),
        )


@dataclass(frozen=True)
class RuntimeIndexWeaviateJobConfig:
    """Runtime index_weaviate job config consumed by service wiring."""

    storage: RuntimeIndexWeaviateStorageConfig
    poll_interval_seconds: int
    weaviate_url: str

