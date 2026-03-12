"""Embed worker orchestration contracts."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class EmbedWorkItem:
    """One embedding work item derived from an inbound URI."""

    uri: str
