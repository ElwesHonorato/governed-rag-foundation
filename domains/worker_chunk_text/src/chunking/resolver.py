"""Chunking stage resolver for worker_chunk_text."""

from chunking.stages import ChunkingStages
from configs.chunking_scaffold import CHUNKING_SCAFFOLD, ChunkingScaffoldKey


class ChunkingStagesResolver:
    def resolve(self, scaffold_key: str) -> ChunkingStages:
        normalized_scaffold_key = scaffold_key.lower().lstrip(".")
        scaffold_type = ChunkingScaffoldKey(normalized_scaffold_key)
        stages = CHUNKING_SCAFFOLD[scaffold_type]
        return ChunkingStages(stages)
