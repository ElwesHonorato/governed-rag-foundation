"""Agent API settings and environment-backed provider."""

from __future__ import annotations

import os
from dataclasses import asdict, dataclass

from agent_settings.settings import SettingsProvider


@dataclass(frozen=True)
class AgentApiSettings:
    """Settings for exposing the agent API service."""

    host: str
    port: int

    @property
    def to_dict(self) -> dict[str, object]:
        return asdict(self)


class EnvironmentSettingsProvider(SettingsProvider[AgentApiSettings]):
    """Load agent API settings from environment variables."""

    def load(self) -> AgentApiSettings:
        return AgentApiSettings(
            host=_required_env("AGENT_API_HOST"),
            port=_required_int_env("AGENT_API_PORT"),
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
