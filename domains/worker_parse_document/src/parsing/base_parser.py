from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True, slots=True)
class ParsedDocument:
    """Immutable parsed-document value object used across parser boundaries."""

    title: str
    text: str


class DocumentParser(Protocol):
    """Parser interface for document formats keyed by file extension."""

    def supported_extensions(self) -> tuple[str, ...]:
        """Return lower-cased extensions without leading dots."""
        ...

    def parse(self, content: str) -> ParsedDocument:
        """Convert raw document content into normalized text fields."""
        ...
