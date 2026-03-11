"""Typed startup contracts for worker_embed_chunks."""

from dataclasses import dataclass


@dataclass(frozen=True)
class EmbedChunksQueueConfigContract:
    """Typed contract for embed_chunks queue runtime settings."""

    stage: str
    queue_pop_timeout_seconds: int
    pop_timeout_seconds: int
    consume: str
    produce: str
    dlq: str


@dataclass(frozen=True)
class EmbedChunksJobConfigContract:
    """Typed contract for embed_chunks storage/runtime fields."""

    bucket: str
    output_prefix: str
    poll_interval_seconds: int
    dimension: int


@dataclass(frozen=True)
class EmbedChunksStorageConfigContract:
    """Typed storage contract for embed_chunks processing runtime."""

    bucket: str
    output_prefix: str


@dataclass(frozen=True)
class EmbedChunksProcessingConfigContract:
    """Typed processing runtime contract consumed by embed_chunks service."""

    poll_interval_seconds: int
    queue: EmbedChunksQueueConfigContract
    storage: EmbedChunksStorageConfigContract


@dataclass(frozen=True)
class EmbedChunksWorkerConfigContract:
    """Typed embed_chunks worker startup configuration."""

    storage: EmbedChunksStorageConfigContract
    poll_interval_seconds: int
    dimension: int
    queue_config: EmbedChunksQueueConfigContract
