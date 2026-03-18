"""Gateway adapter for retrieval backed by the configured retrieval client."""

from __future__ import annotations

from agent_platform.clients.retrieval.weaviate_client import (
    RetrievedChunk,
    WeaviateClient,
)
from agent_platform.startup.contracts import RetrievalConfig


class RetrievalGateway:
    """Expose an app-facing retrieval boundary over the configured retrieval client."""

    def __init__(self, *, client: WeaviateClient, configs: RetrievalConfig) -> None:
        self._client = client
        self.configs = configs

    def retrieve(self, *, query_text: str, limit: int) -> list[RetrievedChunk]:
        return self._client.retrieve(query_text=query_text, limit=limit)
