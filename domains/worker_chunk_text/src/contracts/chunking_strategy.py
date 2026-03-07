"""Chunking strategy enum values for worker_chunk_text."""

from enum import StrEnum


class ChunkingStrategy(StrEnum):
    """Supported chunking strategies."""

    RECURSIVE_CHARACTER = "recursive_character"
