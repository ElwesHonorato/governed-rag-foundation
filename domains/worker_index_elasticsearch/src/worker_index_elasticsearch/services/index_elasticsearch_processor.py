"""Processor that maps chunk ``StageArtifact`` payloads into Elasticsearch documents."""

from __future__ import annotations

import json
from typing import Any

from pipeline_common.elasticsearch import IndexedChunkDocument
from pipeline_common.gateways.elasticsearch import ElasticsearchGateway
from pipeline_common.provenance import chunk_params_hash
from pipeline_common.stages_contracts import ProcessResult, ProcessorContext, StageArtifact
from pipeline_common.stages_contracts.step_00_common import ProcessorMetadata


class IndexElasticsearchProcessor:
    """Build Elasticsearch documents from chunk-stage payloads and index them."""

    def __init__(self, *, elasticsearch_gateway: ElasticsearchGateway) -> None:
        """Store Elasticsearch runtime dependency."""
        self._elasticsearch_gateway = elasticsearch_gateway

    def process(self, *, input_uri: str, raw_payload: bytes) -> ProcessResult:
        """Index one chunk payload into Elasticsearch."""
        artifact = StageArtifact.from_dict(json.loads(raw_payload.decode("utf-8")))
        document = self._map_document(artifact=artifact, artifact_uri=input_uri)
        self._elasticsearch_gateway.index_chunk(document)
        return ProcessResult(
            run_id=document.chunk_id or document.doc_id,
            root_doc_metadata=artifact.root_doc_metadata,
            stage_doc_metadata=artifact.stage_doc_metadata,
            input_uri=input_uri,
            processor_context=ProcessorContext(
                params_hash=chunk_params_hash(artifact.params),
                params=artifact.params,
            ),
            processor=ProcessorMetadata(name="IndexElasticsearchProcessor", version="1.0.0"),
            result={
                "indexed_document_id": document.document_id,
                "elasticsearch_index": self._elasticsearch_gateway.index_name,
            },
        )

    def _map_document(self, *, artifact: StageArtifact, artifact_uri: str) -> IndexedChunkDocument:
        """Map one chunk artifact to the Elasticsearch document contract."""
        chunk_metadata = artifact.content_metadata
        if not isinstance(chunk_metadata, dict):
            raise ValueError("Chunk artifact metadata must be a dictionary.")
        root_metadata = artifact.root_doc_metadata
        processor_metadata = artifact.processor_metadata
        chunk_id = str(chunk_metadata["chunk_id"])
        return IndexedChunkDocument(
            document_id=chunk_id,
            chunk_id=chunk_id,
            doc_id=str(root_metadata.doc_id),
            chunk_text=str(artifact.content.data),
            source_uri=str(root_metadata.uri),
            artifact_uri=artifact_uri,
            content_type=str(root_metadata.content_type),
            created_at=str(root_metadata.timestamp),
            security_clearance=str(root_metadata.security_clearance),
            source_type=str(root_metadata.source_type),
            chunk_text_hash=str(chunk_metadata.get("chunk_text_hash", "")),
            offsets_start=int(chunk_metadata.get("offsets_start", 0)),
            offsets_end=int(chunk_metadata.get("offsets_end", 0)),
            processor_name=str(processor_metadata.name),
            processor_version=str(processor_metadata.version),
            metadata={
                "chunk_index": int(chunk_metadata.get("index", 0)),
                "params": artifact.params,
                "stage_doc_uri": str(artifact.stage_doc_metadata.uri),
            },
        )
