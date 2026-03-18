"""Shared stage contracts for worker_chunk_text chunking."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
from typing import Any

from worker_chunk_text.chunking.params import StageParams
from langchain_text_splitters import (
    RecursiveCharacterTextSplitter,
    TokenTextSplitter,
)


class ChunkingProcessorType(Enum):
    """Supported splitter implementations used by chunking stages."""

    RECURSIVE = RecursiveCharacterTextSplitter
    TOKEN = TokenTextSplitter


class ChunkingStrategyKey(str, Enum):
    """Source-type keys mapped to worker chunking strategies."""

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
    """One configured splitter stage in the chunking pipeline.

    Attributes:
        processor: Splitter implementation to instantiate for this stage.
        params: Typed constructor parameters passed to the splitter.
    """

    processor: ChunkingProcessorType
    params: StageParams

    @property
    def dict(self) -> dict[str, Any]:
        """Return a JSON-serializable representation of the stage configuration."""
        processor_value = self.processor.value
        processor_name = getattr(processor_value, "__name__", str(processor_value))
        return {
            "processor": processor_name,
            "params": asdict(self.params),
        }


@dataclass(slots=True)
class ChunkingStages:
    """Ordered stage sequence applied to a single source artifact.

    Attributes:
        stages: Sequential splitter stages run by the processor.
    """

    stages: list[ChunkingStage]

    @property
    def dict(self) -> list[dict[str, Any]]:
        """Return each configured stage as a serialized dictionary."""
        return [stage.dict for stage in self.stages]
