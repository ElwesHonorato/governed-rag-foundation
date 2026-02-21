#!/usr/bin/env python3
"""Shared context objects and URN resolution for governance managers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ResolvedRefs:
    """Resolved URNs for governance IDs across entity types."""

    domain_urns: dict[str, str]
    group_urns: dict[str, str]
    tag_urns: dict[str, str]
    term_urns: dict[str, str]
    dataset_urns: dict[str, str]


@dataclass(frozen=True)
class GovernanceContext:
    """Execution context shared by all governance entity managers."""

    env_label: str
    client: Any
    graph: Any
    refs: ResolvedRefs


def resolve_refs(model: Any, env_label: str) -> ResolvedRefs:
    """Build all commonly-used URN mappings from loaded definitions."""

    from datahub.metadata.urns import CorpGroupUrn, DatasetUrn, DomainUrn, GlossaryTermUrn, TagUrn

    return ResolvedRefs(
        domain_urns={d["id"]: str(DomainUrn(d["id"])) for d in model.domains},
        group_urns={g["id"]: str(CorpGroupUrn(g["id"])) for g in model.groups},
        tag_urns={t["id"]: str(TagUrn(t["name"])) for t in model.tags},
        term_urns={t["id"]: str(GlossaryTermUrn(t["id"])) for t in model.terms},
        dataset_urns={
            d["id"]: str(DatasetUrn(platform=d["platform"], name=d["name"], env=env_label)) for d in model.datasets
        },
    )
