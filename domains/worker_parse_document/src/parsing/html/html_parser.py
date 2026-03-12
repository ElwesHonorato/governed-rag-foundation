"""Parsing utilities for parsing."""
import json

from typing import Any

import trafilatura
from pipeline_common.stages_contracts import Content


class HtmlParser:
    """HTML parser adapter backed by trafilatura content extraction."""
    VERSION = "1.0.0"

    def supported_extensions(self) -> tuple[str, ...]:
        """Execute supported extensions."""
        return ("html", "htm")

    def parse(self, content: str) -> Content:
        """Extract parser payload fields from HTML content."""
        extracted_json = trafilatura.extract(
            content,
            output_format="json",
            with_metadata=True,
            include_comments=False,
            include_tables=False,
            favor_precision=True,
        )
        if isinstance(extracted_json, str):
            try:
                parsed = json.loads(extracted_json)
            except json.JSONDecodeError:
                parsed = {}
            if isinstance(parsed, dict):
                parsed_payload: dict[str, Any] = dict(parsed)
            else:
                parsed_payload = {}
            text = str(parsed_payload.get("text", "")).strip()
            if text:
                return Content(data=text)

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
        return Content(data=fallback_text)
