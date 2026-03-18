"""Route incoming HTTP requests to grounded-response handlers."""

from __future__ import annotations

from agent_api.adapters.http.grounded_response_http_handler import (
    GroundedResponseHttpHandler,
)
from agent_api.adapters.http.request_normalization import NormalizedRequest
from agent_api.adapters.http.responses import JsonResponse


class AgentApiRouter:
    """Dispatch normalized HTTP requests to route handlers."""

    def __init__(self, *, handlers: GroundedResponseHttpHandler) -> None:
        """Initialize the router.

        Args:
            handlers: HTTP handler object that serves routed endpoints.
        """
        self._handlers = handlers

    def dispatch(self, request: NormalizedRequest) -> JsonResponse:
        """Dispatch one normalized request to a concrete route handler.

        Args:
            request: Normalized HTTP request to dispatch.

        Returns:
            The JSON response produced by the matched route handler.

        Raises:
            FileNotFoundError: If the request does not match a known route.
        """
        match (request.method, request.path):
            case ("GET", "/"):
                return self._handlers.get_health()
            case ("POST", "/grounded-response/query"):
                return self._handlers.query_grounded_response(request.body)
            case _:
                raise FileNotFoundError(request.path)
