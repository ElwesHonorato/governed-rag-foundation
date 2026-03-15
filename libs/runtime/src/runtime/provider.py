import os
from dataclasses import dataclass, field


@dataclass
class Settings:
    ai_backend_url: str = field(init=False)
    ai_backend_timeout_seconds: int = field(init=False)

    def __post_init__(self) -> None:
        timeout_raw = os.getenv("AI_BACKEND_TIMEOUT_SECONDS", "30")
        try:
            ai_backend_timeout = int(timeout_raw)
        except ValueError as exc:
            raise ValueError("AI_BACKEND_TIMEOUT_SECONDS must be an integer") from exc
        self.ai_backend_url = self._required_env("AI_BACKEND_URL")
        self.ai_backend_timeout_seconds = ai_backend_timeout

    def dependencies_payload(self) -> dict[str, str]:
        return {"ai_backend": self.ai_backend_url}

    def _required_env(self, name: str) -> str:
        value = os.getenv(name)
        if not value:
            raise ValueError(f"{name} is not configured")
        return value.strip()
