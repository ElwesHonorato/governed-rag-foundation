"""HTTP application boundary for the agent API."""

from __future__ import annotations

from agent_api.adapters.http.router import AgentApiRouter
from pipeline_common.http import StartResponse, WsgiEnv, WsgiRequestNormalizer


class AgentApiApplication:
    """Small stdlib WSGI app for the agent API."""

    def __init__(
        self,
        *,
        request_normalizer: WsgiRequestNormalizer,
        router: AgentApiRouter,
    ) -> None:
        self._request_normalizer = request_normalizer
        self._router = router

    def __call__(self, env: WsgiEnv, start_response: StartResponse) -> list[bytes]:
        request = self._request_normalizer.normalize(env)
        response = self._router.dispatch(request)
        return response.to_wsgi(start_response)
