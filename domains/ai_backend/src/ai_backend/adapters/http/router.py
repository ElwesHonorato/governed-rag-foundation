"""Explicit route dispatch for the AI backend."""

from __future__ import annotations

from ai_backend.adapters.http.handlers import AiBackendHandlers
from ai_backend.adapters.http.request_normalization import NormalizedRequest
from ai_backend.adapters.http.responses import JsonResponse


class AiBackendRouter:
    """Explicit route dispatch for the AI backend."""

    def __init__(self, *, handlers: AiBackendHandlers) -> None:
        self._handlers = handlers

    def dispatch(self, request: NormalizedRequest) -> JsonResponse:
        match (request.method, request.path):
            case ("GET", "/"):
                return self._handlers.get_health()
            case ("GET", "/capabilities"):
                return self._handlers.list_capabilities()
            case ("GET", "/skills"):
                return self._handlers.list_skills()
            case ("POST", "/runs"):
                return self._handlers.create_run(request.body)
            case ("POST", "/evaluations"):
                return self._handlers.create_evaluation(request.body)
            case ("POST", "/rag/query"):
                return self._handlers.query_rag(request.body)
            case _:
                raise FileNotFoundError(request.path)
