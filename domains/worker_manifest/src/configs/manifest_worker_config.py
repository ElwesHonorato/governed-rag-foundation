"""Typed startup contracts for worker_manifest."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ManifestStorageConfigContract:
    """Typed contract for manifest storage settings."""

    bucket: str
    processed_prefix: str
    chunks_prefix: str
    embeddings_prefix: str
    indexes_prefix: str
    manifest_prefix: str


@dataclass(frozen=True)
class ManifestJobConfigContract:
    """Typed contract for manifest runtime fields."""

    poll_interval_seconds: int
    storage: ManifestStorageConfigContract


@dataclass(frozen=True)
class ManifestProcessingConfigContract:
    """Typed processing runtime contract consumed by manifest service."""

    poll_interval_seconds: int
    storage: ManifestStorageConfigContract


@dataclass(frozen=True)
class ManifestWorkerConfig:
    """Typed manifest worker startup configuration."""

    poll_interval_seconds: int
    storage: ManifestStorageConfigContract
