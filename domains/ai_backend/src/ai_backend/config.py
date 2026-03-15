"""Runtime settings for the AI backend."""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    """Minimal HTTP runtime settings."""

    host: str = os.environ.get("AI_BACKEND_HOST", "0.0.0.0")
    port: int = int(os.environ.get("AI_BACKEND_PORT", "8010"))

    def payload(self) -> dict[str, object]:
        return {"host": self.host, "port": self.port}
