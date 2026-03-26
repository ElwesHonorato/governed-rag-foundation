"""Chunk-oriented Elasticsearch policies shared by indexing and retrieval flows."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from pipeline_common.elasticsearch.contracts import (
    ElasticsearchRetrievedDocument,
    ElasticsearchRetrievedDocumentList,
    IndexedChunkDocument,
)


CHUNK_DOCUMENT = "chunk_document"
CHUNK_SEARCH = "chunk_search"


@dataclass(frozen=True)
class ChunkDocumentIndexPolicy:
    """Chunk-specific Elasticsearch indexing policy."""

    @property
    def index_mappings(self) -> dict[str, Any]:
        """Return the Elasticsearch mappings for chunk documents."""
        return {
            "properties": {
                "chunk_id": {"type": "keyword"},
                "doc_id": {"type": "keyword"},
                "chunk_text": {"type": "text"},
                "source_uri": {"type": "keyword"},
                "artifact_uri": {"type": "keyword"},
                "content_type": {"type": "keyword"},
                "created_at": {"type": "date"},
                "security_clearance": {"type": "keyword"},
                "source_type": {"type": "keyword"},
                "chunk_text_hash": {"type": "keyword"},
                "offsets_start": {"type": "integer"},
                "offsets_end": {"type": "integer"},
                "processor_name": {"type": "keyword"},
                "processor_version": {"type": "keyword"},
                "metadata": {"type": "object", "enabled": True},
            }
        }

    def document_id(self, document: object) -> str:
        """Return the Elasticsearch document id for one indexed chunk document."""
        indexed_document = _require_indexed_chunk_document(document)
        return indexed_document.document_id

    def serialize_document(self, document: object) -> dict[str, Any]:
        """Serialize one indexed chunk document for Elasticsearch indexing."""
        indexed_document = _require_indexed_chunk_document(document)
        return indexed_document.to_dict


@dataclass(frozen=True)
class ChunkSearchPolicy:
    """Chunk-specific Elasticsearch lexical search policy."""

    def build_request(self, query_text: str, limit: int) -> dict[str, Any]:
        """Build the Elasticsearch request body for lexical chunk retrieval."""
        safe_query = query_text.strip()
        if not safe_query:
            return {"size": 0, "query": {"match_none": {}}}
        return {
            "size": max(1, min(limit, 20)),
            "query": {
                "match": {
                    "chunk_text": {
                        "query": safe_query,
                    }
                }
            },
        }

    def build_response(self, hits: list[dict[str, Any]]) -> ElasticsearchRetrievedDocumentList:
        """Build the typed chunk retrieval result set from raw Elasticsearch hits."""
        return ElasticsearchRetrievedDocumentList(
            documents=[self._build_retrieved_document(hit) for hit in hits],
        )

    def _build_retrieved_document(self, hit: dict[str, Any]) -> ElasticsearchRetrievedDocument:
        """Build one typed chunk retrieval result from a raw Elasticsearch hit."""
        source = hit["_source"]
        if not isinstance(source, dict):
            raise TypeError("Elasticsearch hit _source must be a dictionary")
        return ElasticsearchRetrievedDocument.from_dict(
            {
                "chunk_id": source["chunk_id"],
                "doc_id": source["doc_id"],
                "chunk_text": source["chunk_text"],
                "source_uri": source["source_uri"],
                "artifact_uri": source["artifact_uri"],
                "security_clearance": source["security_clearance"],
                "score": hit["_score"],
            }
        )


def _require_indexed_chunk_document(document: object) -> IndexedChunkDocument:
    """Return the typed chunk document or raise when the policy is misused."""
    if not isinstance(document, IndexedChunkDocument):
        raise TypeError("expected IndexedChunkDocument")
    return document


ELASTICSEARCH_POLICIES = {
    CHUNK_DOCUMENT: ChunkDocumentIndexPolicy(),
    CHUNK_SEARCH: ChunkSearchPolicy(),
}
