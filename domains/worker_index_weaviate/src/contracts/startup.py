"""Startup-specific contracts for worker_index_weaviate."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class IndexWeaviateStorageConfigContract:
    """Typed storage contract for index_weaviate processing runtime."""

    bucket: str
    output_prefix: str

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> IndexWeaviateStorageConfigContract:
        """Build index_weaviate storage config from a dictionary payload."""
        return cls(**payload)


@dataclass(frozen=True)
class RawIndexWeaviateJobConfig:
    """Raw index_weaviate job config parsed directly from job properties."""

    storage: IndexWeaviateStorageConfigContract
    poll_interval_seconds: int

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> RawIndexWeaviateJobConfig:
        """Build raw index_weaviate job config from a dictionary payload."""
        return cls(
            storage=IndexWeaviateStorageConfigContract.from_dict(payload["storage"]),
            poll_interval_seconds=int(payload["poll_interval_seconds"]),
        )


@dataclass(frozen=True)
class RuntimeIndexWeaviateJobConfig:
    """Runtime index_weaviate job config consumed by service wiring."""

    storage: IndexWeaviateStorageConfigContract
    poll_interval_seconds: int
