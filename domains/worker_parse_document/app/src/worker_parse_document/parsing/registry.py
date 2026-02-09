from __future__ import annotations

from worker_parse_document.parsing.base import DocumentParser
from worker_parse_document.parsing.html_parser import HtmlParser


def parser_for_key(source_key: str) -> DocumentParser:
    if source_key.lower().endswith(".html") or source_key.lower().endswith(".htm"):
        return HtmlParser()
    raise ValueError(f"Unsupported document type for key: {source_key}")
