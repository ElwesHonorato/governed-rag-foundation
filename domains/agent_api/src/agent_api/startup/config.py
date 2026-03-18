"""Domain-local runtime config assembly for the agent API."""

from __future__ import annotations

from dataclasses import dataclass

from agent_platform.startup.contracts import LLMConfig, RetrievalConfig


@dataclass(frozen=True)
class AgentAPIConfig:
    """Resolved API process config grouped by concern."""

    llm: LLMConfig
    retrieval: RetrievalConfig
