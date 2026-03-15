"""Inference configuration contracts."""

from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class InferenceConfiguration:
    """Minimal inference configuration for the MVP."""

    provider_name: str
    model_name: str
    temperature: float = 0.0
    max_output_tokens: int = 800

    def to_dict(self) -> dict[str, object]:
        return asdict(self)
