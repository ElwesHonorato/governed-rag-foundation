"""Capability catalog loader."""

from __future__ import annotations

from ai_infra.contracts.capability_descriptor import CapabilityDescriptor


class CapabilityCatalog:
    """In-memory capability metadata catalog."""

    def __init__(self, descriptors: list[CapabilityDescriptor]) -> None:
        self._descriptors = descriptors

    def load(self) -> list[CapabilityDescriptor]:
        return list(self._descriptors)
