from abc import ABC, abstractmethod

from typing import Any

class DocumentParser(ABC):
    """Parser interface for document formats keyed by file extension."""

    @abstractmethod
    def supported_extensions(self) -> tuple[str, ...]:
        """Return lower-cased extensions without leading dots."""
        raise NotImplementedError

    @abstractmethod
    def parse(self, content: str) -> dict[str, Any]:
        """Convert raw document content into parser-specific payload fields."""
        raise NotImplementedError
