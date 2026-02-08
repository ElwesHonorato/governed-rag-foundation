# Commit Message Pattern

Use this structure for all commits:

```text
<type>(<scope>): <short summary>

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
feat(retrieval): add vector search endpoint
```

```text
fix(worker): prevent duplicate chunk upserts on retry
```

```text
docs(governance): define policy evaluation lifecycle
```

## Optional local setup
To use the included template file:

```bash
git config commit.template .gitmessage
```
