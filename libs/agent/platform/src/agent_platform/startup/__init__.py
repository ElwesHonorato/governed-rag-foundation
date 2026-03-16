"""Startup wiring for agent-platform."""

from agent_platform.startup.contracts import AgentPlatformConfig
from agent_platform.startup.runtime_settings import (
    AgentPlatformSettingsProvider,
)

__all__ = [
    "AgentPlatformConfig",
    "AgentPlatformSettingsProvider",
]
