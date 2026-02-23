#!/usr/bin/env python3
"""Shared context objects and URN resolution for governance managers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from datahub.metadata.urns import CorpGroupUrn, DatasetUrn, DomainUrn, GlossaryTermUrn, TagUrn


@dataclass(frozen=True)
class ResolvedRefs:
    """Resolved URNs for governance IDs across entity types."""

    domain_urns: dict[str, str]
    group_urns: dict[str, str]
    tag_urns: dict[str, str]
    term_urns: dict[str, str]
    dataset_urns: dict[str, str]


@dataclass(frozen=True)
class DomainManagerContext:
    """Context required by the domain manager."""

    graph: Any
    domain_urns: dict[str, str]


@dataclass(frozen=True)
class GroupManagerContext:
    """Context required by the group manager."""

    graph: Any
    group_urns: dict[str, str]


@dataclass(frozen=True)
class TaxonomyManagerContext:
    """Context required by the taxonomy manager."""

    client: Any
    graph: Any
    term_urns: dict[str, str]


@dataclass(frozen=True)
class DatasetManagerContext:
    """Context required by the dataset manager."""

    client: Any
    env: str
    domain_urns: dict[str, str]
    group_urns: dict[str, str]
    tag_urns: dict[str, str]
    term_urns: dict[str, str]


@dataclass(frozen=True)
class FlowJobManagerContext:
    """Context required by the flow/job manager."""

    client: Any
    env: str
    domain_urns: dict[str, str]
    group_urns: dict[str, str]


@dataclass(frozen=True)
class LineageContractManagerContext:
    """Context required by the lineage-contract manager."""

    client: Any
    dataset_urns: dict[str, str]


def resolve_refs(model: Any, env: str) -> ResolvedRefs:
    """Build all commonly-used URN mappings from loaded definitions."""

    return ResolvedRefs(
        domain_urns={d["id"]: str(DomainUrn(d["id"])) for d in model.domains},
        group_urns={g["id"]: str(CorpGroupUrn(g["id"])) for g in model.groups},
        tag_urns={t["id"]: str(TagUrn(t["name"])) for t in model.tags},
        term_urns={t["id"]: str(GlossaryTermUrn(t["id"])) for t in model.terms},
        dataset_urns={
            d["id"]: str(DatasetUrn(platform=d["platform"], name=d["name"], env=env)) for d in model.datasets
        },
    )
