from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class FrontendAgentApiSettings:
    """Frontend-facing settings for calling the agent API service."""

    agent_api_url: str
    agent_api_timeout_seconds: int

    def dependencies_payload(self) -> dict[str, str]:
        return {"agent_api": self.agent_api_url}


@dataclass(frozen=True)
class AgentApiSettings:
    """Settings for exposing the agent API service."""

    host: str
    port: int

    @property
    def to_dict(self) -> dict[str, object]:
        return asdict(self)
