from collections.abc import Iterable


from parsing.base_parser import DocumentParser


class UnsupportedDocumentTypeError(ValueError):
    """Raised when no parser is registered for a given source URI."""


class ParserRegistry:
    """Registry-based parser resolution by source-URI extension."""

    def __init__(self, parsers: Iterable[DocumentParser] | None = None) -> None:
        """Initialize parser storage and preload provided parsers."""
        self._parsers_by_extension: dict[str, DocumentParser] = {}
        for parser in parsers or ():
            self.register(parser)

    def register(self, parser: DocumentParser) -> None:
        """Register parser for each normalized extension yielded by helper."""
        for extension in self._iter_normalized_extensions(parser):
            self._register_extension(extension, parser)

    def resolve(self, source_uri: str) -> DocumentParser:
        """Return parser for source URI or raise unsupported type error."""
        parser = self._parser_for_source_uri(source_uri)
        if parser is None:
            self._raise_unsupported_source_uri(source_uri)
        return parser

    def _normalize_extension(self, extension: str) -> str:
        """Normalize extension to lowercase with no leading dot."""
        return extension.strip().lower().lstrip(".")

    def _extension_from_uri(self, source_uri: str) -> str:
        """Extract lowercase file extension from source URI."""
        normalized = source_uri.lower().strip()
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

    def _parser_for_source_uri(self, source_uri: str) -> DocumentParser | None:
        """Return parser mapped to source URI extension when present."""
        return self._parsers_by_extension.get(self._extension_from_uri(source_uri))

    def _raise_unsupported_source_uri(self, source_uri: str) -> None:
        """Raise unsupported document type error for source URI."""
        raise UnsupportedDocumentTypeError(f"Unsupported document type for URI: {source_uri}")
