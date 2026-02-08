# Commit Message Pattern (Phase-Based RAG Development)

Use this structure for all commits:

```text
<type>(<scope>): [phase-<n>] <short summary>

Why:
- <problem or goal>

What:
- <main change>

Validation:
- <tests/checks run>

Risks/Notes:
- <impact, rollout notes, follow-ups>

Refs:
- <issue/ticket/ADR/PR>
```

## Header rules
- Keep subject line under 72 chars.
- Use imperative mood (`add`, `fix`, `refactor`).
- Use one phase per commit (`phase-1`, `phase-2`, etc.).

## Allowed types
- `feat`: new behavior/capability
- `fix`: bug fix
- `refactor`: internal code restructuring
- `perf`: performance improvement
- `security`: security hardening
- `test`: tests only
- `docs`: documentation only
- `chore`: maintenance, tooling, housekeeping
- `ci`: CI/CD pipeline changes

## Suggested scopes for this repo
- `api`, `worker`, `retrieval`, `ingestion`, `governance`, `eval`, `infra`, `data`, `ops`

## Examples
```text
feat(retrieval): [phase-1] add vector search endpoint
```

```text
fix(worker): [phase-2] prevent duplicate chunk upserts on retry
```

```text
docs(governance): [phase-3] define policy evaluation lifecycle
```

## Optional local setup
To use the included template file:

```bash
git config commit.template .gitmessage
```
