"""Agent API settings and environment-backed provider."""

from __future__ import annotations

from dataclasses import asdict, dataclass

from agent_settings.settings import SettingsProvider, required_env, required_int_env


@dataclass(frozen=True)
class AgentApiSettings:
    """Settings for exposing the agent API service."""

    host: str
    port: int

    @property
    def to_dict(self) -> dict[str, object]:
        return asdict(self)


class AgentApiSettingsProvider(SettingsProvider[AgentApiSettings]):
    """Load agent API settings from environment variables."""

    def load(self) -> AgentApiSettings:
        return AgentApiSettings(
            host=required_env("AGENT_API_HOST"),
            port=required_int_env("AGENT_API_PORT"),
        )
