# Requirements Workspace

This folder is the single source for requirements and development instructions consumed by humans and AI agents.

## Structure
- `00-overview/`: Vision, scope, glossary, stakeholders, links.
- `10-product/`: Product goals, personas, journeys, UX constraints.
- `20-functional/`: Feature requirements, use cases, user stories.
- `30-non-functional/`: Performance, reliability, observability, scalability.
- `40-architecture/`: System context, boundaries, technical decisions.
- `50-integrations/`: External services, APIs, contracts, SLAs.
- `60-data/`: Data model, lineage, retention, governance rules.
- `70-security-compliance/`: Security controls, risk, compliance requirements.
- `80-testing-acceptance/`: Test strategy, acceptance criteria, quality gates.
- `90-ai-ops/`: AI-specific instructions, prompting rules, guardrails, eval criteria.
- `95-open-questions/`: Unresolved questions, assumptions to validate, blockers.
- `99-decisions/`: ADRs and dated decisions.

## Suggested file naming
Use date-prefixed files for change tracking, for example:
- `2026-02-09-prd-v1.md`
- `2026-02-09-auth-requirements.md`
- `2026-02-09-adr-0001-service-boundary.md`

## AI-friendly doc tips
- Keep requirements atomic and testable.
- Prefer explicit constraints over implied behavior.
- Include examples and anti-examples.
- Add acceptance criteria for every requirement.
