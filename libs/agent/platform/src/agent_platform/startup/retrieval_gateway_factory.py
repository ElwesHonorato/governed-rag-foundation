"""Factory for retrieval gateway construction."""

from __future__ import annotations

from agent_platform.clients.retrieval.weaviate_client import WeaviateClient
from agent_platform.gateways.retrieval.retrieval_gateway import RetrievalGateway
from agent_platform.startup.contracts import RetrievalConfig


class RetrievalGatewayFactory:
    """Build retrieval gateways for local agent-platform runtime."""

    def __init__(
        self,
        *,
        client: WeaviateClient,
        config: RetrievalConfig,
    ) -> None:
        self._client = client
        self._config = config

    def build(self) -> RetrievalGateway:
        return RetrievalGateway(
            client=self._client,
            configs=self._config,
        )
