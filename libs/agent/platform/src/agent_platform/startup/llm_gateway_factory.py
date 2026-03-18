"""Factory for LLM gateway construction."""

from __future__ import annotations

from dataclasses import dataclass

from agent_platform.clients.llm.ollama_client import OllamaClient
from agent_platform.gateways.llm.llm_gateway import LLMGateway


@dataclass(frozen=True)
class ResolvedLLMGateway:
    """Resolved LLM runtime containing the gateway and selected model."""

    gateway: LLMGateway
    model: str


class LLMGatewayFactory:
    """Build LLM gateways for local agent-platform runtime."""

    def __init__(self, *, client: OllamaClient) -> None:
        self._client = client

    def build(self) -> ResolvedLLMGateway:
        gateway = LLMGateway(client=self._client)
        available_models = gateway.list_models()
        if not available_models:
            raise ValueError(
                "No LLM models are available from the configured backend."
            )
        if len(available_models) > 1:
            available_display = ", ".join(sorted(available_models))
            raise ValueError(
                "Multiple LLM models are available from the configured backend. "
                f"Expected exactly one model, found: {available_display}"
            )
        return ResolvedLLMGateway(gateway=gateway, model=available_models[0])
