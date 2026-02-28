"""Typed startup contracts for worker_metrics."""

from dataclasses import dataclass


@dataclass(frozen=True)
class MetricsStorageConfigContract:
    """Typed contract for metrics storage settings."""

    bucket: str
    processed_prefix: str
    chunks_prefix: str
    embeddings_prefix: str
    indexes_prefix: str


@dataclass(frozen=True)
class MetricsJobConfigContract:
    """Typed contract for metrics runtime fields."""

    poll_interval_seconds: int
    storage: MetricsStorageConfigContract


@dataclass(frozen=True)
class MetricsProcessingConfigContract:
    """Typed processing runtime contract consumed by metrics service."""

    poll_interval_seconds: int
    storage: MetricsStorageConfigContract


@dataclass(frozen=True)
class MetricsWorkerConfigContract:
    """Typed metrics worker startup configuration."""

    poll_interval_seconds: int
    storage: MetricsStorageConfigContract
