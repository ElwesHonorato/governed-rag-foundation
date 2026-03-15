"""Runtime settings provider for application domains.

Layer:
- Infrastructure configuration adapter used by composition roots.

Role:
- Convert environment variables into typed settings objects requested by a
  startup path.

Design intent:
- Keep env parsing logic out of application wiring and request handlers.
- Allow each startup path to request only the settings it needs.
"""

from __future__ import annotations

import os
from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class FrontendAIBackendSettings:
    """Frontend-facing settings for calling the AI backend service."""

    ai_backend_url: str
    ai_backend_timeout_seconds: int

    def dependencies_payload(self) -> dict[str, str]:
        return {"ai_backend": self.ai_backend_url}


@dataclass(frozen=True)
class BackendAIBackendSettings:
    """Backend-facing settings for exposing the AI backend service."""

    host: str
    port: int

    @property
    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class SettingsRequest:
    """Requested runtime settings to load from environment."""

    frontend_ai_backend: bool = False
    backend_ai_backend: bool = False


@dataclass(frozen=True)
class SettingsBundle:
    """Bundle of loaded settings based on a requested scope."""

    frontend_ai_backend: FrontendAIBackendSettings | None = None
    backend_ai_backend: BackendAIBackendSettings | None = None


def load_frontend_ai_backend_settings_from_env() -> FrontendAIBackendSettings:
    """Load frontend settings for calling the AI backend service."""
    return FrontendAIBackendSettings(
        ai_backend_url=_required_env("AI_BACKEND_URL"),
        ai_backend_timeout_seconds=_required_int_env("AI_BACKEND_TIMEOUT_SECONDS"),
    )


def load_backend_ai_backend_settings_from_env() -> BackendAIBackendSettings:
    """Load backend settings for exposing the AI backend service."""
    return BackendAIBackendSettings(
        host=_required_env("AI_BACKEND_HOST"),
        port=_required_int_env("AI_BACKEND_PORT"),
    )


class SettingsProvider:
    """Load requested runtime settings from environment variables."""

    def __init__(self, request: SettingsRequest) -> None:
        self._request = request

    @property
    def frontend_ai_backend(self) -> FrontendAIBackendSettings | None:
        if not self._request.frontend_ai_backend:
            return None
        return load_frontend_ai_backend_settings_from_env()

    @property
    def backend_ai_backend(self) -> BackendAIBackendSettings | None:
        if not self._request.backend_ai_backend:
            return None
        return load_backend_ai_backend_settings_from_env()

    @property
    def bundle(self) -> SettingsBundle:
        return SettingsBundle(
            frontend_ai_backend=self.frontend_ai_backend,
            backend_ai_backend=self.backend_ai_backend,
        )


def _required_env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise ValueError(f"{name} is not configured")
    return value.strip()


def _required_int_env(name: str) -> int:
    raw_value = _required_env(name)
    try:
        return int(raw_value)
    except ValueError as exc:
        raise ValueError(f"{name} must be an integer") from exc
