"""Indexing processor implementation for worker_index_weaviate."""

from __future__ import annotations

import json
import logging

from pipeline_common.gateways.object_storage import ObjectStorageGateway
from pipeline_common.stages_contracts import ProcessResult, ProcessorContext
from pipeline_common.stages_contracts.step_00_common import ProcessorMetadata
from services.embed_flow import EmbeddingArtifact
from services.index_flow import IndexStatusArtifact, IndexStatusWriter
from services.weaviate_gateway import upsert_chunk, verify_query

logger = logging.getLogger(__name__)


class IndexWeaviateProcessor:
    """Build indexing instructions and status payloads."""

    def __init__(
        self,
        *,
        object_storage: ObjectStorageGateway,
        status_writer: IndexStatusWriter,
        storage_bucket: str,
        output_prefix: str,
        weaviate_url: str,
    ) -> None:
        """Initialize index processor dependencies."""
        self._object_storage = object_storage
        self._status_writer = status_writer
        self._storage_bucket = storage_bucket
        self._output_prefix = output_prefix
        self._weaviate_url = weaviate_url

    @staticmethod
    def read_embeddings_payload(raw_payload: bytes) -> EmbeddingArtifact:
        """Parse one embeddings artifact payload from storage."""
        payload = dict(json.loads(raw_payload.decode("utf-8", errors="ignore")))
        return EmbeddingArtifact.from_dict(payload)

    def process(
        self,
        *,
        input_uri: str,
        raw_payload: bytes,
    ) -> ProcessResult:
        """Index one embeddings artifact and build the process result."""
        payload = self.read_embeddings_payload(raw_payload)
        resolved_doc_id = payload.doc_id
        resolved_chunk_id = payload.chunk_id
        destination_key = self.build_indexed_key(resolved_doc_id, resolved_chunk_id)
        self._upsert_embeddings(payload)
        self._write_index_status(destination_key, resolved_doc_id, resolved_chunk_id)
        return ProcessResult(
            run_id=resolved_chunk_id or resolved_doc_id,
            root_doc_metadata=payload.metadata.root_doc_metadata,
            stage_doc_metadata=payload.metadata.stage_doc_metadata,
            input_uri=input_uri,
            processor_context=ProcessorContext(params_hash="", params=[]),
            processor=ProcessorMetadata(name="IndexWeaviateProcessor", version="1.0.0"),
            result={
                "destination_key": destination_key,
                "output_uri": self._status_writer.output_uri(destination_key),
            },
        )

    def build_upsert_items(self, payload: EmbeddingArtifact) -> list[dict[str, object]]:
        """Build the Weaviate upsert payloads for one embeddings artifact."""
        return [
            {
                "chunk_id": payload.chunk_id,
                "vector": payload.vector,
                "properties": {
                    "chunk_id": payload.chunk_id,
                    "doc_id": payload.doc_id,
                    "chunk_text": payload.chunk_text,
                    "source_uri": payload.metadata.root_doc_metadata.uri,
                    "security_clearance": payload.metadata.root_doc_metadata.security_clearance,
                    "run_id": payload.metadata.run_id,
                    "embedder_name": payload.metadata.embedder_name,
                    "embedder_version": payload.metadata.embedder_version,
                    "embedding_params_hash": payload.metadata.embedding_params_hash,
                    "embedding_run_id": payload.metadata.embedding_run_id,
                },
            }
        ]

    def build_indexed_key(self, doc_id: str, chunk_id: str) -> str:
        """Build the destination key for the index status artifact."""
        if chunk_id:
            return f"{self._output_prefix}{doc_id}/{chunk_id}.indexed.json"
        return f"{self._output_prefix}{doc_id}.indexed.json"

    @staticmethod
    def build_index_status_payload(doc_id: str, chunk_id: str) -> IndexStatusArtifact:
        """Build the storage payload for one successful indexing status."""
        return IndexStatusArtifact(doc_id=doc_id, status="indexed", chunk_id=chunk_id)

    def _upsert_embeddings(self, payload: EmbeddingArtifact) -> None:
        """Upsert the embedding records into Weaviate."""
        items = self.build_upsert_items(payload)
        for item in items:
            properties = dict(item.get("properties", {}))
            vector = list(item.get("vector", []))
            chunk_id = str(item["chunk_id"])
            upsert_chunk(
                self._weaviate_url,
                chunk_id=chunk_id,
                vector=vector,
                properties=properties,
            )

    def _write_index_status(self, destination_key: str, doc_id: str, chunk_id: str) -> None:
        """Write the index status artifact and log a verification query."""
        self._status_writer.write(
            destination_key=destination_key,
            payload=self.build_index_status_payload(doc_id, chunk_id),
        )
        result = verify_query(self._weaviate_url, "logistics")
        logger.info("Indexed doc_id '%s' verify=%s", doc_id, bool(result))
