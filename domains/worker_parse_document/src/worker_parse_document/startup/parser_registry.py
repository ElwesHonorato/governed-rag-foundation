"""Default parser registry assembly for worker_parse_document."""

from worker_parse_document.parsing.html import HtmlParser
from worker_parse_document.parsing.registry import ParserRegistry


def build_parser_registry() -> ParserRegistry:
    """Build the default parser registry for parse_document."""
    return ParserRegistry(parsers=[HtmlParser()])
