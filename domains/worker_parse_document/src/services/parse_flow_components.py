from dataclasses import dataclass
from typing import Any

from parsing.registry import ParserRegistry
from pipeline_common.stages_contracts import ProcessedDocumentMetadata, ProcessedDocumentPayload
from pipeline_common.gateways.queue import Envelope


@dataclass(frozen=True)
class ParseWorkItem:
    """One parse work item derived from inbound queue payload."""

    source_key: str
    doc_id: str
    destination_key: str


class DocumentParserProcessor:
    """Transform source text into processed parse payload."""

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
        metadata = ProcessedDocumentMetadata.build(
            doc_id=doc_id,
            source_key=source_key,
            timestamp=timestamp,
            security_clearance=self._security_clearance,
        )
        return ProcessedDocumentPayload(
            metadata=metadata,
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
