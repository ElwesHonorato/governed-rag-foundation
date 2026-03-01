#!/usr/bin/env python3
"""Shared context objects and URN resolution for governance managers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from datahub.metadata.urns import CorpGroupUrn, DatasetUrn, DomainUrn, GlossaryTermUrn, TagUrn


@dataclass(frozen=True)
class ResolvedRefs:
    """Resolved URN maps keyed by governance IDs.

    The maps are intentionally separate by entity type. They are not positional
    structures and do not need to be "tied" to each other by index. The shared
    contract is key semantics:
    - `domain_urns` keys are domain IDs.
    - `group_urns` keys are group IDs.
    - `tag_urns` keys are tag IDs.
    - `term_urns` keys are term IDs.
    - `dataset_urns` keys are dataset IDs.

    Example:
    - domain_urns: {"rag-platform": "urn:li:domain:rag-platform"}
    - group_urns: {"search-platform": "urn:li:corpGroup:search-platform"}
    - tag_urns: {"internal": "urn:li:tag:internal"}
    - term_urns: {"embedding": "urn:li:glossaryTerm:embedding"}
    - dataset_urns: {
        "s3.rag-data.04_chunks":
        "urn:li:dataset:(urn:li:dataPlatform:s3,rag-data/04_chunks,DEV)"
      }
    """

    domain_urns: dict[str, str]
    group_urns: dict[str, str]
    tag_urns: dict[str, str]
    term_urns: dict[str, str]
    dataset_urns: dict[str, str]


@dataclass(frozen=True)
class DomainManagerContext:
    """Context required by the domain manager."""

    domain_writer: Any
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
    """Context required by the dataset manager.

    The ID->URN maps are provided independently on purpose. During dataset apply,
    each dataset row references IDs (domain/owners/tags/terms) and the manager
    resolves each reference against the corresponding map.

    Example dataset row:
    - {
        "id": "s3.rag-data.04_chunks",
        "domain": "rag-platform",
        "owners": ["search-platform"],
        "tags": ["internal"],
        "terms": ["embedding"]
      }

    Resolution examples:
    - `domain_urns["rag-platform"]`
    - `group_urns["search-platform"]`
    - `tag_urns["internal"]`
    - `term_urns["embedding"]`
    """

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


@dataclass(frozen=True)
class ManagerContexts:
    """Per-manager split contexts for governance apply orchestration."""

    domain: DomainManagerContext
    group: GroupManagerContext
    taxonomy: TaxonomyManagerContext
    dataset: DatasetManagerContext
    flow_job: FlowJobManagerContext
    lineage: LineageContractManagerContext


def resolve_refs(model: Any, env: str) -> ResolvedRefs:
    """Build all commonly-used URN maps from one governance snapshot.

    Input:
    - `model`: snapshot with domains/groups/tags/terms/datasets definitions.
    - `env`: DataHub environment label used in dataset URNs (for example `DEV`).

    Output:
    - `ResolvedRefs` with per-entity ID->URN maps used by managers.
    """

    return ResolvedRefs(
        domain_urns={d["id"]: str(DomainUrn(d["id"])) for d in model.domains},
        group_urns={g["id"]: str(CorpGroupUrn(g["id"])) for g in model.groups},
        tag_urns={t["id"]: str(TagUrn(t["name"])) for t in model.tags},
        term_urns={t["id"]: str(GlossaryTermUrn(t["id"])) for t in model.terms},
        dataset_urns={
            d["id"]: str(DatasetUrn(platform=d["platform"], name=d["name"], env=env)) for d in model.datasets
        },
    )
