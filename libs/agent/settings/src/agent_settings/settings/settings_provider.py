"""Shared settings-provider abstraction and environment helpers."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Protocol, TypeVar

from agent_settings.settings.models import (
    AgentApiSettings,
    LLMSettings,
    RetrievalSettings,
)

SettingsT = TypeVar("SettingsT")


class SettingsProvider(Protocol[SettingsT]):
    """Load one concrete settings object for a composition root."""

    def load(self) -> SettingsT:
        """Return the fully resolved settings object."""


@dataclass(frozen=True)
class SettingsRequest:
    """Requested shared settings to load from environment."""

    agent_api: bool = False
    llm: bool = False
    retrieval: bool = False


@dataclass(frozen=True)
class SettingsBundle:
    """Bundle of loaded shared settings based on a requested set."""

    agent_api: AgentApiSettings | None = None
    llm: LLMSettings | None = None
    retrieval: RetrievalSettings | None = None


def required_env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise ValueError(f"{name} is not configured")
    return value.strip()


def required_int_env(name: str) -> int:
    raw_value = required_env(name)
    try:
        return int(raw_value)
    except ValueError as exc:
        raise ValueError(f"{name} must be an integer") from exc

def load_llm_settings_from_env() -> LLMSettings:
    return LLMSettings(
        llm_url=required_env("LLM_URL"),
    )


def load_agent_api_settings_from_env() -> AgentApiSettings:
    return AgentApiSettings(
        host=required_env("AGENT_API_HOST"),
        port=required_int_env("AGENT_API_PORT"),
    )


def load_retrieval_settings_from_env() -> RetrievalSettings:
    return RetrievalSettings(
        weaviate_url=required_env("WEAVIATE_URL"),
    )


class EnvironmentSettingsProvider:
    """Load requested shared settings from environment variables."""

    def __init__(self, request: SettingsRequest) -> None:
        self._request = request

    @property
    def agent_api(self) -> AgentApiSettings | None:
        if not self._request.agent_api:
            return None
        return load_agent_api_settings_from_env()

    @property
    def llm(self) -> LLMSettings | None:
        if not self._request.llm:
            return None
        return load_llm_settings_from_env()

    @property
    def retrieval(self) -> RetrievalSettings | None:
        if not self._request.retrieval:
            return None
        return load_retrieval_settings_from_env()

    @property
    def bundle(self) -> SettingsBundle:
        return SettingsBundle(
            agent_api=self.agent_api,
            llm=self.llm,
            retrieval=self.retrieval,
        )
