from __future__ import annotations

from dataclasses import dataclass

from pipeline_common.stages_contracts import ExecutionStatus


@dataclass(slots=True)
class ChunkingExecutionMetadata:
    expected_chunk_count: int
    written_chunk_count: int
    status: ExecutionStatus

    @classmethod
    def from_counts(
        cls,
        expected_chunk_count: int,
        written_chunk_count: int,
    ) -> "ChunkingExecutionMetadata":
        if written_chunk_count == 0:
            status = ExecutionStatus.FAIL
        elif written_chunk_count < expected_chunk_count:
            status = ExecutionStatus.PARTIAL
        else:
            status = ExecutionStatus.SUCCESS
        return cls(
            expected_chunk_count=expected_chunk_count,
            written_chunk_count=written_chunk_count,
            status=status,
        )


@dataclass(slots=True)
class ChunkMetadata:
    source_doc_uri: str
    chunk_id: str
    ordinal: int
    characters: int
    tokens_estimate: int | None = None
