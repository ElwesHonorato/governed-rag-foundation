"""Startup helper for local file-backed state stores."""

from __future__ import annotations

from dataclasses import dataclass

from agent_platform.gateways.state.local_checkpoint_store import LocalCheckpointStore
from agent_platform.gateways.state.local_run_store import LocalRunStore
from agent_platform.gateways.state.local_session_store import LocalSessionStore
from agent_platform.startup.contracts import AgentPlatformConfig


@dataclass(frozen=True)
class LocalStateStores:
    """File-backed stores rooted in the runtime state directory."""

    session_store: LocalSessionStore
    run_store: LocalRunStore
    checkpoint_store: LocalCheckpointStore


class LocalStateStoresFactory:
    """Build file-backed state stores for the local runtime."""

    def build(self, settings: AgentPlatformConfig) -> LocalStateStores:
        return LocalStateStores(
            session_store=LocalSessionStore(str(settings.paths.sessions_dir)),
            run_store=LocalRunStore(str(settings.paths.runs_dir)),
            checkpoint_store=LocalCheckpointStore(str(settings.paths.checkpoints_dir)),
        )
