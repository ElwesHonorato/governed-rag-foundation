"""Factory for LLM gateway construction."""

from __future__ import annotations

from agent_platform.clients.llm.ollama_client import OllamaClient
from agent_platform.gateways.llm.llm_gateway import LLMGateway


class LLMGatewayFactory:
    """Build LLM gateways for local agent-platform runtime."""

    def __init__(self, *, client: OllamaClient) -> None:
        self._client = client

    def build(self) -> LLMGateway:
        return LLMGateway(client=self._client)
