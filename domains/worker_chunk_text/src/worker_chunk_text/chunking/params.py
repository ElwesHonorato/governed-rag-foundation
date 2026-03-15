from __future__ import annotations

from dataclasses import dataclass, field
from typing import TypeAlias


@dataclass(slots=True)
class RecursiveParams:
    """Configuration for recursive character-based chunk splitting.

    Attributes:
        chunk_size: Maximum character count allowed in each emitted chunk.
        chunk_overlap: Number of trailing characters repeated into the next chunk.
        add_start_index: Whether split documents should include ``start_index`` metadata.
        separators: Ordered separators used by the recursive splitter.
        is_separator_regex: Whether separator values should be interpreted as regex patterns.
    """

    chunk_size: int = 700
    chunk_overlap: int = 120
    add_start_index: bool = True
    separators: list[str] = field(default_factory=lambda: ["\n\n", "\n", " ", ""])
    is_separator_regex: bool = False


@dataclass(slots=True)
class TokenParams:
    """Configuration for token-aware chunk splitting.

    Attributes:
        chunk_size: Maximum token count allowed in each emitted chunk.
        chunk_overlap: Number of trailing tokens repeated into the next chunk.
        encoding_name: Tokenizer encoding used when ``model_name`` is not provided.
        model_name: Optional model-specific tokenizer override.
    """

    chunk_size: int = 800
    chunk_overlap: int = 100
    encoding_name: str = "cl100k_base"
    model_name: str | None = None


StageParams: TypeAlias = RecursiveParams | TokenParams
