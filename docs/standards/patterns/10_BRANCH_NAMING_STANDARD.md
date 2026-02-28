# Branch Naming Standard

## Goal
Use predictable, searchable branch names so reviewers can quickly understand intent and scope.

## Format
`<type>/<scope>-<short-kebab-description>`

Examples:
- `feat/rag-api-grounded-citations`
- `fix/worker-scan-queue-retry`
- `refactor/pipeline-common-stagequeue-contracts`

## Allowed Types
- `feat`: new user-facing or system capability
- `fix`: bug fix or regression fix
- `refactor`: internal design/code improvements without behavior change intent
- `docs`: documentation-only changes
- `test`: tests added/updated
- `chore`: maintenance, tooling, config, cleanup
- `infra`: infrastructure, compose, deployment, environment wiring
- `spike`: short-lived investigation/prototype (do not keep long-term)

## Scope Rules
- Use the main area being changed, e.g.:
  - `rag-api`
  - `vector-ui`
  - `pipeline-common`
  - `worker-scan`, `worker-parse-document`, etc.
  - `domains`, `scripts`, `requirements`
- If multiple areas are touched, pick the primary one by impact.

## Description Rules
- Lowercase kebab-case only.
- Keep it short: 3 to 8 words.
- Describe intent, not task mechanics.
- Avoid ticket IDs in the middle of the name; if required, append at the end.

Good:
- `feat/worker-index-weaviate-chunk-status`
- `docs/domains-readme-deep-dive`

Avoid:
- `newbranch`
- `fixStuff`
- `feature/rag api changes`
- `feat/rag-api/do-many-random-things`

## Optional Ticket Suffix
If your workflow requires tracking IDs, append them at the end:
- `fix/queue-reconnect-on-amqp-failure-grf-142`

## Protected/Main Branches
- `master`: protected integration branch
- No direct commits to `master`; use Pull Requests.

## Practical Workflow
1. Create branch from latest `master`.
2. Keep branch focused on one concern.
3. Use atomic commits.
4. Rebase/sync before opening PR.

## Compatibility Note
Existing branches like `sprint-01_prompt` are valid historical work branches. New branches should follow the standard above.
