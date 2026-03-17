"""Composition root for the agent API grounded-response runtime."""

from __future__ import annotations

from dataclasses import dataclass

from ai_infra.retrieval.deterministic_hash_embedder import (
    DeterministicHashEmbedder,
)
from agent_platform.grounded_response.contracts import GroundedResponse
from agent_platform.grounded_response.service import GroundedResponseService
from agent_platform.startup.llm_gateway_factory import LLMGatewayFactory
from agent_platform.startup.embedder_factory import EmbedderFactory
from agent_platform.startup.retrieval_gateway_factory import RetrievalGatewayFactory
from agent_api.startup.runtime_settings import AgentAPIEngineConfig


@dataclass(frozen=True)
class AgentAPIFactory:
    """Narrow grounded-response boundary exposed to the HTTP layer."""

    grounded_response_service: GroundedResponseService

    def query_grounded_response(self, body: dict[str, object]) -> GroundedResponse:
        return self.grounded_response_service.respond(body)


@dataclass(frozen=True)
class AgentApiGatewayFactories:
    """Gateway factories used by API runtime assembly."""

    llm: LLMGatewayFactory
    retrieval: RetrievalGatewayFactory


class AgentAPIEngineFactory:
    """Build the agent API grounded-response runtime graph."""

    def __init__(
        self,
        *,
        retrieval_embedder_factory: EmbedderFactory,
        gateway_factories: AgentApiGatewayFactories,
        settings: AgentAPIEngineConfig,
    ) -> None:
        self._retrieval_embedder_factory = retrieval_embedder_factory
        self._gateway_factories = gateway_factories
        self._settings = settings

    def build(self) -> AgentAPIFactory:
        retrieval_embedder: DeterministicHashEmbedder = (
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
        return AgentAPIFactory(grounded_response_service=grounded_response_service)
