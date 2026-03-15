"""Local config loaders."""

from __future__ import annotations

import json
from importlib.resources import files

from ai_infra.contracts.capability_descriptor import CapabilityDescriptor
from ai_infra.registry.capability_catalog import CapabilityCatalog

CONFIG_PACKAGE = "agent_platform.config"


def load_capability_catalog() -> CapabilityCatalog:
    """Load capability metadata from packaged config resources."""

    raw_items = json.loads(files(CONFIG_PACKAGE).joinpath("capabilities.yaml").read_text())
    return CapabilityCatalog([CapabilityDescriptor(**item) for item in raw_items])


def load_skill_registry() -> dict[str, dict[str, object]]:
    """Load skill definitions from packaged config resources."""

    return json.loads(files(CONFIG_PACKAGE).joinpath("skills.yaml").read_text())
