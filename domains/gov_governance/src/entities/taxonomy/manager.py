#!/usr/bin/env python3
"""Tag and glossary governance manager."""

from __future__ import annotations

import logging

from entities.shared.context import TaxonomyManagerContext
from entities.shared.definitions import TagDefinition, TermDefinition
from entities.shared.ports import GovernanceCatalogWriterPort

logger = logging.getLogger(__name__)


class TaxonomyManager:
    """Apply taxonomy entities: tags and glossary terms."""

    def __init__(self, governance_def_ctx: TaxonomyManagerContext) -> None:
        """Store shared governance execution context."""

        self.governance_def_ctx = governance_def_ctx
        self._governance_writer: GovernanceCatalogWriterPort = governance_def_ctx.governance_writer

    def apply(self, tags: list[TagDefinition], terms: list[TermDefinition]) -> None:
        """Upsert tags and glossary terms."""

        self._apply_tags(tags)
        self._apply_glossary_terms(terms)

    def _apply_tags(self, tags: list[TagDefinition]) -> None:
        """Upsert tag entities using the DataHub SDK."""

        for tag in tags:
            self._governance_writer.upsert_tag(
                name=tag.name,
                display_name=tag.name,
                description=tag.description,
            )
            logger.info("upserted tag %s", tag.id)

    def _apply_glossary_terms(self, terms: list[TermDefinition]) -> None:
        """Upsert glossary term entities via MCP emission."""

        for term in terms:
            self._governance_writer.upsert_glossary_term(
                entity_urn=self.governance_def_ctx.term_urns[term.id],
                term_id=term.id,
                name=term.name,
                definition=term.description,
            )
            logger.info("upserted glossary term %s", term.id)
