#!/usr/bin/env python3
"""Group/owner governance manager."""

from __future__ import annotations

from typing import Any

from datahub.emitter.mcp import MetadataChangeProposalWrapper
from datahub.metadata.schema_classes import ChangeTypeClass, CorpGroupInfoClass

from entities.shared.context import GovernanceContext


class GroupManager:
    """Apply owner-group definitions to DataHub."""

    def __init__(self, ctx: GovernanceContext) -> None:
        """Store shared governance execution context."""

        self.ctx = ctx

    def apply(self, groups: list[dict[str, Any]]) -> None:
        """Upsert all ownership groups."""

        for group in groups:
            aspect = CorpGroupInfoClass(
                displayName=group.get("name"),
                description=group.get("description"),
            )
            self.ctx.graph.emit(
                MetadataChangeProposalWrapper(
                    entityUrn=self.ctx.refs.group_urns[group["id"]],
                    entityType="corpGroup",
                    aspectName="corpGroupInfo",
                    aspect=aspect,
                    changeType=ChangeTypeClass.UPSERT,
                )
            )
            print(f"upserted group {group['id']}")
