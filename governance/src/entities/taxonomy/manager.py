#!/usr/bin/env python3
"""Tag and glossary governance manager."""

from __future__ import annotations

from typing import Any

from datahub.emitter.mcp import MetadataChangeProposalWrapper
from datahub.metadata.schema_classes import ChangeTypeClass, GlossaryTermInfoClass
from datahub.sdk import Tag

from entities.shared.context import GovernanceContext


class TaxonomyManager:
    """Apply taxonomy entities: tags and glossary terms."""

    def __init__(self, ctx: GovernanceContext) -> None:
        """Store shared governance execution context."""

        self.ctx = ctx

    def apply(self, tags: list[dict[str, Any]], terms: list[dict[str, Any]]) -> None:
        """Upsert tags and glossary terms."""

        self._apply_tags(tags)
        self._apply_glossary_terms(terms)

    def _apply_tags(self, tags: list[dict[str, Any]]) -> None:
        """Upsert tag entities using the DataHub SDK."""

        for tag in tags:
            self.ctx.client.entities.upsert(
                Tag(
                    name=tag["name"],
                    display_name=tag.get("name"),
                    description=tag.get("description"),
                )
            )
            print(f"upserted tag {tag['id']}")

    def _apply_glossary_terms(self, terms: list[dict[str, Any]]) -> None:
        """Upsert glossary term entities via MCP emission."""

        for term in terms:
            aspect = GlossaryTermInfoClass(
                id=term["id"],
                name=term["name"],
                definition=term.get("description"),
            )
            self.ctx.graph.emit(
                MetadataChangeProposalWrapper(
                    entityUrn=self.ctx.refs.term_urns[term["id"]],
                    entityType="glossaryTerm",
                    aspectName="glossaryTermInfo",
                    aspect=aspect,
                    changeType=ChangeTypeClass.UPSERT,
                )
            )
            print(f"upserted glossary term {term['id']}")
