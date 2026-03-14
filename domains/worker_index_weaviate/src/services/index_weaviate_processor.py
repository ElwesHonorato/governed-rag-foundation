"""Indexing processor implementation for worker_index_weaviate."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from pipeline_common.gateways.object_storage import ObjectStorageGateway
from pipeline_common.helpers.contracts import doc_id_from_source_uri
from pipeline_common.provenance import source_content_hash
from pipeline_common.stages_contracts import FileMetadata, ProcessResult, ProcessorContext
from pipeline_common.stages_contracts.step_00_common import ProcessorMetadata
from services.index_flow import IndexStatusWriter
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
    def read_embeddings_payload(raw_payload: bytes) -> dict[str, Any]:
        """Parse one embeddings artifact payload from storage."""
        return dict(json.loads(raw_payload.decode("utf-8", errors="ignore")))

    def process(
        self,
        *,
        input_uri: str,
        raw_payload: bytes,
    ) -> ProcessResult:
        """Index one embeddings artifact and build the process result."""
        payload = self.read_embeddings_payload(raw_payload)
        resolved_doc_id = str(payload.get("doc_id", ""))
        resolved_chunk_id = str(payload.get("chunk_id", ""))
        destination_key = self.build_indexed_key(resolved_doc_id, resolved_chunk_id)
        self._upsert_embeddings(payload)
        self._write_index_status(destination_key, resolved_doc_id, resolved_chunk_id)
        metadata = dict(payload.get("metadata", {}))
        source_uri = str(metadata.get("source_uri") or "")
        return ProcessResult(
            run_id=resolved_chunk_id or resolved_doc_id,
            root_doc_metadata=FileMetadata(
                doc_id=resolved_doc_id,
                uri=source_uri,
                timestamp=str(metadata.get("timestamp") or ""),
                security_clearance=str(metadata.get("security_clearance") or ""),
                source_type=Path(source_uri).suffix.lower().lstrip("."),
                content_type="application/json",
                source_content_hash="",
            ),
            stage_doc_metadata=FileMetadata(
                doc_id=doc_id_from_source_uri(input_uri),
                uri=input_uri,
                timestamp=str(metadata.get("timestamp") or ""),
                security_clearance=str(metadata.get("security_clearance") or ""),
                source_type=Path(input_uri).suffix.lower().lstrip("."),
                content_type="application/json",
                source_content_hash=source_content_hash(raw_payload),
            ),
            input_uri=input_uri,
            processor_context=ProcessorContext(params_hash="", params=[]),
            processor=ProcessorMetadata(name="IndexWeaviateProcessor", version="1.0.0"),
            result={
                "destination_key": destination_key,
                "output_uri": self._status_writer.output_uri(destination_key),
            },
        )

    def build_upsert_items(self, payload: dict[str, Any]) -> list[dict[str, Any]]:
        """Build the Weaviate upsert payloads for one embeddings artifact."""
        return self._build_upsert_items_local(payload)

    @staticmethod
    def _build_upsert_items_local(payload: dict[str, Any]) -> list[dict[str, Any]]:
        if isinstance(payload.get("embeddings"), list):
            items = payload.get("embeddings", [])
        else:
            items = [payload]
        records: list[dict[str, Any]] = []
        for item in items:
            metadata = dict(item.get("metadata", {}))
            chunk_id = str(item["chunk_id"])
            records.append(
                {
                    "chunk_id": chunk_id,
                    "vector": item.get("vector", []),
                    "properties": {
                        "chunk_id": chunk_id,
                        "doc_id": metadata.get("doc_id"),
                        "chunk_text": metadata.get("chunk_text"),
                        "source_uri": metadata.get("source_uri"),
                        "security_clearance": metadata.get("security_clearance"),
                        "run_id": metadata.get("run_id"),
                        "embedder_name": metadata.get("embedder_name"),
                        "embedder_version": metadata.get("embedder_version"),
                        "embedding_params_hash": metadata.get("embedding_params_hash"),
                        "embedding_run_id": metadata.get("embedding_run_id"),
                    },
                }
            )
        return records

    def build_indexed_key(self, doc_id: str, chunk_id: str) -> str:
        """Build the destination key for the index status artifact."""
        if chunk_id:
            return f"{self._output_prefix}{doc_id}/{chunk_id}.indexed.json"
        return f"{self._output_prefix}{doc_id}.indexed.json"

    @staticmethod
    def build_index_status_payload(doc_id: str, chunk_id: str) -> dict[str, Any]:
        """Build the storage payload for one successful indexing status."""
        status_payload: dict[str, Any] = {"doc_id": doc_id, "status": "indexed"}
        if chunk_id:
            status_payload["chunk_id"] = chunk_id
        return status_payload

    def _upsert_embeddings(self, payload: dict[str, Any]) -> None:
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
