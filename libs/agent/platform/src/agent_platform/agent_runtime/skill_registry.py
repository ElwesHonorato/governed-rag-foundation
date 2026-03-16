"""Skill registry contracts."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SkillDefinition:
    """Typed skill definition used by planning."""

    name: str
    planning_config: dict[str, object]


@dataclass(frozen=True)
class SkillRegistry:
    """Lookup boundary for configured skills."""

    _skills: dict[str, SkillDefinition]

    def names(self) -> list[str]:
        return sorted(self._skills.keys())

    def get(self, skill_name: str) -> SkillDefinition:
        try:
            return self._skills[skill_name]
        except KeyError as exc:
            raise ValueError(f"Unknown skill: {skill_name}") from exc
