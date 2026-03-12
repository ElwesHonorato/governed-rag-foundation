"""File-type-aware chunking scaffold and runtime resolver."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from chunking.stages import ChunkingProcessorType, ChunkingStage
from chunking.params_contract import RecursiveParams, StageParams, TokenParams


class ChunkingScaffoldKey(str, Enum):
    TXT = "txt"
    MD = "md"
    HTML = "html"
    PDF = "pdf"
    PY = "py"
    JSON = "json"
    CSV = "csv"
    EML = "eml"

CHUNKING_SCAFFOLD: dict[ChunkingScaffoldKey, list[ChunkingStage]] = {
    ChunkingScaffoldKey.TXT: [
        ChunkingStage(
            processor=ChunkingProcessorType.RECURSIVE,
            params=RecursiveParams(),
        )
    ],
    ChunkingScaffoldKey.MD: [
        ChunkingStage(
            processor=ChunkingProcessorType.RECURSIVE,
            params=RecursiveParams(),
        )
    ],
    ChunkingScaffoldKey.HTML: [
        ChunkingStage(
            processor=ChunkingProcessorType.RECURSIVE,
            params=RecursiveParams(),
        )
    ],
    ChunkingScaffoldKey.PDF: [
        ChunkingStage(
            processor=ChunkingProcessorType.RECURSIVE,
            params=RecursiveParams(),
        ),
    ],
    ChunkingScaffoldKey.PY: [
        ChunkingStage(
            processor=ChunkingProcessorType.TOKEN,
            params=TokenParams(),
        ),
    ],
    ChunkingScaffoldKey.JSON: [
        ChunkingStage(
            processor=ChunkingProcessorType.RECURSIVE,
            params=RecursiveParams(chunk_overlap=100),
        ),
    ],
    ChunkingScaffoldKey.CSV: [
        ChunkingStage(
            processor=ChunkingProcessorType.RECURSIVE,
            params=RecursiveParams(),
        ),
    ],
    ChunkingScaffoldKey.EML: [
        ChunkingStage(
            processor=ChunkingProcessorType.RECURSIVE,
            params=RecursiveParams(chunk_overlap=100),
        ),
    ],
}
