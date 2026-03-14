from __future__ import annotations

from dataclasses import asdict, dataclass

from pipeline_common.stages_contracts import ExecutionStatus


@dataclass(slots=True)
class ChunkingExecutionMetadata:
    """Summary of chunk write results for one processor run.

    Attributes:
        chunk_count_expected: Number of chunk artifacts the processor attempted to emit.
        chunk_count_written: Number of chunk artifacts successfully written.
        chunk_entries: Destination keys written for the emitted chunk artifacts.
    """

    chunk_count_expected: int
    chunk_count_written: int
    chunk_entries: list[str]

    @property
    def status(self) -> ExecutionStatus:
        """Derive aggregate execution status from expected versus written chunk counts."""
        if self.chunk_count_written == 0:
            return ExecutionStatus.FAIL
        if self.chunk_count_written < self.chunk_count_expected:
            return ExecutionStatus.PARTIAL
        return ExecutionStatus.SUCCESS

    @property
    def to_dict(self) -> dict[str, object]:
        """Serialize chunk execution metadata for process results."""
        payload = asdict(self)
        payload["status"] = self.status.value
        return payload


@dataclass(slots=True)
class ChunkMetadata:
    """Metadata attached to a single emitted chunk artifact.

    Attributes:
        index: Zero-based chunk order within the processed document.
        chunk_id: Stable provenance-derived identifier for the chunk.
        offsets_start: Inclusive start offset in the source text.
        offsets_end: Exclusive end offset in the source text.
        chunk_text_hash: Deterministic hash of the chunk text payload.
    """

    index: int
    chunk_id: str
    offsets_start: int
    offsets_end: int
    chunk_text_hash: str

    @property
    def to_dict(self) -> dict[str, object]:
        """Serialize chunk content metadata for artifact persistence."""
        return asdict(self)
