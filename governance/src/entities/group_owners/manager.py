#!/usr/bin/env python3
"""Group/owner governance manager."""

from __future__ import annotations

from typing import Any

from datahub.emitter.mcp import MetadataChangeProposalWrapper
from datahub.metadata.urns import CorpGroupUrn, CorpUserUrn
from datahub.metadata.schema_classes import ChangeTypeClass, CorpGroupInfoClass

from entities.shared.context import GroupManagerContext


class GroupManager:
    """Apply owner-group definitions to DataHub."""

    def __init__(self, governance_def_ctx: GroupManagerContext) -> None:
        """Store shared governance execution context."""

        self.governance_def_ctx = governance_def_ctx

    def apply(self, groups: list[dict[str, Any]]) -> None:
        """Upsert all ownership groups."""

        for group in groups:
            admins = self._as_user_urns(group.get("admins", []))
            members = self._as_user_urns(group.get("members", []))
            nested_groups = self._as_group_urns(group.get("groups", []))
            aspect = CorpGroupInfoClass(
                displayName=group.get("name"),
                description=group.get("description"),
                admins=admins,
                members=members,
                groups=nested_groups,
            )
            self.governance_def_ctx.graph.emit(
                MetadataChangeProposalWrapper(
                    entityUrn=self.governance_def_ctx.group_urns[group["id"]],
                    entityType="corpGroup",
                    aspectName="corpGroupInfo",
                    aspect=aspect,
                    changeType=ChangeTypeClass.UPSERT,
                )
            )
            print(f"upserted group {group['id']}")

    def _as_user_urns(self, values: Any) -> list[str]:
        if not isinstance(values, list):
            return []
        user_urns: list[str] = []
        for value in values:
            if not isinstance(value, str) or not value:
                continue
            user_urns.append(value if value.startswith("urn:li:corpuser:") else str(CorpUserUrn(value)))
        return user_urns

    def _as_group_urns(self, values: Any) -> list[str]:
        if not isinstance(values, list):
            return []
        group_urns: list[str] = []
        for value in values:
            if not isinstance(value, str) or not value:
                continue
            if value.startswith("urn:li:corpGroup:"):
                group_urns.append(value)
            else:
                group_urns.append(self.governance_def_ctx.group_urns.get(value, str(CorpGroupUrn(value))))
        return group_urns
