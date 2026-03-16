"""Startup-time asset assembly for the agent-platform runtime."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ai_infra.registry.capability_registry import CapabilityRegistry
from agent_platform.application.skill_registry import SkillRegistry
from agent_platform.registry.local_capability_catalog import (
    load_capability_catalog,
    load_skill_registry,
)
from agent_platform.gateways.state.local_checkpoint_store import LocalCheckpointStore
from agent_platform.gateways.state.local_run_store import LocalRunStore
from agent_platform.gateways.state.local_session_store import LocalSessionStore
from agent_platform.startup.bootstrap import PreparedRuntimeArtifacts, RuntimeBootstrapper
from agent_platform.startup.contracts import AgentPlatformConfig
from agent_platform.startup.provider import SettingsProvider, SettingsRequest
from agent_platform.startup.retrieval_composition import (
    RetrievalComposition,
    RetrievalCompositionFactory,
)


@dataclass(frozen=True)
class LocalStateStores:
    """File-backed stores rooted in the runtime state directory."""

    session_store: LocalSessionStore
    run_store: LocalRunStore
    checkpoint_store: LocalCheckpointStore


@dataclass(frozen=True)
class StartupAssets:
    """Startup assets needed by higher-level runtime builders."""

    settings: AgentPlatformConfig
    retrieval: RetrievalComposition
    prepared_artifacts: PreparedRuntimeArtifacts
    capability_registry: CapabilityRegistry
    skill_registry: SkillRegistry
    stores: LocalStateStores


class StartupAssetsFactory:
    """Build startup assets shared by execution and RAG assembly."""

    def __init__(
        self,
        *,
        bootstrapper: RuntimeBootstrapper,
        retrieval_composition_factory: RetrievalCompositionFactory,
    ) -> None:
        self._bootstrapper = bootstrapper
        self._retrieval_composition_factory = retrieval_composition_factory

    def build(self) -> StartupAssets:
        settings = self._load_settings()
        retrieval = self._retrieval_composition_factory.build(settings.retrieval)
        return StartupAssets(
            settings=settings,
            retrieval=retrieval,
            prepared_artifacts=self._bootstrapper.prepare(settings, retrieval),
            capability_registry=CapabilityRegistry(load_capability_catalog()),
            skill_registry=load_skill_registry(),
            stores=self._build_local_state_stores(settings),
        )

    def _load_settings(self) -> AgentPlatformConfig:
        settings = SettingsProvider(
            SettingsRequest(agent_platform=True)
        ).bundle.agent_platform
        if settings is None:
            raise ValueError("Agent platform settings were not requested")
        return settings

    def _build_local_state_stores(
        self, settings: AgentPlatformConfig
    ) -> LocalStateStores:
        state_dir = Path(settings.paths.state_dir)
        return LocalStateStores(
            session_store=LocalSessionStore(str(state_dir / "sessions")),
            run_store=LocalRunStore(str(state_dir / "runs")),
            checkpoint_store=LocalCheckpointStore(str(state_dir / "checkpoints")),
        )
