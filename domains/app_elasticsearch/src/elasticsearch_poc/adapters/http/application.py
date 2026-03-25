"""HTTP application boundary for the Elasticsearch API."""

from __future__ import annotations

from elasticsearch_poc.adapters.http.http_types import StartResponse, WsgiEnv
from elasticsearch_poc.adapters.http.request_normalization import WsgiRequestNormalizer
from elasticsearch_poc.adapters.http.router import ElasticsearchApiRouter


class ElasticsearchApiApplication:
    """Small stdlib WSGI app for the Elasticsearch API."""

    def __init__(
        self,
        *,
        request_normalizer: WsgiRequestNormalizer,
        router: ElasticsearchApiRouter,
    ) -> None:
        self._request_normalizer = request_normalizer
        self._router = router

    def __call__(self, env: WsgiEnv, start_response: StartResponse) -> list[bytes]:
        request = self._request_normalizer.normalize(env)
        response = self._router.dispatch(request)
        return response.to_wsgi(start_response)
