"""Capability registry facade."""

from __future__ import annotations

from ai_infra.contracts.capability_descriptor import CapabilityDescriptor
from ai_infra.registry.capability_catalog import CapabilityCatalog
from ai_infra.registry.capability_resolver import CapabilityResolver


class CapabilityRegistry:
    """File-backed capability registry."""

    def __init__(self, catalog: CapabilityCatalog) -> None:
        self._catalog = catalog
        self._resolver = CapabilityResolver(self._catalog.load())

    def list_capabilities(self) -> list[CapabilityDescriptor]:
        return self._resolver.list_capabilities()

    def resolve(self, name: str) -> CapabilityDescriptor:
        return self._resolver.resolve(name)
