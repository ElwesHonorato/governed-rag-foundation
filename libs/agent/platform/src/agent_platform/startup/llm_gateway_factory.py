"""Factory for LLM gateway construction."""

from __future__ import annotations

from agent_platform.clients.llm.ollama_client import OllamaClient
from agent_platform.gateways.llm.llm_gateway import LLMGateway
from agent_platform.startup.contracts import LLMParams


class LLMGatewayFactory:
    """Build LLM gateways for local agent-platform runtime."""

    def __init__(self, *, client: OllamaClient, params: LLMParams) -> None:
        self._client = client
        self._params = params

    def build(self) -> LLMGateway:
        return LLMGateway(
            client=self._client,
            params=self._params,
        )
