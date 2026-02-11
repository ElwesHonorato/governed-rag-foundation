from dataclasses import dataclass
from abc import ABC, abstractmethod


@dataclass(frozen=True, slots=True)
class ParsedDocument:
    """Immutable parsed-document value object used across parser boundaries."""

    title: str
    text: str


class DocumentParser(ABC):
    """Parser interface for document formats keyed by file extension."""

    @abstractmethod
    def supported_extensions(self) -> tuple[str, ...]:
        """Return lower-cased extensions without leading dots."""
        raise NotImplementedError

    @abstractmethod
    def parse(self, content: str) -> ParsedDocument:
        """Convert raw document content into normalized text fields."""
        raise NotImplementedError
