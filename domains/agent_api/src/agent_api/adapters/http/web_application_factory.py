"""Composition root for the agent API WSGI application."""

from __future__ import annotations

from agent_api.adapters.http.application import AgentApiApplication
from agent_api.adapters.http.request_normalization import WsgiRequestNormalizer
from agent_api.adapters.http.router import AgentApiRouter


class WebApplicationFactory:
    """Build the agent API WSGI application from runtime dependencies."""

    def __init__(
        self,
        *,
        request_normalizer: WsgiRequestNormalizer,
        router: AgentApiRouter,
    ) -> None:
        self._request_normalizer = request_normalizer
        self._router = router

    def create(self) -> AgentApiApplication:
        return AgentApiApplication(
            request_normalizer=self._request_normalizer,
            router=self._router,
        )
