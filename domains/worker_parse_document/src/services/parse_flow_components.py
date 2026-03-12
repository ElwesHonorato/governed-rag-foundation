import mimetypes
from pathlib import Path
from typing import Any

from parsing.registry import ParserRegistry
from pipeline_common.stages_contracts import (
    BaseProcessor,
    RootDocumentMetadata,
    StageArtifact,
    StageArtifactMetadata,
)


class DocumentParserProcessor(BaseProcessor):
    """Transform source text into processed parse payload."""
    VERSION = "1.0.0"
    STAGE_NAME = "parse_document"

    def __init__(
        self,
        *,
        parser_registry: ParserRegistry,
        security_clearance: str,
    ) -> None:
        self._parser_registry = parser_registry
        self._security_clearance = security_clearance

    def build_payload(
        self,
        *,
        source_uri: str,
        doc_id: str,
        raw_text: str,
        raw_content_hash: str,
        timestamp: str,
    ) -> dict[str, Any]:
        parser = self._parser_registry.resolve(source_uri)
        parsed_payload = parser.parse(raw_text)
        root_metadata = RootDocumentMetadata(
            doc_id=doc_id,
            source_uri=source_uri,
            timestamp=timestamp,
            security_clearance=self._security_clearance,
            source_type=Path(source_uri).suffix.lower().lstrip("."),
            content_type=str(mimetypes.guess_type(source_uri)[0] or "application/octet-stream"),
            source_content_hash=raw_content_hash,
        )
        processor_metadata = self._build_processor_metadata()
        return StageArtifact(
            metadata=StageArtifactMetadata(
                processor=processor_metadata,
                root=root_metadata,
                content={"contract": "Content"},
                params=[],
            ),
            content=parsed_payload,
        ).to_dict
