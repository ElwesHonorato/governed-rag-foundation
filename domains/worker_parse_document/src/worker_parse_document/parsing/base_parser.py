from abc import ABC, abstractmethod

from pipeline_common.stages_contracts import Content

class DocumentParser(ABC):
    """Parser interface for document formats keyed by file extension."""

    @abstractmethod
    def supported_extensions(self) -> tuple[str, ...]:
        """Return lower-cased extensions without leading dots."""
        raise NotImplementedError

    @abstractmethod
    def parse(self, content: str) -> Content:
        """Convert raw document content into parser-specific payload fields."""
        raise NotImplementedError
