"""Shared Elasticsearch infrastructure adapter."""

from __future__ import annotations

from typing import Any

from elasticsearch import Elasticsearch

from pipeline_common.elasticsearch import ElasticsearchRetrievedDocument, IndexedChunkDocument


class ElasticsearchGateway:
    """Narrow runtime facade for indexing and querying chunk documents."""

    def __init__(
        self,
        *,
        url: str,
        index_name: str,
        timeout_seconds: float = 10.0,
    ) -> None:
        """Initialize Elasticsearch client state."""
        self._index_name = index_name.strip()
        self._client = Elasticsearch(url.strip(), request_timeout=timeout_seconds)

    @property
    def index_name(self) -> str:
        """Return the configured Elasticsearch index name."""
        return self._index_name

    def ping(self) -> bool:
        """Return whether Elasticsearch is reachable."""
        return bool(self._client.ping())

    def ensure_chunk_index(self) -> None:
        """Create the chunk index if it does not already exist."""
        if self._client.indices.exists(index=self._index_name):
            return
        self._client.indices.create(
            index=self._index_name,
            mappings={
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
            },
        )

    def index_chunk(self, document: IndexedChunkDocument) -> None:
        """Upsert one chunk document into Elasticsearch."""
        self.ensure_chunk_index()
        self._client.index(
            index=self._index_name,
            id=document.document_id,
            document=document.to_dict,
            refresh="false",
        )

    def search(self, *, query_text: str, limit: int) -> list[dict[str, Any]]:
        """Run a BM25-style search over indexed chunk text."""
        safe_query = query_text.strip()
        if not safe_query:
            return []
        response = self._client.search(
            index=self._index_name,
            size=max(1, min(limit, 20)),
            query={
                "match": {
                    "chunk_text": {
                        "query": safe_query,
                    }
                }
            },
        )
        hits = response.get("hits", {}).get("hits", [])
        if not isinstance(hits, list):
            return []
        return [self._to_retrieved_document(hit).to_dict for hit in hits if isinstance(hit, dict)]

    def _to_retrieved_document(self, hit: dict[str, Any]) -> ElasticsearchRetrievedDocument:
        """Build one normalized retrieval result from a raw Elasticsearch hit."""
        source = hit.get("_source", {})
        if not isinstance(source, dict):
            source = {}
        raw_score = hit.get("_score", 0.0)
        score = float(raw_score) if isinstance(raw_score, (float, int)) else 0.0
        return ElasticsearchRetrievedDocument(
            chunk_id=str(source.get("chunk_id", "")),
            doc_id=str(source.get("doc_id", "")),
            chunk_text=str(source.get("chunk_text", "")),
            source_uri=str(source.get("source_uri", "")),
            artifact_uri=str(source.get("artifact_uri", "")),
            security_clearance=str(source.get("security_clearance", "")),
            score=score,
        )
