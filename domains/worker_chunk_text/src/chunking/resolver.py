"""Chunking stage resolver for worker_chunk_text."""

from chunking.stages import ChunkingStages
from configs.chunking_strategies import CHUNKING_STRATEGIES, ChunkingStrategyKey


class ChunkingStagesResolver:
    def resolve(self, scaffold_key: str) -> ChunkingStages:
        normalized_scaffold_key = scaffold_key.lower().lstrip(".")
        scaffold_type = ChunkingStrategyKey(normalized_scaffold_key)
        stages = CHUNKING_STRATEGIES[scaffold_type]
        return ChunkingStages(stages)
