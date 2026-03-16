"""Shared settings-provider abstraction and environment helpers."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Protocol, TypeVar

from agent_settings.settings.models import LLMSettings, RetrievalSettings

SettingsT = TypeVar("SettingsT")


class SettingsProvider(Protocol[SettingsT]):
    """Load one concrete settings object for a composition root."""

    def load(self) -> SettingsT:
        """Return the fully resolved settings object."""


@dataclass(frozen=True)
class SettingsRequest:
    """Requested shared settings to load from environment."""

    llm: bool = False
    retrieval: bool = False


@dataclass(frozen=True)
class SettingsBundle:
    """Bundle of loaded shared settings based on a requested set."""

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


def optional_int_env(name: str, default: int) -> int:
    raw_value = os.environ.get(name)
    if raw_value is None or not raw_value.strip():
        return default
    try:
        return int(raw_value.strip())
    except ValueError as exc:
        raise ValueError(f"{name} must be an integer") from exc


def load_llm_settings_from_env() -> LLMSettings:
    return LLMSettings(
        llm_url=required_env("LLM_URL"),
        llm_model=required_env("LLM_MODEL"),
        llm_timeout_seconds=required_int_env("LLM_TIMEOUT_SECONDS"),
    )


def load_retrieval_settings_from_env() -> RetrievalSettings:
    return RetrievalSettings(
        weaviate_url=required_env("WEAVIATE_URL"),
        embedding_dim=required_int_env("EMBEDDING_DIM"),
        retrieval_limit=optional_int_env("WEAVIATE_QUERY_DEFAULTS_LIMIT", 5),
    )
class SharedSettingsProvider:
    """Load requested shared settings from environment variables."""

    def __init__(self, request: SettingsRequest) -> None:
        self._request = request

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
            llm=self.llm,
            retrieval=self.retrieval,
        )
