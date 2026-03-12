"""Run identifier builders shared by workers."""

from __future__ import annotations

import hashlib
import time


def build_source_run_id(source_uri: str, *, timestamp: int | None = None) -> str:
    """Build run id from source URI hash + timestamp."""
    resolved_timestamp = int(time.time_ns()) if timestamp is None else int(timestamp)
    source_hash = hashlib.sha256(source_uri.encode("utf-8")).hexdigest()
    return f"{source_hash}-{resolved_timestamp}"
