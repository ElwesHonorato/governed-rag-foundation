"""Composition root for the agent API grounded-response runtime."""

from __future__ import annotations

from dataclasses import dataclass

from agent_platform.grounded_response.contracts import GroundedResponse
from agent_platform.grounded_response.service import GroundedResponseService
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
