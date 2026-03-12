"""File-type-aware chunking scaffold and runtime resolver."""

from __future__ import annotations

from enum import Enum

from chunking.params_contract import RecursiveParams, TokenParams
from chunking.stages import ChunkingProcessorType, ChunkingStage


class ChunkingStrategyKey(str, Enum):
    TXT = "txt"
    MD = "md"
    HTML = "html"
    PDF = "pdf"
    PY = "py"
    JSON = "json"
    CSV = "csv"
    EML = "eml"


CHUNKING_STRATEGIES: dict[ChunkingStrategyKey, list[ChunkingStage]] = {
    ChunkingStrategyKey.TXT: [
        ChunkingStage(
            processor=ChunkingProcessorType.RECURSIVE,
            params=RecursiveParams(),
        )
    ],
    ChunkingStrategyKey.MD: [
        ChunkingStage(
            processor=ChunkingProcessorType.RECURSIVE,
            params=RecursiveParams(),
        )
    ],
    ChunkingStrategyKey.HTML: [
        ChunkingStage(
            processor=ChunkingProcessorType.RECURSIVE,
            params=RecursiveParams(),
        )
    ],
    ChunkingStrategyKey.PDF: [
        ChunkingStage(
            processor=ChunkingProcessorType.RECURSIVE,
            params=RecursiveParams(),
        ),
    ],
    ChunkingStrategyKey.PY: [
        ChunkingStage(
            processor=ChunkingProcessorType.TOKEN,
            params=TokenParams(),
        ),
    ],
    ChunkingStrategyKey.JSON: [
        ChunkingStage(
            processor=ChunkingProcessorType.RECURSIVE,
            params=RecursiveParams(chunk_overlap=100),
        ),
    ],
    ChunkingStrategyKey.CSV: [
        ChunkingStage(
            processor=ChunkingProcessorType.RECURSIVE,
            params=RecursiveParams(),
        ),
    ],
    ChunkingStrategyKey.EML: [
        ChunkingStage(
            processor=ChunkingProcessorType.RECURSIVE,
            params=RecursiveParams(chunk_overlap=100),
        ),
    ],
}
