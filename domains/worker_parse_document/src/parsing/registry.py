from collections.abc import Iterable

from parsing.base_parser import DocumentParser


class UnsupportedDocumentTypeError(ValueError):
    """Raised when no parser is registered for a given source key."""


class ParserRegistry:
    """Registry-based parser resolution by source-key extension."""

    def __init__(self, parsers: Iterable[DocumentParser] | None = None) -> None:
        """Initialize parser storage and preload provided parsers."""
        self._parsers_by_extension: dict[str, DocumentParser] = {}
        for parser in parsers or ():
            self.register(parser)

    def register(self, parser: DocumentParser) -> None:
        """Register parser for each normalized extension yielded by helper."""
        for extension in self._iter_normalized_extensions(parser):
            self._register_extension(extension, parser)

    def resolve(self, source_key: str) -> DocumentParser:
        """Return parser for source key or raise unsupported type error."""
        parser = self._parser_for_source_key(source_key)
        if parser is None:
            self._raise_unsupported_source_key(source_key)
        return parser

    def _normalize_extension(self, extension: str) -> str:
        """Normalize extension to lowercase with no leading dot."""
        return extension.strip().lower().lstrip(".")

    def _extension_from_key(self, source_key: str) -> str:
        """Extract lowercase file extension from source key."""
        normalized = source_key.lower().strip()
        if "." not in normalized:
            return ""
        return normalized.rsplit(".", maxsplit=1)[1]

    def _iter_normalized_extensions(self, parser: DocumentParser) -> Iterable[str]:
        """Yield each non-empty normalized extension declared by the parser."""
        for extension in parser.supported_extensions():
            normalized_extension = self._normalize_extension(extension)
            if normalized_extension:
                yield normalized_extension

    def _register_extension(self, extension: str, parser: DocumentParser) -> None:
        """Register parser under one extension, enforcing uniqueness."""
        if self._has_parser_for_extension(extension):
            raise ValueError(f"Parser already registered for extension '{extension}'")
        self._parsers_by_extension[extension] = parser

    def _has_parser_for_extension(self, extension: str) -> bool:
        """Return whether one parser is already bound to extension."""
        return extension in self._parsers_by_extension

    def _parser_for_source_key(self, source_key: str) -> DocumentParser | None:
        """Return parser mapped to source key extension when present."""
        return self._parsers_by_extension.get(self._extension_from_key(source_key))

    def _raise_unsupported_source_key(self, source_key: str) -> None:
        """Raise unsupported document type error for source key."""
        raise UnsupportedDocumentTypeError(f"Unsupported document type for key: {source_key}")
