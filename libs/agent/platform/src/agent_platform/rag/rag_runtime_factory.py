"""RAG runtime assembly for the agent-platform engine."""

from __future__ import annotations

from agent_platform.gateways.retrieval.weaviate_retrieval_client import (
    WeaviateRetrievalClient,
)
from agent_platform.llm.ollama_client import OllamaClient
from agent_platform.rag.service import RagService
from agent_platform.startup.startup_assets_factory import StartupAssets


class RagRuntimeFactory:
    """Build retrieval-grounded response collaborators for the engine."""

    def build(self, assets: StartupAssets) -> RagService:
        settings = assets.settings
        return RagService(
            llm_client=OllamaClient(
                llm_url=settings.llm.llm_url,
                timeout_seconds=settings.llm.llm_timeout_seconds,
            ),
            retrieval_client=WeaviateRetrievalClient(
                weaviate_url=settings.retrieval.weaviate_url,
                embedder=assets.retrieval.embedder,
            ),
            model=settings.llm.llm_model,
            retrieval_limit=settings.retrieval.retrieval_limit,
        )
