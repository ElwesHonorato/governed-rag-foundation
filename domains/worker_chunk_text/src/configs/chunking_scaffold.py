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
    DOCX = "docx"
    PY = "py"
    JS = "js"
    JAVA = "java"
    JSON = "json"
    CSV = "csv"
    EML = "eml"


class ChunkingProcessorType(Enum):
    RECURSIVE = RecursiveCharacterTextSplitter
    TOKEN = TokenTextSplitter


class CustomChunkingProcessorType(str, Enum):
    PAGE = "page"
    CODE = "code"
    JSON_OBJECTS = "json_objects"
    ROW_GROUPS = "row_groups"
    EMAIL_PARTS = "email_parts"


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


@dataclass(slots=True)
class CodeParams:
    language: str
    chunk_size: int = 1200
    chunk_overlap: int = 100


@dataclass(slots=True)
class PageSplitParams:
    keep_page_metadata: bool = True


@dataclass(slots=True)
class JsonObjectParams:
    split_level: str = "top_level"
    keep_path_metadata: bool = True
    max_field_length: int = 2000


@dataclass(slots=True)
class RowGroupParams:
    rows_per_chunk: int = 20
    repeat_header: bool = True
    include_column_metadata: bool = True


@dataclass(slots=True)
class EmailPartsParams:
    split_headers: bool = True
    split_body: bool = True
    clean_quoted_text: bool = True


StageParams: TypeAlias = (
    RecursiveParams
    | TokenParams
    | CodeParams
    | PageSplitParams
    | JsonObjectParams
    | RowGroupParams
    | EmailPartsParams
)


@dataclass(slots=True)
class ChunkingStage:
    processor: ChunkingProcessorType | CustomChunkingProcessorType
    params: StageParams

    def to_serializable_dict(self) -> dict[str, Any]:
        processor_value = self.processor.value
        processor_name = getattr(processor_value, "__name__", str(processor_value))
        return {
            "processor": processor_name,
            "params": asdict(self.params),
        }


@dataclass(slots=True)
class ChunkingStages:
    stages: list[ChunkingStage]

    def to_serializable_dict(self) -> dict[str, Any]:
        return {"stages": [stage.to_serializable_dict() for stage in self.stages]}


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
            processor=CustomChunkingProcessorType.PAGE,
            params=PageSplitParams(),
        ),
        ChunkingStage(
            processor=ChunkingProcessorType.RECURSIVE,
            params=RecursiveParams(),
        ),
    ],
    ChunkingScaffoldKey.PY: [
        ChunkingStage(
            processor=CustomChunkingProcessorType.CODE,
            params=CodeParams(language="python"),
        ),
        ChunkingStage(
            processor=ChunkingProcessorType.TOKEN,
            params=TokenParams(),
        ),
    ],
    ChunkingScaffoldKey.JSON: [
        ChunkingStage(
            processor=CustomChunkingProcessorType.JSON_OBJECTS,
            params=JsonObjectParams(),
        ),
        ChunkingStage(
            processor=ChunkingProcessorType.RECURSIVE,
            params=RecursiveParams(chunk_overlap=100),
        ),
    ],
    ChunkingScaffoldKey.CSV: [
        ChunkingStage(
            processor=CustomChunkingProcessorType.ROW_GROUPS,
            params=RowGroupParams(),
        ),
    ],
    ChunkingScaffoldKey.EML: [
        ChunkingStage(
            processor=CustomChunkingProcessorType.EMAIL_PARTS,
            params=EmailPartsParams(),
        ),
        ChunkingStage(
            processor=ChunkingProcessorType.RECURSIVE,
            params=RecursiveParams(chunk_overlap=100),
        ),
    ],
}

class ChunkingScaffoldResolver:
    scaffold_key: str | None = None

    def resolve(self, scaffold_key: str) -> ChunkingStages:
        normalized_scaffold_key = scaffold_key.lower().lstrip(".")
        scaffold_type = ChunkingScaffoldKey(normalized_scaffold_key)
        ChunkingScaffoldResolver.scaffold_key = normalized_scaffold_key
        stages = CHUNKING_SCAFFOLD[scaffold_type]
        return ChunkingStages(
            [stage for stage in stages if isinstance(stage.processor, ChunkingProcessorType)]
        )
