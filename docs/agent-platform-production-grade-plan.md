# Agent Platform Production-Grade Plan

## Purpose

This plan upgrades the current `agent_platform` implementation from a working internal package into a production-grade library with explicit contracts, stable imports, tested packaging, and a clean consumer boundary for `app_agent_api`.

The current code already removed `sys.path` bootstrapping and moved the reusable runtime into:
- `libs/agent_platform`
- `libs/ai_infra`
- `domains/app_agent_api`

This document now describes the current state and the remaining work. It does not preserve transitional layouts or backward-compatibility steps.

## Current State

### Libraries and consumers

- `libs/ai_infra` is the shared runtime library.
- `libs/agent_platform` is the reusable agent runtime package and CLI host.
- `domains/app_agent_api` is the HTTP shell that consumes `agent_platform`.

### What is already fixed

- application code no longer mutates `sys.path`
- `agent_platform`, `ai_infra`, and `app_agent_api` are installable Poetry packages
- the CLI runs through the installed `agent-platform` entrypoint
- the API imports the runtime through declared package dependencies

### What is still not production-grade

#### 1. Import names are still too generic

Current examples:
- `from startup.service_factory import AgentPlatformServiceFactory`
- `from infrastructure.local_command_runner import LocalCommandRunner`
- `from cli.agent_cli import main`

Why this is still weak:
- `startup`, `cli`, and `infrastructure` are generic top-level module names
- those names are easy to collide with in a monorepo or extracted repo
- the current shape works because the package environment is controlled, not because the import surface is strong

#### 2. Static assets are still path-addressed from source layout

Current examples:
- prompt/config assets live under `libs/agent_platform/src/config`
- some tooling and docs still reference those asset paths directly

Why this is still weak:
- source-relative paths are more brittle than packaged resource loading
- wheel/install behavior should not depend on raw repo layout assumptions

#### 3. Runtime configuration needs a tighter contract

Current examples:
- `AGENT_PLATFORM_WORKSPACE_ROOT`
- `LLM_URL`
- `LLM_MODEL`
- `LLM_TIMEOUT_SECONDS`

Why this needs hardening:
- required environment should be validated consistently at startup
- defaults and state directories should be documented as part of the package contract
- consumers should not infer config behavior from source code

#### 4. API serving is still MVP-grade

Current shape:
- `app_agent_api` exposes `create_app()`
- local serving works, but the production server contract is still light

Why this needs hardening:
- production docs should define the supported WSGI/ASGI serving path
- health, config, and deployment expectations should be explicit

#### 5. Packaging and runtime tests are too light

Current gap:
- there are smoke checks and manual validation
- there is not yet a strong automated test layer for install/import/runtime behavior

Why this matters:
- packaging regressions are easy to reintroduce
- clean-environment behavior should be proven in CI, not inferred

## Target State

At the end of this plan:
- `libs/agent_platform` remains the reusable runtime package
- `domains/app_agent_api` remains the deployable HTTP shell
- `agent_platform` has a stable, unique package namespace
- prompt/config assets load through package-safe resource access
- runtime configuration is explicit and validated
- packaging, entrypoints, and consumer imports are covered by tests and CI

## Recommended Package Shape

### `libs/ai_infra`

Keep as the shared low-level library:
- package name: `ai_infra`
- source root: `libs/ai_infra/src/ai_infra`

### `libs/agent_platform`

Keep as the reusable runtime library, but restore a unique package namespace:
- package name: `agent_platform`
- preferred source root: `libs/agent_platform/src/agent_platform`
- subpackages:
  - `agent_platform.cli`
  - `agent_platform.startup`
  - `agent_platform.infrastructure`
  - `agent_platform.config` or packaged resources

This is the one structural reversal recommended here. The extra package namespace is not redundant at library scope; it is what prevents generic top-level module collisions once this code is consumed outside its own project root.

### `domains/app_agent_api`

Keep as the deployable consumer:
- package name: `app_agent_api`
- imports `agent_platform` through packaging metadata only
- exposes `create_app()` and a supported production server target

## Phases

## Phase 1: Restore a unique library namespace

### Goals

- eliminate generic top-level imports from `libs/agent_platform`
- make the library safe to consume from other projects and a future extracted repo

### Changes

- move:
  - `libs/agent_platform/src/cli`
  - `libs/agent_platform/src/startup`
  - `libs/agent_platform/src/infrastructure`
  - `libs/agent_platform/src/config`
  under:
  - `libs/agent_platform/src/agent_platform/`
- update imports to:
  - `from agent_platform.startup.service_factory import AgentPlatformServiceFactory`
  - `from agent_platform.infrastructure.local_command_runner import LocalCommandRunner`
  - `from agent_platform.cli.agent_cli import main`
- update Poetry package inclusion and script targets accordingly

### Acceptance criteria

- `rg -n "from (startup|cli|infrastructure)\\b" libs/agent_platform domains/app_agent_api` returns no package-import matches
- the installed console script still works
- the API still imports `create_app()` cleanly through installed dependencies

## Phase 2: Make asset loading package-safe

### Goals

- remove raw source-tree assumptions for prompts and static config

### Changes

- load packaged YAML/JSON assets through `importlib.resources`
- keep runtime-generated state separate from packaged static resources
- remove direct references to `src/config/...` from application behavior

### Acceptance criteria

- packaged assets load after install without depending on repo-relative paths
- runtime state writes only to configured state directories

## Phase 3: Harden runtime configuration

### Goals

- make startup configuration explicit, validated, and documented

### Changes

- define a typed settings contract for:
  - `AGENT_PLATFORM_WORKSPACE_ROOT`
  - `AGENT_PLATFORM_STATE_DIR`
  - `LLM_URL`
  - `LLM_MODEL`
  - `LLM_TIMEOUT_SECONDS`
- fail fast on missing required values
- document the supported environment contract in the library README and API README

### Acceptance criteria

- startup fails with clear errors on invalid configuration
- docs match the actual required settings

## Phase 4: Harden the API deployment contract

### Goals

- make `app_agent_api` production-servable with a clear contract

### Changes

- define the supported production entrypoint for `app_agent_api`
- document the expected application server
- keep local dev serving separate from production serving guidance

### Acceptance criteria

- the API has one documented production run path
- the app factory and deployment target are both covered by tests

## Phase 5: Add packaging and runtime tests

### Required tests

#### Unit tests

- `SandboxPolicy`
- `TerminationPolicy`
- `CapabilityExecutionService`
- `RunSupervisor`
- config extraction and validation
- file-backed stores

#### Integration tests

- installed `agent-platform` CLI works
- `app_agent_api.create_app()` works after install
- packaged assets load correctly
- out-of-workspace command arguments are rejected
- non-zero command results are surfaced as failures

#### Packaging tests

- importing `ai_infra`, `agent_platform`, and `app_agent_api` succeeds in a clean environment
- no test depends on `PYTHONPATH` hacks or source-path mutation

### Acceptance criteria

- package install/import/runtime behavior is covered by automated tests
- clean-environment behavior is reproducible in CI

## Phase 6: Add CI enforcement

### Required CI checks

- install `libs/ai_infra`
- install `libs/agent_platform`
- install `domains/app_agent_api`
- run affected test suites
- run CLI smoke check
- import the API factory

Recommended smoke checks:

```bash
cd libs/agent_platform && poetry run agent-platform skill-list
cd domains/app_agent_api && poetry run python -c "from app_agent_api.app import create_app; create_app()"
```

### Acceptance criteria

- CI proves packaging, imports, and basic runtime wiring

## Concrete Worklist

### `libs/ai_infra`

- keep package metadata current
- verify dependency contracts stay domain-agnostic

### `libs/agent_platform`

- restore the `agent_platform` package namespace
- update imports and script targets
- move static asset loading to package resources
- tighten config extraction and validation
- update README and architecture docs

### `domains/app_agent_api`

- keep dependency on `libs/agent_platform` explicit
- define the supported production server contract
- update README and runtime docs

### `docs/`

- keep `docs/ARCHITECTURE.md` aligned with the current `libs/agent_platform` placement
- document only the supported package and entrypoint layout
- avoid migration-only references to removed paths

## Non-Goals

This plan does not expand platform scope:
- no new capabilities
- no new skills
- no retrieval redesign
- no compatibility shims
- no temporary wrappers for removed paths

## Definition Of Done

- `libs/agent_platform` exposes a unique `agent_platform` package namespace again
- no generic top-level imports like `startup`, `cli`, or `infrastructure` remain in production code
- packaged assets load safely after install
- config contracts are explicit and validated
- CLI and API install and run through supported entrypoints
- tests cover install/import/runtime basics
- CI verifies the supported paths
