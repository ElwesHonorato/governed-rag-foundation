"""Grounded response runtime assembly for the agent-platform engine."""

from __future__ import annotations

from agent_platform.agent_runtime.execution_runtime_factory import EngineGateways
from agent_platform.grounded_response.service import GroundedResponseService
from agent_platform.startup.startup_assets_factory import StartupAssets


class GroundedResponseFactory:
    """Build retrieval-grounded response collaborators for the engine."""

    def build(
        self,
        assets: StartupAssets,
        gateways: EngineGateways,
    ) -> GroundedResponseService:
        settings = assets.settings
        return GroundedResponseService(
            llm_gateway=gateways.llm_gateway,
            retrieval_gateway=gateways.retrieval_gateway,
            model=settings.llm.llm_model,
            retrieval_limit=settings.retrieval.retrieval_limit,
        )
