"""Factory for local command gateway construction."""

from __future__ import annotations

from agent_platform.gateways.command.local_command_gateway import LocalCommandGateway
from agent_platform.startup.contracts import AgentPlatformConfig


class CommandGatewayFactory:
    """Build command gateways for local agent-platform runtime."""

    def build(self, settings: AgentPlatformConfig) -> LocalCommandGateway:
        return LocalCommandGateway(str(settings.paths.workspace_root))
