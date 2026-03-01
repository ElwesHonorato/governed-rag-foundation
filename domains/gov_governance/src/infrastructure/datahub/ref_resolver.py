#!/usr/bin/env python3
"""DataHub URN resolver for governance reference maps."""

from __future__ import annotations

from datahub.metadata.urns import CorpGroupUrn, DatasetUrn, DomainUrn, GlossaryTermUrn, TagUrn

from entities import ResolvedRefs
from state_loader import GovernanceDefinitionSnapshot


def resolve_refs(snapshot: GovernanceDefinitionSnapshot, env_name: str) -> ResolvedRefs:
    """Resolve governance ID->URN maps using DataHub URN classes."""

    return ResolvedRefs(
        domain_urns={d["id"]: str(DomainUrn(d["id"])) for d in snapshot.domains},
        group_urns={g["id"]: str(CorpGroupUrn(g["id"])) for g in snapshot.groups},
        tag_urns={t["id"]: str(TagUrn(t["name"])) for t in snapshot.tags},
        term_urns={t["id"]: str(GlossaryTermUrn(t["id"])) for t in snapshot.terms},
        dataset_urns={
            d["id"]: str(DatasetUrn(platform=d["platform"], name=d["name"], env=env_name))
            for d in snapshot.datasets
        },
    )
