from __future__ import annotations

from dataclasses import dataclass

from pipeline_common.stages_contracts import ExecutionStatus


@dataclass(slots=True)
class ChunkingExecutionMetadata:
    """Summary of chunk write results for one processor run.

    Attributes:
        expected_chunk_count: Number of chunk artifacts the processor attempted to emit.
        written_chunk_count: Number of chunk artifacts successfully written.
        status: Aggregate execution status derived from the write counts.
    """

    expected_chunk_count: int
    written_chunk_count: int
    status: ExecutionStatus

    @classmethod
    def from_counts(
        cls,
        expected_chunk_count: int,
        written_chunk_count: int,
    ) -> "ChunkingExecutionMetadata":
        """Build execution metadata and derive status from expected versus written counts."""
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
    """Metadata attached to a single emitted chunk artifact.

    Attributes:
        source_doc_uri: URI of the upstream document that produced the chunk.
        chunk_id: Stable provenance-derived identifier for the chunk.
        ordinal: Zero-based chunk order within the processed document.
        characters: Character count of the chunk payload.
        tokens_estimate: Optional approximate token count for the chunk content.
    """

    source_doc_uri: str
    chunk_id: str
    ordinal: int
    characters: int
    tokens_estimate: int | None = None
