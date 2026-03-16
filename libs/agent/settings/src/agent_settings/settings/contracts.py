from __future__ import annotations

from dataclasses import dataclass

from agent_settings.settings.models import AgentApiSettings, FrontendAgentApiSettings


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
