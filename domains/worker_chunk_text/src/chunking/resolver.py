"""Chunking stage resolver for worker_chunk_text."""

from chunking.stage_contract import ChunkingStages, ChunkingStrategyKey
from chunking.strategies import CHUNKING_STRATEGIES


class ChunkingStagesResolver:
    """Resolve stage sequences for source types handled by this worker."""

    def resolve(self, scaffold_key: str) -> ChunkingStages:
        """Normalize a source-type key and return the configured stages.

        Args:
            scaffold_key: Source-type identifier such as ``pdf`` or ``.md``.

        Returns:
            The ordered chunking stages for the normalized source type.

        Raises:
            ValueError: If the normalized source type is not supported.
        """
        normalized_scaffold_key = scaffold_key.lower().lstrip(".")
        scaffold_type = ChunkingStrategyKey(normalized_scaffold_key)
        stages = CHUNKING_STRATEGIES[scaffold_type]
        return ChunkingStages(stages)
