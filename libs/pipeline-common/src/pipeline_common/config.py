import os



def _required_env(name: str) -> str:
    """Internal helper for required env."""
    value = os.getenv(name)
    if not value:
        raise ValueError(f"{name} is not configured")
    return value.strip()


def _optional_env(name: str, default: str) -> str:
    """Internal helper for optional env."""
    value = os.getenv(name, default)
    return value.strip() or default


def _required_int(name: str, default: int) -> int:
    """Internal helper for required int."""
    raw = _optional_env(name, str(default))
    try:
        parsed = int(raw)
    except ValueError as exc:
        raise ValueError(f"{name} must be an integer") from exc
    if parsed <= 0:
        raise ValueError(f"{name} must be greater than zero")
    return parsed
