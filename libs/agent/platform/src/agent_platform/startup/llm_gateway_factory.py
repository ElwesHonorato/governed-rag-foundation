"""Factory for LLM gateway construction."""

from __future__ import annotations

from agent_platform.clients.llm.ollama_client import OllamaClient
from agent_platform.gateways.llm.llm_gateway import LLMGateway
from agent_platform.startup.contracts import AgentPlatformConfig


class LLMGatewayFactory:
    """Build LLM gateways for local agent-platform runtime."""

    def build(self, settings: AgentPlatformConfig) -> LLMGateway:
        client = OllamaClient(
            llm_url=settings.llm.llm_url,
            timeout_seconds=settings.llm.llm_timeout_seconds,
        )
        return LLMGateway(client=client)
