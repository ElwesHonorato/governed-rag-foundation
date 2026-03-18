"""Factory for retrieval gateway construction."""

from __future__ import annotations

from ai_infra.retrieval.deterministic_hash_embedder import (
    DeterministicHashEmbedder,
)
from agent_platform.clients.retrieval.weaviate_client import WeaviateClient
from agent_platform.gateways.retrieval.retrieval_gateway import RetrievalGateway
from agent_platform.startup.contracts import RetrievalConfig


class RetrievalGatewayFactory:
    """Build retrieval gateways for local agent-platform runtime."""

    def __init__(self, *, retrieval_embedder: DeterministicHashEmbedder) -> None:
        self._retrieval_embedder = retrieval_embedder

    def build(
        self,
        *,
        settings: RetrievalConfig,
    ) -> RetrievalGateway:
        client = WeaviateClient(
            weaviate_url=settings.settings.weaviate_url,
            embedder=self._retrieval_embedder,
        )
        return RetrievalGateway(client=client)
