"""Explicit route dispatch for the agent API."""

from __future__ import annotations

from agent_api.adapters.http.handlers import AgentApiHandlers
from agent_api.adapters.http.request_normalization import NormalizedRequest
from agent_api.adapters.http.responses import JsonResponse


class AgentApiRouter:
    """Explicit route dispatch for the agent API."""

    def __init__(self, *, handlers: AgentApiHandlers) -> None:
        self._handlers = handlers

    def dispatch(self, request: NormalizedRequest) -> JsonResponse:
        match (request.method, request.path):
            case ("GET", "/"):
                return self._handlers.get_health()
            case ("POST", "/grounded-response/query"):
                return self._handlers.query_grounded_response(request.body)
            case _:
                raise FileNotFoundError(request.path)
