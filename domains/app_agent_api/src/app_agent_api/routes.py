"""WSGI route handling for the agent-platform HTTP API."""

from __future__ import annotations

import json
from http import HTTPStatus
from typing import Callable

from startup.service_factory import AgentPlatformApp
from app_agent_api.config import Settings


StartResponse = Callable[[str, list[tuple[str, str]]], None]


class AgentApiApplication:
    """Small stdlib WSGI app for the agent-platform MVP."""

    def __init__(self, *, settings: Settings, agent_app: AgentPlatformApp) -> None:
        self._settings = settings
        self._agent_app = agent_app

    def __call__(self, environ: dict[str, object], start_response: StartResponse):
        method = str(environ.get("REQUEST_METHOD", "GET")).upper()
        path = str(environ.get("PATH_INFO", "/"))
        body = self._read_json_body(environ)
        try:
            payload, status = self._dispatch(method=method, path=path, body=body)
        except FileNotFoundError:
            payload, status = {"error": "not found"}, HTTPStatus.NOT_FOUND
        except ValueError as exc:
            payload, status = {"error": str(exc)}, HTTPStatus.BAD_REQUEST
        response_bytes = json.dumps(payload, indent=2).encode("utf-8")
        start_response(
            f"{status.value} {status.phrase}",
            [
                ("Content-Type", "application/json"),
                ("Content-Length", str(len(response_bytes))),
            ],
        )
        return [response_bytes]

    def _dispatch(self, *, method: str, path: str, body: dict[str, object]) -> tuple[dict[str, object] | list[object], HTTPStatus]:
        if method == "GET" and path == "/":
            return {"service": "agent-api", "status": "ok", "settings": self._settings.payload()}, HTTPStatus.OK
        if method == "GET" and path == "/capabilities":
            return [item.to_dict() for item in self._agent_app.capability_registry.list_capabilities()], HTTPStatus.OK
        if method == "GET" and path == "/skills":
            return sorted(self._agent_app.skill_registry.keys()), HTTPStatus.OK
        if method == "GET" and path.startswith("/sessions/"):
            session_id = path.split("/", 2)[2]
            return self._agent_app.session_store.load_session(session_id).to_dict(), HTTPStatus.OK
        if method == "GET" and path.startswith("/runs/"):
            run_id = path.split("/", 2)[2]
            return self._agent_app.run_store.load_run(run_id).to_dict(), HTTPStatus.OK
        if method == "POST" and path == "/runs":
            objective = str(body.get("objective", "")).strip()
            skill_name = str(body.get("skill_name", "analyze_repository")).strip()
            if not objective:
                raise ValueError("objective is required")
            if skill_name not in self._agent_app.skill_registry:
                raise ValueError(f"unknown skill: {skill_name}")
            run = self._agent_app.run_objective(objective=objective, skill_name=skill_name)
            return run.to_dict(), HTTPStatus.CREATED
        if method == "POST" and path == "/evaluations":
            run_id = str(body.get("run_id", "")).strip()
            if not run_id:
                raise ValueError("run_id is required")
            run = self._agent_app.run_store.load_run(run_id)
            evaluation = self._agent_app.evaluation_runner.evaluate(run)
            return evaluation.to_dict(), HTTPStatus.CREATED
        raise FileNotFoundError(path)

    @staticmethod
    def _read_json_body(environ: dict[str, object]) -> dict[str, object]:
        try:
            length = int(str(environ.get("CONTENT_LENGTH") or "0"))
        except ValueError:
            length = 0
        if length <= 0:
            return {}
        raw = environ["wsgi.input"].read(length)
        if not raw:
            return {}
        return json.loads(raw.decode("utf-8"))
