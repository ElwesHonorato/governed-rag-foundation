"""HTTP application boundary for the AI backend."""

from __future__ import annotations

from ai_backend.http_types import StartResponse, WsgiEnv
from ai_backend.request_normalization import WsgiRequestNormalizer
from ai_backend.router import AiBackendRouter


class AiBackendApplication:
    """Small stdlib WSGI app for the AI backend."""

    def __init__(
        self,
        *,
        request_normalizer: WsgiRequestNormalizer,
        router: AiBackendRouter,
    ) -> None:
        self._request_normalizer = request_normalizer
        self._router = router

    def __call__(self, env: WsgiEnv, start_response: StartResponse) -> list[bytes]:
        request = self._request_normalizer.normalize(env)
        response = self._router.dispatch(request)
        return response.to_wsgi(start_response)
