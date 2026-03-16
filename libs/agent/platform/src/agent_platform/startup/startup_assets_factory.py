"""Startup-time asset assembly for the agent-platform runtime."""

from __future__ import annotations

import json
from dataclasses import dataclass
from importlib.resources import files
from pathlib import Path

from agent_platform.agent_runtime.skill_registry import SkillRegistry
from agent_platform.agent_runtime.skill_registry import SkillDefinition
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
from ai_infra.contracts.capability_descriptor import CapabilityDescriptor
from ai_infra.registry.capability_catalog import CapabilityCatalog
from ai_infra.registry.capability_registry import CapabilityRegistry

CONFIG_PACKAGE = "agent_platform.config"


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


def load_capability_catalog() -> CapabilityCatalog:
    """Load capability metadata from packaged config resources."""

    raw_items = json.loads(files(CONFIG_PACKAGE).joinpath("capabilities.yaml").read_text())
    return CapabilityCatalog([CapabilityDescriptor(**item) for item in raw_items])


def load_skill_registry() -> SkillRegistry:
    """Load skill definitions from packaged config resources."""

    raw_skills = json.loads(files(CONFIG_PACKAGE).joinpath("skills.yaml").read_text())
    return SkillRegistry(
        {
            skill_name: SkillDefinition(
                name=skill_name,
                planning_config=skill_config,
            )
            for skill_name, skill_config in raw_skills.items()
        }
    )
