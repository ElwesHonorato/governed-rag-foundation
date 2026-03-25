"""HTTP handlers for grounded-response API endpoints."""

from __future__ import annotations

from dataclasses import asdict
from http import HTTPStatus

from agent_platform.grounded_response.service import GroundedResponseService
from agent_settings.settings import AgentApiSettings
from pipeline_common.http import JsonResponse


class GroundedResponseHttpHandler:
    """Build JSON responses for grounded-response HTTP endpoints.

    This adapter translates HTTP-layer inputs into grounded-response service
    calls and formats the returned values as ``JsonResponse`` payloads.
    """

    def __init__(
        self,
        *,
        settings: AgentApiSettings,
        grounded_response_service: GroundedResponseService,
    ) -> None:
        """Initialize the HTTP handler.

        Args:
            settings: Service-level API settings used by the health endpoint.
            grounded_response_service: Application service that executes
                grounded-response queries.
        """
        self._settings = settings
        self._grounded_response_service = grounded_response_service

    def get_health(self) -> JsonResponse:
        """Return the service health response.

        Returns:
            A JSON response describing service status and loaded API settings.
        """
        return JsonResponse(
            payload={"service": "agent-api", "status": "ok", "settings": asdict(self._settings)},
            status=HTTPStatus.OK,
        )

    def query_grounded_response(self, body: dict[str, object]) -> JsonResponse:
        """Execute a grounded-response query and return the HTTP payload.

        Args:
            body: Normalized request body containing grounded-response input.

        Returns:
            A JSON response containing the grounded-response result payload.
        """
        response = self._grounded_response_service.respond(body)
        return JsonResponse(payload=response.to_dict(), status=HTTPStatus.OK)
