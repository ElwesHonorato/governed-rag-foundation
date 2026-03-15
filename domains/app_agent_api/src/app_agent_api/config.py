"""Runtime settings for the agent API."""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    """Minimal HTTP runtime settings."""

    host: str = os.environ.get("AGENT_API_HOST", "0.0.0.0")
    port: int = int(os.environ.get("AGENT_API_PORT", "8010"))

    def payload(self) -> dict[str, object]:
        return {"host": self.host, "port": self.port}
