"""HTTP application boundary for the AI backend."""

from __future__ import annotations

from agent_platform.startup.service_factory import AgentPlatformApp
from ai_backend.handlers import AiBackendHandlers
from ai_backend.http_types import StartResponse, WsgiEnv
from ai_backend.request_normalization import WsgiRequestNormalizer
from ai_backend.router import AiBackendRouter
from runtime.provider import BackendAIBackendSettings


class AiBackendApplication:
    """Small stdlib WSGI app for the AI backend."""

    def __init__(self, *, settings: BackendAIBackendSettings, agent_app: AgentPlatformApp) -> None:
        handlers = AiBackendHandlers(settings=settings, agent_app=agent_app)
        self._request_normalizer = WsgiRequestNormalizer()
        self._router = AiBackendRouter(handlers=handlers)

    def __call__(self, env: WsgiEnv, start_response: StartResponse) -> list[bytes]:
        request = self._request_normalizer.normalize(env)
        response = self._router.dispatch(request)
        return response.to_wsgi(start_response)
