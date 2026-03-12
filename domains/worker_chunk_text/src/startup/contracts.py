"""Startup-specific contracts for worker_chunk_text."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

@dataclass(frozen=True)
class RawStoragePathsContract:
    """Raw storage paths declared in job properties before environment scoping."""

    bucket: str
    output_prefix: str
    manifest_prefix: str

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> RawStoragePathsContract:
        """Build raw storage paths from a dictionary payload."""
        return cls(**payload)


@dataclass(frozen=True)
class RuntimeStoragePathsContract:
    """Environment-dependent runtime storage paths for chunk and manifest output."""

    bucket: str
    output_prefix: str
    manifest_prefix: str

    @classmethod
    def from_raw(
        cls,
        raw: RawStoragePathsContract,
        *,
        env: str | None,
    ) -> RuntimeStoragePathsContract:
        """Build environment-dependent runtime storage paths from raw storage paths."""
        return cls(
            bucket=raw.bucket,
            output_prefix=f"{env}/{raw.output_prefix}",
            manifest_prefix=f"{env}/{raw.manifest_prefix}",
        )


@dataclass(frozen=True)
class RawChunkJobConfig:
    """Raw chunk job config parsed directly from job properties."""

    storage: RawStoragePathsContract
    poll_interval_seconds: int

    @classmethod
    def from_dict(cls, payload: dict[str, object]) -> RawChunkJobConfig:
        """Build raw chunk job config from a dictionary payload."""
        return cls(
            storage=RawStoragePathsContract.from_dict(payload["storage"]),
            poll_interval_seconds=int(payload["poll_interval_seconds"]),
        )


@dataclass(frozen=True)
class RuntimeChunkJobConfig:
    """Runtime chunk job config after startup-time transformations."""

    poll_interval_seconds: int
    storage: RuntimeStoragePathsContract
