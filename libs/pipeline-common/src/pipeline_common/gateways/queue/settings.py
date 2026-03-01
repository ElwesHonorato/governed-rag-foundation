from dataclasses import dataclass

from pipeline_common.helpers.config import _required_env, _required_int


@dataclass(frozen=True)
class QueueRuntimeSettings:
    """Queue runtime settings for workers."""

    broker_url: str
    queue_pop_timeout_seconds: int

    @classmethod
    def from_env(cls) -> "QueueRuntimeSettings":
        """Execute from env."""
        return cls(
            broker_url=_required_env("BROKER_URL"),
            queue_pop_timeout_seconds=_required_int("QUEUE_POP_TIMEOUT_SECONDS", 1),
        )
