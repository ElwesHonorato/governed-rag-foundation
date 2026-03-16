"""Grounded response runtime assembly for the agent-platform engine."""

from __future__ import annotations

from agent_platform.clients.llm.ollama_client import OllamaClient
from agent_platform.clients.retrieval.weaviate_client import (
    WeaviateClient,
)
from agent_platform.grounded_response.service import GroundedResponseService
from agent_platform.startup.startup_assets_factory import StartupAssets


class GroundedResponseFactory:
    """Build retrieval-grounded response collaborators for the engine."""

    def build(self, assets: StartupAssets) -> GroundedResponseService:
        settings = assets.settings
        return GroundedResponseService(
            llm_client=OllamaClient(
                llm_url=settings.llm.llm_url,
                timeout_seconds=settings.llm.llm_timeout_seconds,
            ),
            retrieval_client=WeaviateClient(
                weaviate_url=settings.retrieval.weaviate_url,
                embedder=assets.retrieval.embedder,
            ),
            model=settings.llm.llm_model,
            retrieval_limit=settings.retrieval.retrieval_limit,
        )
