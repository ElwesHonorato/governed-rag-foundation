from __future__ import annotations

from dataclasses import dataclass, field
from typing import TypeAlias


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
