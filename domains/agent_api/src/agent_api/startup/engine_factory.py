"""Composition root for the agent API grounded-response runtime."""

from __future__ import annotations

from dataclasses import dataclass

from ai_infra.retrieval.deterministic_retrieval_embedder import (
    DeterministicRetrievalEmbedder,
)
from agent_platform.grounded_response.contracts import GroundedResponse
from agent_platform.grounded_response.service import GroundedResponseService
from agent_platform.startup.contracts import AgentPlatformConfig
from agent_platform.startup.llm_gateway_factory import LLMGatewayFactory
from agent_platform.startup.retrieval_embedder_factory import (
    RetrievalEmbedderFactory,
)
from agent_platform.startup.retrieval_gateway_factory import RetrievalGatewayFactory


@dataclass(frozen=True)
class Engine:
    """Narrow grounded-response boundary exposed to the HTTP layer."""

    grounded_response_service: GroundedResponseService

    def query_grounded_response(self, body: dict[str, object]) -> GroundedResponse:
        return self.grounded_response_service.respond(body)


@dataclass(frozen=True)
class AgentApiGatewayFactories:
    """Gateway factories used by API runtime assembly."""

    llm: LLMGatewayFactory
    retrieval: RetrievalGatewayFactory


class EngineFactory:
    """Build the agent API grounded-response runtime graph."""

    def __init__(
        self,
        *,
        retrieval_embedder_factory: RetrievalEmbedderFactory,
        gateway_factories: AgentApiGatewayFactories,
        settings: AgentPlatformConfig,
    ) -> None:
        self._retrieval_embedder_factory = retrieval_embedder_factory
        self._gateway_factories = gateway_factories
        self._settings = settings

    def build(self) -> Engine:
        retrieval_embedder: DeterministicRetrievalEmbedder = (
            self._retrieval_embedder_factory.build(
                self._settings.retrieval.embedding_dim
            )
        )
        llm_gateway = self._gateway_factories.llm.build(self._settings)
        retrieval_gateway = self._gateway_factories.retrieval.build(
            settings=self._settings,
            retrieval_embedder=retrieval_embedder,
        )
        grounded_response_service = GroundedResponseService(
            llm_gateway=llm_gateway,
            retrieval_gateway=retrieval_gateway,
            model=self._settings.llm.llm_model,
            retrieval_limit=self._settings.retrieval.retrieval_limit,
        )
        return Engine(grounded_response_service=grounded_response_service)
