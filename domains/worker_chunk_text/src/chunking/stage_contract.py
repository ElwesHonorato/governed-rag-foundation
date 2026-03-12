"""Shared stage contracts for worker_chunk_text chunking."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
from typing import Any

from chunking.params import StageParams
from langchain_text_splitters import (
    RecursiveCharacterTextSplitter,
    TokenTextSplitter,
)


class ChunkingProcessorType(Enum):
    RECURSIVE = RecursiveCharacterTextSplitter
    TOKEN = TokenTextSplitter


class ChunkingStrategyKey(str, Enum):
    TXT = "txt"
    MD = "md"
    HTML = "html"
    PDF = "pdf"
    PY = "py"
    JSON = "json"
    CSV = "csv"
    EML = "eml"


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
