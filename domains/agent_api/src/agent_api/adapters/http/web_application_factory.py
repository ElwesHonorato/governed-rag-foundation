"""Composition root for the agent API WSGI application."""

from __future__ import annotations

from agent_api.adapters.http.application import AgentApiApplication
from agent_api.adapters.http.handlers import AgentApiHandlers
from agent_api.adapters.http.request_normalization import WsgiRequestNormalizer
from agent_api.adapters.http.router import AgentApiRouter
from agent_api.engine_factory import Engine
from agent_settings.settings import AgentApiSettings


class WebApplicationFactory:
    """Build the agent API WSGI application from runtime dependencies."""

    def __init__(
        self,
        *,
        settings: AgentApiSettings,
        agent_app: Engine,
    ) -> None:
        self._settings = settings
        self._agent_app = agent_app

    def create(self) -> AgentApiApplication:
        handlers = AgentApiHandlers(settings=self._settings, agent_app=self._agent_app)
        request_normalizer = WsgiRequestNormalizer()
        router = AgentApiRouter(handlers=handlers)
        return AgentApiApplication(
            request_normalizer=request_normalizer,
            router=router,
        )
