"""Capability resolver."""

from __future__ import annotations

from ai_infra.contracts.capability_descriptor import CapabilityDescriptor


class CapabilityResolver:
    """Resolve capabilities by name."""

    def __init__(self, descriptors: list[CapabilityDescriptor]) -> None:
        self._descriptors = {descriptor.name: descriptor for descriptor in descriptors}

    def resolve(self, name: str) -> CapabilityDescriptor:
        try:
            return self._descriptors[name]
        except KeyError as exc:
            raise ValueError(f"Unknown capability: {name}") from exc

    def list_capabilities(self) -> list[CapabilityDescriptor]:
        return [self._descriptors[key] for key in sorted(self._descriptors)]
