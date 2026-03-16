"""ai_ui settings and environment-backed provider."""

from __future__ import annotations

from dataclasses import dataclass

from agent_settings.settings import SettingsProvider, required_env, required_int_env


@dataclass(frozen=True)
class FrontendAgentApiSettings:
    """Frontend-facing settings for calling the agent API service."""

    agent_api_url: str
    agent_api_timeout_seconds: int


class AiUiSettingsProvider(SettingsProvider[FrontendAgentApiSettings]):
    """Load ai_ui settings from environment variables."""

    def load(self) -> FrontendAgentApiSettings:
        return FrontendAgentApiSettings(
            agent_api_url=required_env("AGENT_API_URL"),
            agent_api_timeout_seconds=required_int_env("AGENT_API_TIMEOUT_SECONDS"),
        )
