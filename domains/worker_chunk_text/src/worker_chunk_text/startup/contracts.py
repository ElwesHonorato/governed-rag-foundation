"""Startup-specific contracts for worker_chunk_text."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


DEFAULT_MANIFEST_PREFIX = "07_metadata/manifest/"


@dataclass(frozen=True)
class RawChunkStorageConfig:
    """Storage paths declared in job properties before environment scoping.

    Attributes:
        bucket: Bucket name used for both chunk and manifest writes.
        output_prefix: Base prefix where chunk artifacts should be written.
        manifest_prefix: Base prefix where manifests should be written.
    """

    bucket: str
    output_prefix: str
    manifest_prefix: str

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> RawChunkStorageConfig:
        """Build raw storage paths from a dictionary payload."""
        return cls(
            bucket=str(payload["bucket"]),
            output_prefix=str(payload["output_prefix"]),
            manifest_prefix=str(payload.get("manifest_prefix", DEFAULT_MANIFEST_PREFIX)),
        )


@dataclass(frozen=True)
class RuntimeChunkStorageConfig:
    """Environment-scoped storage locations used by the running worker.

    Attributes:
        bucket: Bucket name used for output writes.
        output_prefix: Environment-scoped chunk artifact prefix.
        manifest_prefix: Environment-scoped manifest prefix.
    """

    bucket: str
    output_prefix: str
    manifest_prefix: str

    @classmethod
    def from_raw(
        cls,
        raw: RawChunkStorageConfig,
        *,
        env: str | None,
    ) -> RuntimeChunkStorageConfig:
        """Build runtime storage paths by prefixing raw paths with the active environment.

        Args:
            raw: Unscoped storage paths from job properties.
            env: Environment name inserted ahead of the configured prefixes.

        Returns:
            Environment-scoped storage paths for runtime writes.
        """
        return cls(
            bucket=raw.bucket,
            output_prefix=f"{env}/{raw.output_prefix}",
            manifest_prefix=f"{env}/{raw.manifest_prefix}",
        )


@dataclass(frozen=True)
class RawChunkJobConfig:
    """Chunk worker configuration parsed directly from job properties.

    Attributes:
        storage: Raw storage path configuration before environment scoping.
        poll_interval_seconds: Queue poll timeout used by the worker loop.
    """

    storage: RawChunkStorageConfig
    poll_interval_seconds: int
    elasticsearch_index_queue_name: str

    @classmethod
    def from_dict(cls, payload: dict[str, object]) -> RawChunkJobConfig:
        """Build raw chunk job config from a dictionary payload."""
        queue_payload = payload["queue"]
        return cls(
            storage=RawChunkStorageConfig.from_dict(payload["storage"]),
            poll_interval_seconds=int(payload["poll_interval_seconds"]),
            elasticsearch_index_queue_name=str(queue_payload["elasticsearch_produce"]),
        )


@dataclass(frozen=True)
class RuntimeChunkJobConfig:
    """Resolved startup configuration for the chunk-text worker.

    Attributes:
        poll_interval_seconds: Queue poll timeout used by the worker service.
        storage: Environment-scoped storage locations for chunk and manifest output.
    """

    poll_interval_seconds: int
    storage: RuntimeChunkStorageConfig
    elasticsearch_index_queue_name: str
