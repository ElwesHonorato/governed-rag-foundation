from collections.abc import Iterable

from parsing.base_parser import DocumentParser
from parsing.html import HtmlParser


class UnsupportedDocumentTypeError(ValueError):
    """Raised when no parser is registered for a given source key."""


class ParserRegistry:
    """Registry-based parser resolution by source-key extension."""

    def __init__(self, parsers: Iterable[DocumentParser] | None = None) -> None:
        self._parsers_by_extension: dict[str, DocumentParser] = {}
        for parser in parsers or ():
            self.register(parser)

    def register(self, parser: DocumentParser) -> None:
        """Register a parser instance for all extensions it supports."""
        for extension in parser.supported_extensions():
            normalized_extension = self._normalize_extension(extension)
            if not normalized_extension:
                continue
            if normalized_extension in self._parsers_by_extension:
                raise ValueError(f"Parser already registered for extension '{normalized_extension}'")
            self._parsers_by_extension[normalized_extension] = parser

    def resolve(self, source_key: str) -> DocumentParser:
        """Resolve the parser for a source key or raise a domain-specific error."""
        parser = self._parsers_by_extension.get(self._extension_from_key(source_key))
        if parser is None:
            raise UnsupportedDocumentTypeError(f"Unsupported document type for key: {source_key}")
        return parser

    def can_resolve(self, source_key: str) -> bool:
        """Return whether a parser exists for the source key extension."""
        return self._extension_from_key(source_key) in self._parsers_by_extension

    def _normalize_extension(self, extension: str) -> str:
        return extension.strip().lower().lstrip(".")

    def _extension_from_key(self, source_key: str) -> str:
        normalized = source_key.lower().strip()
        if "." not in normalized:
            return ""
        return normalized.rsplit(".", maxsplit=1)[1]


def build_default_parser_registry() -> ParserRegistry:
    """Build the production parser registry with built-in parser adapters."""
    return ParserRegistry(parsers=[HtmlParser()])
