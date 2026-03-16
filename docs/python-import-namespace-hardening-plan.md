# Python Import Namespace Hardening Plan

## Purpose

This document defines the repo-wide fix for ambiguous Python imports such as:

```python
from startup.service_factory import ...
from services.worker_scan_service import ...
from infrastructure.datahub import ...
from cli.agent_cli import ...
```

These imports are structurally weak in a monorepo because they rely on generic top-level module names instead of unique package namespaces.

The goal is to remove that ambiguity once, at the architectural level, and stop reintroducing it in future domains and libraries.

This plan is intentionally adversarial:
- it assumes developers will run code from mixed environments
- it assumes editable installs, `PYTHONPATH`, IDEs, CI, and test runners will expose hidden import coupling
- it treats "works in one local shell" as insufficient evidence

## Executive Summary

### Main conclusion

The repository now has two different states:

1. Safe package-shaped projects
- `libs/agent/core`
- `libs/pipeline-common` at the import level
- `domains/ai_backend`
- `domains/ai_ui`
- `domains/app_vector_ui`
- `domains/llm_orchestration`

2. Namespaced but still operationally incomplete projects
- `domains/worker_scan`
- `domains/worker_parse_document`
- `domains/worker_index_weaviate`
- `domains/worker_embed_chunks`
- `domains/worker_chunk_text`
- `domains/gov_governance`

The highest-risk packaged boundary, `libs/agent/platform`, has already been fixed by restoring the `agent_platform.*` namespace. The remaining work is mostly operational consistency: package metadata, CI, Docker execution paths, and removal of `PYTHONPATH` as a supported contract.

## Findings

### 1. Fixed: `libs/agent/platform` no longer exports generic top-level packages

Current layout:

```text
libs/agent/platform/src/agent_platform/
  cli/
  startup/
  infrastructure/
  config/
```

Current imports:

```python
from agent_platform.startup.engine_factory import EngineFactory
from agent_platform.gateways.command.local_command_gateway import LocalCommandGateway
from agent_cli.app import main
```

Why this matters:
- this was the highest-risk packaged import boundary in the repo
- it should now be treated as the model for the other domains

### 2. Fixed in code, but still needs operational cleanup: worker domains repeat the same architectural pattern

Observed repeated top-level source directories:
- `startup`: 6 occurrences
- `services`: 4 occurrences
- `infrastructure`: 2 occurrences

Examples before the fix:
- `domains/worker_scan/src/startup`
- `domains/worker_parse_document/src/startup`
- `domains/worker_index_weaviate/src/startup`
- `domains/worker_embed_chunks/src/startup`

Current direction after the fix:
- `domains/worker_scan/src/worker_scan/startup`
- `domains/worker_parse_document/src/worker_parse_document/startup`
- `domains/worker_index_weaviate/src/worker_index_weaviate/startup`
- `domains/worker_embed_chunks/src/worker_embed_chunks/startup`

Why this is risky:
- today these workers mostly run with one app source root at a time
- tomorrow a shared test harness, local REPL, monorepo tooling, or a packaging cleanup will put multiple roots into one environment
- before the fix, `from startup...` and `from services...` became nondeterministic as soon as environments mixed

Adversarial interpretation:
- the current structure is a deferred bug
- the only reason it has not caused broader failures yet is execution isolation, not sound module design

### 3. Fixed in code, still incomplete operationally: governance code still relies on path-shaped execution

Observed:
- `domains/gov_governance/src/gov_governance/infrastructure`
- `domains/gov_governance/src/gov_governance/orchestration`
- `domains/gov_governance/src/gov_governance/state_loader`
- imports now use `gov_governance.*`
- README and CI examples set `PYTHONPATH=libs/pipeline-common/src`

Why this is risky:
- the governance package is still source-tree oriented
- it already relies on path shaping in docs and CI
- generic `infrastructure` is especially collision-prone in a monorepo

### 4. Medium: Dockerfiles and docs normalize path-based execution instead of package-based execution

Observed:
- several Dockerfiles set `PYTHONPATH=/app:/app/src:/pipeline-common/src`
- governance docs and workflow use `PYTHONPATH=... python domains/gov_governance/src/apply.py`
- test docs still use `PYTHONPATH` for low-level checks

Why this matters:
- path-order becomes part of runtime behavior
- packaging errors stay hidden
- import bugs appear only when environment shape changes

### 5. Low: some projects are still `package-mode = false`

Observed:
- all worker domains
- `domains/ai_ui`
- `domains/app_vector_ui`
- `libs/pipeline-common`

This is not automatically wrong. It becomes a problem when combined with:
- generic top-level module names
- cross-project imports
- `PYTHONPATH`-based execution

## Root Cause

The real problem is not merely "bad imports". The real problem is inconsistent rules for what `src/` means.

Today the repo mixes three patterns:

### Pattern A: true package namespace

Examples:
- `libs/agent/core/src/ai_infra`
- `domains/ai_backend/src/ai_backend`
- `domains/ai_ui/src/ai_ui`

This is structurally safe.

### Pattern B: isolated app source root with generic submodules

Examples:
- `domains/worker_scan/src/startup`
- `domains/worker_scan/src/services`

This is only conditionally safe if:
- the app is run in isolation
- no other source roots with the same names are importable

### Pattern C: reusable package with generic top-level submodules

Historical example:
- `libs/agent/platform/src/startup`

This is structurally unsafe.

That third pattern has now been removed from the agent platform. The second pattern should continue to be phased out or explicitly contained everywhere else.

## Non-Negotiable Repo Rules

These rules solve the problem permanently.

### Rule 1

Every reusable library or cross-domain dependency must have a unique package namespace.

Required shape:

```text
src/<unique_package_name>/
```

Examples:
- `src/ai_infra/`
- `src/agent_platform/`
- `src/ai_backend/`

Forbidden for reusable packages:
- `src/startup/`
- `src/services/`
- `src/infrastructure/`
- `src/cli/`

### Rule 2

No packaged project may expose generic top-level modules as its public import surface.

Forbidden:

```python
from startup...
from services...
from infrastructure...
from cli...
```

Required:

```python
from agent_platform.startup...
from worker_scan.startup...
from gov_governance.infrastructure...
```

### Rule 3

No supported runtime path may depend on `PYTHONPATH` for application imports.

Allowed:
- one-off debugging
- temporary local experiments

Not allowed as product contract:
- README instructions
- CI workflows
- Docker runtime assumptions
- stack runbooks

### Rule 4

If a domain is expected to stay source-tree-only, it must remain fully isolated and must not be imported by other projects.

That means:
- no path dependencies on it
- no cross-domain imports from it
- no shared test env depending on its internal modules

If that isolation is not guaranteed, the domain must be converted to a namespaced package.

### Rule 5

No backward compatibility for old import paths.

Do not add:
- alias packages
- compatibility wrappers
- dual import support
- re-export shims

Rename the package structure and update all call sites in the same change.

## Target End State

### Libraries

```text
libs/agent/core/src/ai_infra/
libs/pipeline-common/src/pipeline_common/
libs/agent/platform/src/agent_platform/
```

### Apps and worker domains

```text
domains/ai_backend/src/ai_backend/
domains/ai_ui/src/ai_ui/
domains/app_vector_ui/src/vector_ui/
domains/gov_governance/src/gov_governance/
domains/worker_scan/src/worker_scan/
domains/worker_parse_document/src/worker_parse_document/
domains/worker_index_weaviate/src/worker_index_weaviate/
domains/worker_embed_chunks/src/worker_embed_chunks/
domains/worker_chunk_text/src/worker_chunk_text/
```

### Internal subpackages

Inside each unique package root, these names are fine:
- `startup`
- `services`
- `infrastructure`
- `config`
- `processors`

Because they are namespaced:

```python
from worker_scan.startup.service_factory import ScanServiceFactory
from worker_parse_document.services.worker_parse_document_service import WorkerParseDocumentService
```

## Required Changes By Priority

## Priority 0: Immediate blocker

### `libs/agent/platform`

Move from:

```text
libs/agent/platform/src/
  cli/
  startup/
  infrastructure/
  config/
```

To:

```text
libs/agent/platform/src/agent_platform/
  cli/
  startup/
  infrastructure/
  config/
```

Update:
- `libs/agent/platform/pyproject.toml`
- all imports to `agent_platform.*`
- `domains/ai_backend` imports to `agent_platform.*`
- docs and tests

Why first:
- this is already a real dependency boundary
- this is already packaged
- this is the easiest place for an actual wrong import to hit a consumer

## Priority 1: Hardening shared or likely-to-spread code

### `domains/gov_governance`

Move from:

```text
domains/gov_governance/src/
  infrastructure/
  orchestration/
  state_loader/
```

To:

```text
domains/gov_governance/src/gov_governance/
  infrastructure/
  orchestration/
  state_loader/
```

Update:
- imports to `gov_governance.*`
- README examples
- CI workflow

Why next:
- it already has CI and documented execution paths
- it already depends on path shaping
- `infrastructure` is too generic to leave exposed

## Priority 2: Hardening worker domains

Convert each worker to a unique package root:

- `worker_scan`
- `worker_parse_document`
- `worker_index_weaviate`
- `worker_embed_chunks`
- `worker_chunk_text`

Example target:

```text
domains/worker_scan/src/worker_scan/
  app.py
  startup/
  services/
```

Required import change:

```python
from worker_scan.startup.service_factory import ScanServiceFactory
from worker_scan.services.worker_scan_service import WorkerScanService
```

Why:
- it removes ambiguity permanently
- it makes later packaging straightforward
- it stops every worker from reserving generic names at the top level

## Priority 3: Normalize packaging policy

For each domain, make an explicit decision:

### Option A: packaged project

Use:
- `packages = [{ include = "<package_name>", from = "src" }]`
- entrypoints or module-based launch

### Option B: isolated app shell

Allowed only if:
- it is not imported cross-project
- Docker, CI, and docs do not combine it with other ambiguous roots

My recommendation:
- make all Python deployables namespaced packages
- whether or not you fully package them with Poetry immediately

Even if `package-mode = false` stays temporarily, the source layout should still become:

```text
src/<unique_package_name>/
```

That is the core fix.

## Required Operational Changes

### Dockerfiles

Current pattern:

```dockerfile
PYTHONPATH=/app:/app/src:/pipeline-common/src
```

Required direction:
- prefer installed packages over `PYTHONPATH`
- if `PYTHONPATH` remains temporarily, it must not be relied on to disambiguate generic app modules

### CI

Remove supported workflows that depend on:
- `PYTHONPATH=... python domains/.../src/app.py`

Replace with:
- installed package entrypoints
- module-qualified invocation

### Docs

Remove examples that normalize:
- raw generic imports
- direct execution from ambiguous source roots
- `PYTHONPATH` as the supported operating mode

## Recommended Rollout

## Phase 1

Fix `libs/agent/platform` and `domains/ai_backend`.

Acceptance criteria:
- `agent_platform` package root restored
- no `from startup` or `from infrastructure` under `libs/agent/platform`
- no `from startup` imports inside `domains/ai_backend`

## Phase 2

Fix `domains/gov_governance`.

Acceptance criteria:
- all imports are `gov_governance.*`
- README and CI use package-safe execution paths

## Phase 3

Fix worker domains one by one.

Recommended order:
1. `worker_scan`
2. `worker_parse_document`
3. `worker_index_weaviate`
4. `worker_embed_chunks`
5. `worker_chunk_text`

Acceptance criteria for each worker:
- unique package root exists
- `startup` and `services` are no longer top-level imports
- runtime still works with the same external behavior

## Phase 4

Standardize CI and Docker execution paths.

Acceptance criteria:
- no supported execution path depends on generic top-level modules
- `PYTHONPATH` is not part of the primary runtime contract

## Verification Commands

These should become the enforcement checks.

### Check for forbidden generic imports

```bash
rg -n '^from (startup|services|infrastructure|cli|config|contracts|settings|routes|handlers|adapters|processors)\b|^import (startup|services|infrastructure|cli|config|contracts|settings|routes|handlers|adapters|processors)\b' domains libs -g '!**/.venv/**' -g '!**/__pycache__/**'
```

Expected result:
- no matches in packaged or cross-domain-consumed projects
- eventually no matches anywhere outside intentionally isolated temporary code

### Check for source-root generic package exposure

```bash
find domains libs -path '*/src' -type d -print | while read d; do find "$d" -mindepth 1 -maxdepth 1 -type d -printf '%f\n'; done | sort | uniq -c | sort -nr
```

Expected result:
- repeated names like `startup` and `services` disappear from top-level `src/` roots

### Check for path-based supported execution

```bash
rg -n 'PYTHONPATH|python .*src/app\.py|sys\.path\.insert' domains libs docs .github -g '!**/.venv/**' -g '!**/__pycache__/**'
```

Expected result:
- no supported product or CI path depends on these patterns

## What Not To Do

Do not solve this with:
- import alias shims
- fake `startup` compatibility packages
- transitional dual imports
- repo-wide `PYTHONPATH` conventions
- "just be careful" team norms

Those approaches preserve the ambiguity instead of removing it.

## Final Recommendation

Treat this as a repo-wide namespace governance problem.

The permanent fix is:
1. every reusable or externally consumed Python project gets a unique package root
2. every internal module import is qualified by that package root
3. no supported runtime path depends on `PYTHONPATH` to find application code
4. no backward-compatibility shims are added for old import paths

If you follow only one rule, follow this one:

```text
No top-level generic module names under any Python project src/ root.
Always use src/<unique_project_package>/...
```
