"""Shared settings models for agent libraries."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class LLMSettings:
    """Settings for the local LLM gateway."""

    llm_url: str


@dataclass(frozen=True)
class RetrievalSettings:
    """Settings for retrieval infrastructure."""

    weaviate_url: str


@dataclass(frozen=True)
class AgentApiSettings:
    """Settings for exposing the agent API service."""

    host: str
    port: int
