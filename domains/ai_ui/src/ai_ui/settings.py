"""ai_ui settings and environment-backed provider."""

from __future__ import annotations

from dataclasses import dataclass

from agent_settings.settings import required_env, required_int_env


@dataclass(frozen=True)
class FrontendAgentApiSettings:
    """Frontend-facing settings for calling the agent API service."""

    agent_api_url: str
    agent_api_timeout_seconds: int

    @classmethod
    def from_env(cls) -> "FrontendAgentApiSettings":
        return cls(
            agent_api_url=required_env("AGENT_API_URL"),
            agent_api_timeout_seconds=required_int_env("AGENT_API_TIMEOUT_SECONDS"),
        )
