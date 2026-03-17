"""Endpoint handlers for the agent API."""

from __future__ import annotations

from dataclasses import asdict
from http import HTTPStatus

from agent_api.adapters.http.responses import JsonResponse
from agent_api.startup.engine_factory import AgentAPIFactory
from agent_settings.settings import AgentApiSettings


class AgentApiHandlers:
    """Endpoint orchestration for agent API routes."""

    def __init__(self, *, settings: AgentApiSettings, agent_app: AgentAPIFactory) -> None:
        self._settings = settings
        self._agent_app = agent_app

    def get_health(self) -> JsonResponse:
        return JsonResponse(
            payload={"service": "agent-api", "status": "ok", "settings": asdict(self._settings)},
            status=HTTPStatus.OK,
        )

    def query_grounded_response(self, body: dict[str, object]) -> JsonResponse:
        response = self._agent_app.query_grounded_response(body)
        return JsonResponse(payload=response.to_dict(), status=HTTPStatus.OK)
