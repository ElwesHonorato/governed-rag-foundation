"""Capability policy checks."""

from __future__ import annotations

from ai_infra.contracts.capability_descriptor import CapabilityDescriptor


class CapabilityPolicy:
    """Ensures a capability descriptor can execute."""

    def validate(self, descriptor: CapabilityDescriptor) -> None:
        if not descriptor.name:
            raise ValueError("Capability descriptor must define a name.")
