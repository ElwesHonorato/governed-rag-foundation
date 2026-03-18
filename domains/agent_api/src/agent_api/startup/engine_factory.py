"""Composition root for the agent API grounded-response runtime."""

from __future__ import annotations

from dataclasses import dataclass

from agent_platform.grounded_response.contracts import GroundedResponse
from agent_platform.grounded_response.service import GroundedResponseService
from agent_platform.startup.contracts import LLMRetrievalConfig
from agent_platform.startup.llm_gateway_factory import LLMGatewayFactory
from agent_platform.startup.retrieval_gateway_factory import RetrievalGatewayFactory


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
        gateway_factories: AgentApiGatewayFactories,
        settings: LLMRetrievalConfig,
    ) -> None:
        self._gateway_factories = gateway_factories
        self._settings = settings

    def build(self) -> AgentAPIFactory:
        resolved_llm_gateway = self._build_llm_gateway()
        retrieval_gateway = self._build_retrieval_gateway()
        grounded_response_service = GroundedResponseService(
            llm_gateway=resolved_llm_gateway.gateway,
            retrieval_gateway=retrieval_gateway,
            model=resolved_llm_gateway.model,
            retrieval_limit=self._settings.retrieval.retrieval_limit,
        )
        return AgentAPIFactory(grounded_response_service=grounded_response_service)

    def _build_llm_gateway(self):
        return self._gateway_factories.llm.build()

    def _build_retrieval_gateway(self):
        return self._gateway_factories.retrieval.build(
            settings=self._settings,
        )
