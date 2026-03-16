"""Environment-to-settings loaders for runtime configuration."""

from __future__ import annotations

import os

from agent_settings.settings.models import AgentApiSettings, FrontendAgentApiSettings


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
