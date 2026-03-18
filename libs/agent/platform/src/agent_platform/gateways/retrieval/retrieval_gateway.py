"""Gateway adapter for retrieval backed by the configured retrieval client."""

from __future__ import annotations

from ai_infra.retrieval.deterministic_hash_embedder import (
    DeterministicHashEmbedder,
)
from agent_platform.clients.retrieval.weaviate_client import (
    RetrievedChunk,
    WeaviateClient,
)
from agent_platform.startup.contracts import RetrievalParams


class RetrievalGateway:
    """Expose an app-facing retrieval boundary over the configured retrieval client."""

    def __init__(
        self,
        *,
        client: WeaviateClient,
        embedder: DeterministicHashEmbedder,
        params: RetrievalParams,
    ) -> None:
        self._client = client
        self._embedder = embedder
        self.params = params

    def retrieve(self, *, query_text: str, limit: int) -> list[RetrievedChunk]:
        return self._client.retrieve(
            query_text=query_text,
            limit=limit,
            embedder=self._embedder,
        )
