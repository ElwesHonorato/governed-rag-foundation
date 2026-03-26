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


class ElasticsearchIndexGateway:
    """Narrow runtime facade for Elasticsearch indexing operations."""

    def __init__(
        self,
        *,
        client: Elasticsearch,
        index_name: str,
        index_policy: ElasticsearchIndexPolicy,
    ) -> None:
        """Initialize Elasticsearch client state."""
        self.index_name = index_name.strip()
        self._client = client
        self._index_policy = index_policy

    def ensure_index(self) -> None:
        """Create the configured index if it does not already exist."""
        if self._client.indices.exists(index=self.index_name):
            return
        self._client.indices.create(
            index=self.index_name,
            mappings=self._index_policy.index_mappings,
        )

    def index_document(self, document: object) -> None:
        """Upsert one document into Elasticsearch."""
        self.ensure_index()
        self._client.index(
            index=self.index_name,
            id=self._index_policy.document_id(document),
            document=self._index_policy.serialize_document(document),
            refresh="false",
        )


class ElasticsearchSearchGateway:
    """Narrow runtime facade for Elasticsearch search operations."""

    def __init__(
        self,
        *,
        url: str,
        index_name: str,
        search_policy: ElasticsearchSearchPolicy,
        timeout_seconds: float = 10.0,
    ) -> None:
        """Initialize Elasticsearch client state."""
        self.index_name = index_name.strip()
        self._client = Elasticsearch(url.strip(), request_timeout=timeout_seconds)
        self._search_policy = search_policy

    def search(self, *, query_text: str, limit: int) -> object:
        """Run one configured Elasticsearch search operation."""
        response = self._search_response(query_text=query_text, limit=limit)
        return self._search_policy.build_response(self._search_hits(response))

    def _search_response(self, *, query_text: str, limit: int) -> dict[str, Any]:
        """Run one raw Elasticsearch search request."""
        return self._client.search(
            index=self.index_name,
            **self._search_policy.build_request(query_text, limit),
        )

    def _search_hits(self, response: dict[str, Any]) -> list[dict[str, Any]]:
        """Return raw Elasticsearch hits filtered to dictionaries only."""
        hits = response.get("hits", {}).get("hits", [])
        if not isinstance(hits, list):
            hits = []
        return [hit for hit in hits if isinstance(hit, dict)]
