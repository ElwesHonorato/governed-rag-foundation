"""Shared settings-provider abstraction for agent libraries and domains."""

from __future__ import annotations

from typing import Protocol, TypeVar

SettingsT = TypeVar("SettingsT")


class SettingsProvider(Protocol[SettingsT]):
    """Load one concrete settings object for a composition root."""

    def load(self) -> SettingsT:
        """Return the fully resolved settings object."""
