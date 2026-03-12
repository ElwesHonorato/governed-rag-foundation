from dataclasses import dataclass

from pipeline_common.helpers.config import _optional_env, _required_int


@dataclass(frozen=True)
class DataHubSettings:
    """DataHub bootstrap settings for flow/job template upserts."""

    server: str
    token: str | None
    timeout_sec: float
    retry_max_times: int

    @classmethod
    def from_env(cls) -> "DataHubSettings":
        """Execute from env."""
        token = _optional_env("DATAHUB_TOKEN", "")
        server = _optional_env("DATAHUB_GMS_SERVER", "")
        if not server:
            server = _optional_env("DATAHUB_GMS_URL", "http://localhost:8081")
        return cls(
            server=server,
            token=token or None,
            timeout_sec=float(_optional_env("DATAHUB_TIMEOUT_SEC", "3")),
            retry_max_times=_required_int("DATAHUB_RETRY_MAX_TIMES", 1),
        )
