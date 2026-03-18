"""Factory for local filesystem gateway construction."""

from __future__ import annotations

from agent_platform.gateways.filesystem.local_filesystem_gateway import (
    LocalFilesystemGateway,
)
from agent_platform.startup.contracts import AgentPlatformConfig


class FilesystemGatewayFactory:
    """Build filesystem gateways for local agent-platform runtime."""

    def build(self, settings: AgentPlatformConfig) -> LocalFilesystemGateway:
        return LocalFilesystemGateway(str(settings.paths.workspace_root))
