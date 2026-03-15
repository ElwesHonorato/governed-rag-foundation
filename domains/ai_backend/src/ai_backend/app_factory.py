"""Composition root for the AI backend WSGI application."""

from __future__ import annotations

from agent_platform.startup.service_factory import AgentPlatformServiceFactory
from ai_backend.application import AiBackendApplication
from ai_backend.handlers import AiBackendHandlers
from ai_backend.request_normalization import WsgiRequestNormalizer
from ai_backend.router import AiBackendRouter
from runtime.provider import BackendAIBackendSettings


class AiBackendApplicationFactory:
    """Build the AI backend WSGI application from runtime dependencies."""

    def __init__(self, *, settings: BackendAIBackendSettings) -> None:
        self._settings = settings

    def create(self) -> AiBackendApplication:
        agent_app = AgentPlatformServiceFactory().build()
        handlers = AiBackendHandlers(settings=self._settings, agent_app=agent_app)
        request_normalizer = WsgiRequestNormalizer()
        router = AiBackendRouter(handlers=handlers)
        return AiBackendApplication(
            request_normalizer=request_normalizer,
            router=router,
        )
