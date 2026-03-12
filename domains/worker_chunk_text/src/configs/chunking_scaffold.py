"""File-type-aware chunking scaffold and runtime resolver."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, TypeAlias

from langchain_text_splitters import (
    RecursiveCharacterTextSplitter,
    TokenTextSplitter,
)


class ChunkingScaffoldKey(str, Enum):
    TXT = "txt"
    MD = "md"
    HTML = "html"
    PDF = "pdf"
    PY = "py"
    JSON = "json"
    CSV = "csv"
    EML = "eml"


class ChunkingProcessorType(Enum):
    RECURSIVE = RecursiveCharacterTextSplitter
    TOKEN = TokenTextSplitter


@dataclass(slots=True)
class RecursiveParams:
    chunk_size: int = 700
    chunk_overlap: int = 120
    add_start_index: bool = True
    separators: list[str] = field(default_factory=lambda: ["\n\n", "\n", " ", ""])
    is_separator_regex: bool = False


@dataclass(slots=True)
class TokenParams:
    chunk_size: int = 800
    chunk_overlap: int = 100
    encoding_name: str = "cl100k_base"
    model_name: str | None = None

StageParams: TypeAlias = RecursiveParams | TokenParams


@dataclass(slots=True)
class ChunkingStage:
    processor: ChunkingProcessorType
    params: StageParams

    @property
    def dict(self) -> dict[str, Any]:
        processor_value = self.processor.value
        processor_name = getattr(processor_value, "__name__", str(processor_value))
        return {
            "processor": processor_name,
            "params": asdict(self.params),
        }


@dataclass(slots=True)
class ChunkingStages:
    stages: list[ChunkingStage]

    @property
    def dict(self) -> list[dict[str, Any]]:
        return [stage.dict for stage in self.stages]


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

class ChunkingStagesResolver:
    def resolve(self, scaffold_key: str) -> ChunkingStages:
        normalized_scaffold_key = scaffold_key.lower().lstrip(".")
        scaffold_type = ChunkingScaffoldKey(normalized_scaffold_key)
        stages = CHUNKING_SCAFFOLD[scaffold_type]
        return ChunkingStages(stages)
