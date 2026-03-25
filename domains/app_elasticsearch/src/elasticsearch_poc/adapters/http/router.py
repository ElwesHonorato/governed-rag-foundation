"""Route incoming HTTP requests to retrieval handlers."""

from __future__ import annotations

from elasticsearch_poc.adapters.http.contracts import RetrieveRequest
from elasticsearch_poc.adapters.http.retrieve_http_handler import RetrieveHttpHandler
from pipeline_common.http import JsonResponse, NormalizedRequest


class ElasticsearchApiRouter:
    """Dispatch normalized HTTP requests to route handlers."""

    def __init__(self, *, handlers: RetrieveHttpHandler) -> None:
        self._handlers = handlers

    def dispatch(self, request: NormalizedRequest) -> JsonResponse:
        match (request.method, request.path):
            case ("GET", "/"):
                return self._handlers.get_health()
            case ("POST", "/retrieve"):
                return self._handlers.retrieve(RetrieveRequest.from_dict(request.body))
            case _:
                return self._handlers.not_found(path=request.path)
