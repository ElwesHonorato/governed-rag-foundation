"""Local config loaders."""

from __future__ import annotations

import json
from importlib.resources import files

from agent_platform.application.skill_registry import SkillDefinition, SkillRegistry
from ai_infra.contracts.capability_descriptor import CapabilityDescriptor
from ai_infra.registry.capability_catalog import CapabilityCatalog

CONFIG_PACKAGE = "agent_platform.config"


def load_capability_catalog() -> CapabilityCatalog:
    """Load capability metadata from packaged config resources."""

    raw_items = json.loads(files(CONFIG_PACKAGE).joinpath("capabilities.yaml").read_text())
    return CapabilityCatalog([CapabilityDescriptor(**item) for item in raw_items])


def load_skill_registry() -> SkillRegistry:
    """Load skill definitions from packaged config resources."""

    raw_skills = json.loads(files(CONFIG_PACKAGE).joinpath("skills.yaml").read_text())
    return SkillRegistry(
        {
            skill_name: SkillDefinition(
                name=skill_name,
                planning_config=skill_config,
            )
            for skill_name, skill_config in raw_skills.items()
        }
    )
