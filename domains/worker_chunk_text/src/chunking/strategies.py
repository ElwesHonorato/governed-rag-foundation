"""File-type-aware chunking scaffold and runtime resolver."""

from __future__ import annotations

from chunking.params import RecursiveParams, TokenParams
from chunking.stage_contract import ChunkingProcessorType, ChunkingStage, ChunkingStrategyKey


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
