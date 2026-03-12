"""Unified worker_chunk_text contracts, ordered high-level to low-level."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from pipeline_common.stages_contracts import ExecutionStatus


@dataclass(frozen=True)
class ChunkTextQueueConfigContract:
    stage: str
    queue_pop_timeout_seconds: int
    pop_timeout_seconds: int
    consume: str
    produce: str
    dlq: str

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> ChunkTextQueueConfigContract:
        normalized_payload = dict(payload)
        normalized_payload["queue_pop_timeout_seconds"] = int(normalized_payload["queue_pop_timeout_seconds"])
        normalized_payload["pop_timeout_seconds"] = int(normalized_payload["pop_timeout_seconds"])
        return cls(**normalized_payload)

@dataclass(frozen=True)
class ChunkingExecutionResult:
    chunk_count_expected: int
    chunk_count_written: int
    chunk_entries: list[str]
    status: ExecutionStatus = field(init=False)

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "status",
            self.resolve_status(
                chunk_count_expected=self.chunk_count_expected,
                chunk_count_written=self.chunk_count_written,
            ),
        )

    @classmethod
    def resolve_status(cls, *, chunk_count_expected: int, chunk_count_written: int) -> ExecutionStatus:
        if chunk_count_written == chunk_count_expected:
            return ExecutionStatus.SUCCESS
        if chunk_count_written > 0:
            return ExecutionStatus.PARTIAL
        return ExecutionStatus.FAIL


@dataclass(frozen=True)
class ChunkMetadata:
    index: int
    chunk_id: str
    offsets_start: int
    offsets_end: int
    chunk_text_hash: str

    @property
    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

