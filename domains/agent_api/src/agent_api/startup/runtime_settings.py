"""Domain-local runtime config assembly for the agent API."""

from __future__ import annotations

from dataclasses import dataclass

from agent_platform.startup.contracts import LLMRetrievalConfig
from agent_settings.settings import LLMSettings, RetrievalSettings, SettingsBundle


@dataclass(frozen=True)
class AgentAPIConfig(LLMRetrievalConfig):
    llm: LLMSettings
    retrieval: RetrievalSettings


@dataclass(frozen=True)
class AgentAPIConfigFactory:
    """Build API runtime config from the centralized settings bundle."""

    def build(self, settings: SettingsBundle) -> AgentAPIConfig:
        return AgentAPIConfig(
            llm=settings.llm,
            retrieval=settings.retrieval,
        )
