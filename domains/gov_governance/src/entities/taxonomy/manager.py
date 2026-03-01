#!/usr/bin/env python3
"""Tag and glossary governance manager."""

from __future__ import annotations

from typing import Any

from entities.shared.context import TaxonomyManagerContext
from entities.shared.ports import GovernanceCatalogWriterPort


class TaxonomyManager:
    """Apply taxonomy entities: tags and glossary terms."""

    def __init__(self, governance_def_ctx: TaxonomyManagerContext) -> None:
        """Store shared governance execution context."""

        self.governance_def_ctx = governance_def_ctx
        self._governance_writer: GovernanceCatalogWriterPort = governance_def_ctx.governance_writer

    def apply(self, tags: list[dict[str, Any]], terms: list[dict[str, Any]]) -> None:
        """Upsert tags and glossary terms."""

        self._apply_tags(tags)
        self._apply_glossary_terms(terms)

    def _apply_tags(self, tags: list[dict[str, Any]]) -> None:
        """Upsert tag entities using the DataHub SDK."""

        for tag in tags:
            self._governance_writer.upsert_tag(
                name=tag["name"],
                display_name=tag.get("name"),
                description=tag.get("description"),
            )
            print(f"upserted tag {tag['id']}")

    def _apply_glossary_terms(self, terms: list[dict[str, Any]]) -> None:
        """Upsert glossary term entities via MCP emission."""

        for term in terms:
            self._governance_writer.upsert_glossary_term(
                entity_urn=self.governance_def_ctx.term_urns[term["id"]],
                term_id=term["id"],
                name=term["name"],
                definition=term.get("description"),
            )
            print(f"upserted glossary term {term['id']}")
