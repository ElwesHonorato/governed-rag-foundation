"""Endpoint handlers for the AI backend."""

from __future__ import annotations

from http import HTTPStatus

from ai_backend.responses import JsonResponse
from ai_backend.service_factory import AgentPlatformRuntime
from runtime.provider import BackendAIBackendSettings


class AiBackendHandlers:
    """Endpoint orchestration for AI backend routes."""

    def __init__(self, *, settings: BackendAIBackendSettings, agent_app: AgentPlatformRuntime) -> None:
        self._settings = settings
        self._agent_app = agent_app

    def get_health(self) -> JsonResponse:
        return JsonResponse(
            payload={"service": "ai-backend", "status": "ok", "settings": self._settings.to_dict},
            status=HTTPStatus.OK,
        )

    def list_capabilities(self) -> JsonResponse:
        return JsonResponse(
            payload=[item.to_dict() for item in self._agent_app.list_capabilities()],
            status=HTTPStatus.OK,
        )

    def list_skills(self) -> JsonResponse:
        return JsonResponse(
            payload=self._agent_app.list_skills(),
            status=HTTPStatus.OK,
        )

    def create_run(self, body: dict[str, object]) -> JsonResponse:
        objective = str(body.get("objective", "")).strip()
        skill_name = str(body.get("skill_name", "analyze_repository")).strip()
        run = self._agent_app.run_objective(objective=objective, skill_name=skill_name)
        return JsonResponse(payload=run.to_dict(), status=HTTPStatus.CREATED)

    def create_evaluation(self, body: dict[str, object]) -> JsonResponse:
        run_id = str(body.get("run_id", "")).strip()
        evaluation = self._agent_app.evaluate_run(run_id)
        return JsonResponse(payload=evaluation.to_dict(), status=HTTPStatus.CREATED)

    def query_rag(self, body: dict[str, object]) -> JsonResponse:
        response = self._agent_app.query_rag(body)
        return JsonResponse(payload=response.to_dict(), status=HTTPStatus.OK)
