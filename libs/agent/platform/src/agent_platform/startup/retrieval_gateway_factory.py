"""Factory for retrieval gateway construction."""

from __future__ import annotations

from ai_infra.retrieval.deterministic_retrieval_embedder import (
    DeterministicRetrievalEmbedder,
)
from agent_platform.clients.retrieval.weaviate_client import WeaviateClient
from agent_platform.gateways.retrieval.retrieval_gateway import RetrievalGateway
from agent_platform.startup.contracts import AgentPlatformConfig


class RetrievalGatewayFactory:
    """Build retrieval gateways for local agent-platform runtime."""

    def build(
        self,
        *,
        settings: AgentPlatformConfig,
        retrieval_embedder: DeterministicRetrievalEmbedder,
    ) -> RetrievalGateway:
        client = WeaviateClient(
            weaviate_url=settings.retrieval.weaviate_url,
            embedder=retrieval_embedder,
        )
        return RetrievalGateway(client=client)
