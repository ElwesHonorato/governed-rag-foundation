"""Composition root for the AI backend WSGI application."""

from __future__ import annotations

from ai_backend.adapters.http.application import AiBackendApplication
from ai_backend.adapters.http.handlers import AiBackendHandlers
from ai_backend.adapters.http.request_normalization import WsgiRequestNormalizer
from ai_backend.adapters.http.router import AiBackendRouter
from ai_backend.engine_factory import Engine
from runtime.provider import BackendAIBackendSettings


class WebApplicationFactory:
    """Build the AI backend WSGI application from runtime dependencies."""

    def __init__(
        self,
        *,
        settings: BackendAIBackendSettings,
        agent_app: Engine,
    ) -> None:
        self._settings = settings
        self._agent_app = agent_app

    def create(self) -> AiBackendApplication:
        handlers = AiBackendHandlers(settings=self._settings, agent_app=self._agent_app)
        request_normalizer = WsgiRequestNormalizer()
        router = AiBackendRouter(handlers=handlers)
        return AiBackendApplication(
            request_normalizer=request_normalizer,
            router=router,
        )
