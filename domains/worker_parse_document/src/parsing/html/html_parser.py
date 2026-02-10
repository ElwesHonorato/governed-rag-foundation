import json

import trafilatura

from parsing.base_parser import ParsedDocument


DEFAULT_TITLE = "Untitled"


class HtmlParser:
    """HTML parser adapter backed by trafilatura content extraction."""

    def supported_extensions(self) -> tuple[str, ...]:
        return ("html", "htm")

    def parse(self, content: str) -> ParsedDocument:
        """Extract canonical title/text fields from HTML content."""
        extracted_json = trafilatura.extract(
            content,
            output_format="json",
            with_metadata=True,
            include_comments=False,
            include_tables=False,
            favor_precision=True,
        )
        title = DEFAULT_TITLE
        if isinstance(extracted_json, str):
            try:
                parsed = json.loads(extracted_json)
            except json.JSONDecodeError:
                parsed = {}
            title = str(parsed.get("title", "")).strip() or DEFAULT_TITLE
            text = str(parsed.get("text", "")).strip()
            if text:
                return ParsedDocument(title=title, text=text)

        fallback_text = (
            trafilatura.extract(
                content,
                output_format="txt",
                include_comments=False,
                include_tables=False,
                favor_precision=True,
            )
            or ""
        ).strip()
        return ParsedDocument(title=title, text=fallback_text)
