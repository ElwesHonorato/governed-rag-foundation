"""Runtime settings provider for application domains.

Layer:
- Infrastructure configuration adapter used by composition roots.

Role:
- Convert environment variables into typed settings objects requested by a
  startup path.

Design intent:
- Keep env parsing logic out of application wiring and request handlers.
- Allow each startup path to request only the settings it needs.
"""

from __future__ import annotations

import os
from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class FrontendAgentApiSettings:
    """Frontend-facing settings for calling the agent API service."""

    agent_api_url: str
    agent_api_timeout_seconds: int

    def dependencies_payload(self) -> dict[str, str]:
        return {"agent_api": self.agent_api_url}


@dataclass(frozen=True)
class AgentApiSettings:
    """Settings for exposing the agent API service."""

    host: str
    port: int

    @property
    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class SettingsRequest:
    """Requested runtime settings to load from environment."""

    frontend_agent_api: bool = False
    agent_api: bool = False


@dataclass(frozen=True)
class SettingsBundle:
    """Bundle of loaded settings based on a requested scope."""

    frontend_agent_api: FrontendAgentApiSettings | None = None
    agent_api: AgentApiSettings | None = None


def load_frontend_agent_api_settings_from_env() -> FrontendAgentApiSettings:
    """Load frontend settings for calling the agent API service."""
    return FrontendAgentApiSettings(
        agent_api_url=_required_env("AGENT_API_URL"),
        agent_api_timeout_seconds=_required_int_env("AGENT_API_TIMEOUT_SECONDS"),
    )


def load_agent_api_settings_from_env() -> AgentApiSettings:
    """Load settings for exposing the agent API service."""
    return AgentApiSettings(
        host=_required_env("AGENT_API_HOST"),
        port=_required_int_env("AGENT_API_PORT"),
    )


class SettingsProvider:
    """Load requested runtime settings from environment variables."""

    def __init__(self, request: SettingsRequest) -> None:
        self._request = request

    @property
    def frontend_agent_api(self) -> FrontendAgentApiSettings | None:
        if not self._request.frontend_agent_api:
            return None
        return load_frontend_agent_api_settings_from_env()

    @property
    def agent_api(self) -> AgentApiSettings | None:
        if not self._request.agent_api:
            return None
        return load_agent_api_settings_from_env()

    @property
    def bundle(self) -> SettingsBundle:
        return SettingsBundle(
            frontend_agent_api=self.frontend_agent_api,
            agent_api=self.agent_api,
        )


def _required_env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise ValueError(f"{name} is not configured")
    return value.strip()


def _required_int_env(name: str) -> int:
    raw_value = _required_env(name)
    try:
        return int(raw_value)
    except ValueError as exc:
        raise ValueError(f"{name} must be an integer") from exc
