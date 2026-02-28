# Guidance Inventory And Consolidation Map

This document tracks where guidance existed before normalization and where it now lives.

## Inventory (discovered)
- Root/project docs:
  - `README.md`
  - `requirements/40-architecture/rag-architecture-blueprint.md`
  - `requirements/99-decisions/README.md`
- Pattern/standards corpus:
  - `standards/patterns/10_BRANCH_NAMING_STANDARD.md`
  - `standards/patterns/20_COMMIT_MESSAGE_PATTERN.md`
  - `standards/patterns/30_DOCSTRING_STANDARD.md`
  - `standards/patterns/40_INFRASTRUCTURE_FACTORY_NAMING_REVIEW.md`
  - `standards/patterns/50_WORKER_BOOTSTRAP_PATTERN.md`
  - `standards/patterns/60_WORKER_SCAN_INITIALIZATION_FLOW.md`

## Normalized guidance locations
- Repo-wide agent rules: `AGENTS.md`
- Scoped agent rules:
  - `domains/AGENTS.md`
  - `libs/pipeline-common/AGENTS.md`
  - `governance/AGENTS.md`
- Architecture + implementation patterns:
  - `docs/ARCHITECTURE.md`
  - `docs/patterns/*.md`
- ADR landing page:
  - `docs/adr/README.md`

## Consolidation map
- Startup/composition guidance:
  - Source: `standards/patterns/50_*`, `standards/patterns/60_*`
  - Normalized: `docs/patterns/composition-root.md`, `docs/patterns/dependency-injection.md`
- Error/logging operational guidance:
  - Source: worker service behavior + architecture references
  - Normalized: `docs/patterns/error-handling.md`, `docs/patterns/logging-and-tracing.md`
- Architecture summary:
  - Source: `README.md`, `requirements/40-architecture/*`
  - Normalized: `docs/ARCHITECTURE.md`
- ADR direction:
  - Source: `requirements/99-decisions/README.md`
  - Normalized pointer: `docs/adr/README.md`

## Notes
- Existing standards under `standards/patterns/` are preserved.
- `docs/` is intended as the practical, non-duplicative developer-facing guidance surface.
- TODO: if team prefers a single canonical location, choose one of `docs/patterns/` or `standards/patterns/` and keep the other as index-only links.
