"""Startup contracts."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RepositoryPaths:
    """Repository-derived paths used by the local runtime."""

    repo_root: str
    workspace_root: str
    state_dir: str


@dataclass(frozen=True)
class LLMSettings:
    """Settings for the local LLM gateway."""

    llm_url: str
    llm_model: str
    llm_timeout_seconds: int


@dataclass(frozen=True)
class RetrievalSettings:
    """Settings for retrieval infrastructure."""

    weaviate_url: str
    embedding_dim: int
    retrieval_limit: int


@dataclass(frozen=True)
class AgentPlatformConfig:
    """Resolved startup configuration grouped by component."""

    paths: RepositoryPaths
    llm: LLMSettings
    retrieval: RetrievalSettings
