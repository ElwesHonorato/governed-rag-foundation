from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class LineageQueryConfig:
    api_base_url: str
    job_namespace: str
    dataset_namespace: str
    no_color: bool
