"""Shared Elasticsearch infrastructure adapter."""

from __future__ import annotations

from typing import Any, Protocol

from elasticsearch import Elasticsearch


class ElasticsearchIndexPolicy(Protocol):
    """Policy for index creation and document indexing behavior."""

    @property
    def index_mappings(self) -> dict[str, Any]:
        """Return the Elasticsearch index mappings."""

    def document_id(self, document: object) -> str:
        """Return the Elasticsearch document id for one document."""

    def serialize_document(self, document: object) -> dict[str, Any]:
        """Serialize one document for Elasticsearch indexing."""


class ElasticsearchSearchPolicy(Protocol):
    """Policy for Elasticsearch search request and result behavior."""

    def build_request(self, query_text: str, limit: int) -> dict[str, Any]:
        """Build one Elasticsearch search request."""

    def build_response(self, hits: list[dict[str, Any]]) -> object:
        """Build one typed result object from raw Elasticsearch hits."""


class ElasticsearchGateway:
    """Narrow runtime facade for Elasticsearch indexing and search operations."""

    def __init__(
        self,
        *,
        url: str,
        index_name: str,
        index_policy: ElasticsearchIndexPolicy,
        search_policy: ElasticsearchSearchPolicy,
        timeout_seconds: float = 10.0,
    ) -> None:
        """Initialize Elasticsearch client state."""
        self._index_name = index_name.strip()
        self._client = Elasticsearch(url.strip(), request_timeout=timeout_seconds)
        self._index_policy = index_policy
        self._search_policy = search_policy

    @property
    def index_name(self) -> str:
        """Return the configured Elasticsearch index name."""
        return self._index_name

    def ping(self) -> bool:
        """Return whether Elasticsearch is reachable."""
        return bool(self._client.ping())

    def ensure_index(self) -> None:
        """Create the configured index if it does not already exist."""
        if self._client.indices.exists(index=self._index_name):
            return
        self._client.indices.create(
            index=self._index_name,
            mappings=self._index_policy.index_mappings,
        )

    def index_document(self, document: object) -> None:
        """Upsert one document into Elasticsearch."""
        self.ensure_index()
        self._client.index(
            index=self._index_name,
            id=self._index_policy.document_id(document),
            document=self._index_policy.serialize_document(document),
            refresh="false",
        )

    def search(self, *, query_text: str, limit: int) -> object:
        """Run one configured Elasticsearch search operation."""
        response = self._client.search(
            index=self._index_name,
            **self._search_policy.build_request(query_text, limit),
        )
        hits = response.get("hits", {}).get("hits", [])
        if not isinstance(hits, list):
            hits = []
        return self._search_policy.build_response([hit for hit in hits if isinstance(hit, dict)])
