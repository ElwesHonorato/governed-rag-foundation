"""ai_ui settings and environment-backed provider."""

from __future__ import annotations

import os
from dataclasses import dataclass

from agent_settings.settings import SettingsProvider


@dataclass(frozen=True)
class FrontendAgentApiSettings:
    """Frontend-facing settings for calling the agent API service."""

    agent_api_url: str
    agent_api_timeout_seconds: int

    def dependencies_payload(self) -> dict[str, str]:
        return {"agent_api": self.agent_api_url}


class EnvironmentSettingsProvider(SettingsProvider[FrontendAgentApiSettings]):
    """Load ai_ui settings from environment variables."""

    def load(self) -> FrontendAgentApiSettings:
        return FrontendAgentApiSettings(
            agent_api_url=_required_env("AGENT_API_URL"),
            agent_api_timeout_seconds=_required_int_env("AGENT_API_TIMEOUT_SECONDS"),
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
