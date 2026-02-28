"""Typed startup contracts for worker_chunk_text."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ChunkTextQueueConfigContract:
    """Typed contract for chunk_text queue runtime settings."""

    stage: str
    queue_pop_timeout_seconds: int
    pop_timeout_seconds: int
    consume: str
    produce: str
    dlq: str


@dataclass(frozen=True)
class ChunkTextJobConfigContract:
    """Typed contract for chunk_text storage/runtime fields."""

    bucket: str
    input_prefix: str
    output_prefix: str
    poll_interval_seconds: int


@dataclass(frozen=True)
class ChunkTextStorageConfigContract:
    """Typed storage contract for chunk_text processing runtime."""

    bucket: str
    input_prefix: str
    output_prefix: str


@dataclass(frozen=True)
class ChunkTextProcessingConfigContract:
    """Typed processing runtime contract consumed by chunk_text service."""

    poll_interval_seconds: int
    queue: ChunkTextQueueConfigContract
    storage: ChunkTextStorageConfigContract


@dataclass(frozen=True)
class ChunkTextWorkerConfigContract:
    """Typed chunk_text worker startup configuration."""

    storage: ChunkTextStorageConfigContract
    poll_interval_seconds: int
    queue_config: ChunkTextQueueConfigContract
