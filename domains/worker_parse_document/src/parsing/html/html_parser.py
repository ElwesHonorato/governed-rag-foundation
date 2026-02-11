"""Parsing utilities for parsing."""
import json

from typing import Any

import trafilatura

DEFAULT_TITLE = "Untitled"


class HtmlParser:
    """HTML parser adapter backed by trafilatura content extraction."""

    def supported_extensions(self) -> tuple[str, ...]:
        """Execute supported extensions."""
        return ("html", "htm")

    def parse(self, content: str) -> dict[str, Any]:
        """Extract parser payload fields from HTML content."""
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
            if isinstance(parsed, dict):
                parsed_payload: dict[str, Any] = dict(parsed)
            else:
                parsed_payload = {}
            title = str(parsed_payload.get("title", "")).strip() or DEFAULT_TITLE
            text = str(parsed_payload.get("text", "")).strip()
            if text:
                parsed_payload["title"] = title
                parsed_payload["text"] = text
                return parsed_payload

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
        return {"title": title, "text": fallback_text}
