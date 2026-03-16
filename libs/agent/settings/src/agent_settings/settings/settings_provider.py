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

from agent_settings.settings.contracts import SettingsBundle, SettingsRequest
from agent_settings.settings.env_loaders import (
    load_agent_api_settings_from_env,
    load_frontend_agent_api_settings_from_env,
)
from agent_settings.settings.models import AgentApiSettings, FrontendAgentApiSettings


class SettingsProvider:
    """Load requested runtime settings from environment variables."""

    def __init__(self, request: SettingsRequest) -> None:
        self._request = request

    @property
    def frontend_agent_api(self) -> FrontendAgentApiSettings | None:
        if not self._request.frontend_agent_api:
            return None
        return load_frontend_agent_api_settings_from_env()

    @property
    def agent_api(self) -> AgentApiSettings | None:
        if not self._request.agent_api:
            return None
        return load_agent_api_settings_from_env()

    @property
    def bundle(self) -> SettingsBundle:
        return SettingsBundle(
            frontend_agent_api=self.frontend_agent_api,
            agent_api=self.agent_api,
        )
