"""Startup-time asset assembly for the agent-platform runtime."""

from __future__ import annotations

from dataclasses import dataclass

from agent_settings.settings import SettingsProvider
from agent_platform.agent_runtime.skill_registry import SkillRegistry
from agent_platform.startup.bootstrap import PreparedRuntimeArtifacts, RuntimeBootstrapper
from agent_platform.startup.local_state_stores_factory import (
    LocalStateStores,
    LocalStateStoresFactory,
)
from agent_platform.startup.packaged_configuration import (
    load_capability_catalog,
    load_skill_registry,
)
from agent_platform.startup.contracts import AgentPlatformConfig
from agent_platform.startup.retrieval_composition import (
    RetrievalComposition,
    RetrievalCompositionFactory,
)
from ai_infra.registry.capability_registry import CapabilityRegistry


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
        local_state_stores_factory: LocalStateStoresFactory,
        settings_provider: SettingsProvider[AgentPlatformConfig],
    ) -> None:
        self._bootstrapper = bootstrapper
        self._retrieval_composition_factory = retrieval_composition_factory
        self._local_state_stores_factory = local_state_stores_factory
        self._settings_provider = settings_provider

    def build(self) -> StartupAssets:
        settings = self._load_settings()
        retrieval = self._retrieval_composition_factory.build(settings.retrieval)
        return StartupAssets(
            settings=settings,
            retrieval=retrieval,
            prepared_artifacts=self._bootstrapper.prepare(settings, retrieval),
            capability_registry=CapabilityRegistry(load_capability_catalog()),
            skill_registry=load_skill_registry(),
            stores=self._local_state_stores_factory.build(settings),
        )

    def _load_settings(self) -> AgentPlatformConfig:
        return self._settings_provider.load()
