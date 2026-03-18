"""Parse processor implementation for worker_parse_document."""

from __future__ import annotations

import mimetypes
from pathlib import Path
from typing import Any

from worker_parse_document.parsing.registry import ParserRegistry
from pipeline_common.helpers.contracts import utc_now_iso
from pipeline_common.provenance import source_content_hash
from pipeline_common.stages_contracts import (
    BaseProcessor,
    FileMetadata,
    ProcessResult,
    ProcessorContext,
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
        """Initialize parse processor dependencies."""
        self._parser_registry = parser_registry
        self._security_clearance = security_clearance

    def process(
        self,
        *,
        source_uri: str,
        doc_id: str,
        raw_payload: bytes,
        destination_key: str,
    ) -> ProcessResult:
        """Parse one source payload and build the process result."""
        timestamp = utc_now_iso()
        raw_text = raw_payload.decode("utf-8", errors="ignore")
        raw_content_hash = source_content_hash(raw_payload)
        payload = self._build_payload(
            source_uri=source_uri,
            doc_id=doc_id,
            raw_text=raw_text,
            raw_content_hash=raw_content_hash,
            timestamp=timestamp,
        )
        artifact = StageArtifact.from_dict(payload)
        return ProcessResult(
            run_id=doc_id,
            root_doc_metadata=artifact.root_doc_metadata,
            stage_doc_metadata=FileMetadata(
                doc_id=doc_id,
                uri=source_uri,
                timestamp=timestamp,
                security_clearance=artifact.root_doc_metadata.security_clearance,
                source_type=Path(source_uri).suffix.lower().lstrip("."),
                content_type="application/octet-stream",
                source_content_hash=raw_content_hash,
            ),
            input_uri=source_uri,
            processor_context=ProcessorContext(params_hash="", params=[]),
            processor=artifact.processor_metadata,
            result={
                "payload": payload,
                "destination_key": destination_key,
            },
        )

    def _build_payload(
        self,
        *,
        source_uri: str,
        doc_id: str,
        raw_text: str,
        raw_content_hash: str,
        timestamp: str,
    ) -> dict[str, Any]:
        """Build the parse stage artifact payload."""
        parser = self._parser_registry.resolve(source_uri)
        parsed_payload = parser.parse(raw_text)
        root_metadata = FileMetadata(
            doc_id=doc_id,
            uri=source_uri,
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
                root_doc_metadata=root_metadata,
                stage_doc_metadata=root_metadata,
                content_metadata={"contract": "Content"},
                params=[],
            ),
            content=parsed_payload,
        ).to_dict
