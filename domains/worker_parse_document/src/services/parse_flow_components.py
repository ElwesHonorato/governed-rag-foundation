from dataclasses import dataclass
import mimetypes
from pathlib import Path
from typing import Any

from parsing.registry import ParserRegistry
from pipeline_common.stages_contracts import (
    BaseProcessor,
    ProcessedDocumentPayload,
    SourceDocumentMetadata,
)
from pipeline_common.gateways.queue import Envelope


@dataclass(frozen=True)
class ParseWorkItem:
    """One parse work item derived from inbound queue payload."""

    source_key: str
    doc_id: str
    destination_key: str


class DocumentParserProcessor(BaseProcessor):
    """Transform source text into processed parse payload."""
    VERSION = "1.0.0"
    STAGE_NAME = "parse_document"

    def __init__(
        self,
        *,
        parser_registry: ParserRegistry,
        security_clearance: str,
        spark_session: Any | None,
    ) -> None:
        self._parser_registry = parser_registry
        self._security_clearance = security_clearance
        self._spark_session = spark_session

    def build_payload(self, *, source_key: str, doc_id: str, raw_text: str, timestamp: str) -> dict[str, Any]:
        parser = self._parser_registry.resolve(source_key)
        parsed_payload = parser.parse(raw_text)
        metadata = SourceDocumentMetadata.build(
            doc_id=doc_id,
            source_key=source_key,
            timestamp=timestamp,
            security_clearance=self._security_clearance,
            source_type=Path(source_key).suffix.lower().lstrip("."),
            content_type=str(mimetypes.guess_type(source_key)[0] or "application/octet-stream"),
        )
        processor_metadata = self._build_processor_metadata()
        return ProcessedDocumentPayload(
            metadata=metadata,
            processor_metadata=processor_metadata,
            parsed=parsed_payload,
        ).to_dict()


class ParseOutputMessageFactory:
    """Build downstream output message after successful parse write."""

    @staticmethod
    def build(*, destination_key: str) -> Envelope:
        return Envelope(
            type="chunk_text.request",
            payload={"storage_key": destination_key},
        )
