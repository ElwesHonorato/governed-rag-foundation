#!/usr/bin/env python3
"""Group/owner governance manager."""

from __future__ import annotations

from entities.shared.context import GroupManagerContext
from entities.shared.definitions import GroupDefinition
from entities.shared.ports import GovernanceCatalogWriterPort


class GroupManager:
    """Apply owner-group definitions to DataHub."""

    def __init__(self, governance_def_ctx: GroupManagerContext) -> None:
        """Store shared governance execution context."""

        self.governance_def_ctx = governance_def_ctx
        self._governance_writer: GovernanceCatalogWriterPort = governance_def_ctx.governance_writer

    def apply(self, groups: list[GroupDefinition]) -> None:
        """Upsert all ownership groups."""

        for group in groups:
            self._governance_writer.upsert_group(
                group_urn=self.governance_def_ctx.group_urns[group.id],
                display_name=group.name,
                description=group.description,
                admin_refs=group.admins,
                member_refs=group.members,
                group_refs=group.groups,
            )
            print(f"upserted group {group.id}")
