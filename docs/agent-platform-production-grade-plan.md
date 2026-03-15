# Agent Platform Production-Grade Migration Plan

## Purpose

This plan upgrades the current `agent_platform` MVP from a source-tree-run prototype into a production-grade Python package set with explicit imports, supported entrypoints, and CI-verifiable install behavior.

The immediate trigger for this plan is the current bootstrap approach in:
- `domains/agent_platform/src/app.py`
- `domains/app_agent_api/src/agent_api/app.py`

Both files mutate `sys.path` because the code is not currently installed as packages and because imports depend on ambiguous top-level module names such as `startup`, `cli`, and `infrastructure`.

## Current Problems

### 1. Entrypoints depend on `sys.path` mutation

Current behavior:
- `domains/agent_platform/src/app.py` inserts `libs/ai_infra/src` and `domains/agent_platform/src` into `sys.path`
- `domains/app_agent_api/src/agent_api/app.py` inserts three source roots into `sys.path`

Why this is not production-grade:
- runtime behavior depends on execution path rather than install state
- import resolution is hidden inside application code
- local success does not prove clean-environment installability
- any new entrypoint risks duplicating the same bootstrap logic

### 2. Projects are not packaged

Current behavior:
- `domains/agent_platform/pyproject.toml` uses `package-mode = false`
- `domains/app_agent_api/pyproject.toml` uses `package-mode = false`
- `libs/ai_infra/pyproject.toml` uses `package-mode = false`

Why this is not production-grade:
- no supported install path
- no console scripts
- no clean way to express inter-project dependencies
- deployment/runtime tooling cannot rely on standard packaging semantics

### 3. Imports are ambiguous across the monorepo

Current examples:
- `from startup.service_factory import AgentPlatformServiceFactory`
- `from infrastructure.local_command_runner import LocalCommandRunner`
- `from cli.agent_cli import main`

Why this is risky:
- `startup`, `cli`, and `infrastructure` are generic top-level names
- the repo already contains repeated top-level names across domains
- imports can change meaning based on `sys.path` order
- test runners, IDEs, and shells become fragile

### 4. API domain crosses domain boundaries through source-path tricks

Current behavior:
- `app_agent_api` reaches into `agent_platform` source via path mutation and top-level imports

Why this is not production-grade:
- the dependency exists, but it is implicit rather than declared
- API startup is coupled to repo layout rather than package contracts

### 5. Supported execution path is unclear

Current behavior:
- the working commands use `python3 domains/.../app.py`

Why this is not production-grade:
- direct source-file execution should not be the supported interface
- production operations should rely on installed console scripts or a WSGI/ASGI module target

## Target State

At the end of this migration:
- no application code mutates `sys.path`
- `ai_infra`, `agent_platform`, and `app_agent_api` are installable packages
- all imports are package-qualified and unambiguous
- CLI and API are launched through supported installed entrypoints
- inter-project dependencies are explicit in packaging metadata
- CI verifies install, import, and runtime behavior from a clean environment

## Recommended Package Shape

### 1. `libs/ai_infra`

Keep as shared library:
- package name: `ai_infra`
- source root: `libs/ai_infra/src/ai_infra`

### 2. `domains/agent_platform`

Convert into a real package with a stable package namespace:
- preferred package name: `agent_platform`
- move code under:
  - `domains/agent_platform/src/agent_platform/cli/`
  - `domains/agent_platform/src/agent_platform/startup/`
  - `domains/agent_platform/src/agent_platform/infrastructure/`
  - `domains/agent_platform/src/agent_platform/config/` for packaged assets if appropriate

### 3. `domains/app_agent_api`

Keep HTTP surface separate but package it properly:
- package name: `app_agent_api` or `agent_api_app`
- avoid reusing `agent_api` as a generic top-level import if there is any risk of collision
- expose a production-ready `create_app()` function from the package

## Migration Phases

## Phase 1: Normalize imports and package boundaries

### Goals
- eliminate ambiguous top-level imports
- make code importable by package name alone

### Changes

#### `domains/agent_platform`

Move from:
- `domains/agent_platform/src/app.py`
- `domains/agent_platform/src/cli/...`
- `domains/agent_platform/src/startup/...`
- `domains/agent_platform/src/infrastructure/...`

To:
- `domains/agent_platform/src/agent_platform/__init__.py`
- `domains/agent_platform/src/agent_platform/cli/agent_cli.py`
- `domains/agent_platform/src/agent_platform/startup/service_factory.py`
- `domains/agent_platform/src/agent_platform/infrastructure/...`

Update imports to forms like:
- `from agent_platform.cli.agent_cli import main`
- `from agent_platform.startup.service_factory import AgentPlatformServiceFactory`
- `from agent_platform.infrastructure.local_command_runner import LocalCommandRunner`

#### `domains/app_agent_api`

Move from:
- `domains/app_agent_api/src/agent_api/...`

To a package-qualified structure, for example:
- `domains/app_agent_api/src/app_agent_api/__init__.py`
- `domains/app_agent_api/src/app_agent_api/config.py`
- `domains/app_agent_api/src/app_agent_api/routes.py`
- `domains/app_agent_api/src/app_agent_api/wsgi.py`

Update imports to forms like:
- `from app_agent_api.config import Settings`
- `from app_agent_api.routes import AgentApiApplication`
- `from agent_platform.startup.service_factory import AgentPlatformServiceFactory`

### Acceptance criteria
- `rg -n "from (startup|cli|infrastructure)\\b"` returns no matches for these projects
- application imports resolve without `sys.path` mutation

## Phase 2: Turn all three projects into installable packages

### Goals
- replace source-tree assumptions with packaging metadata
- support editable installs for development and standard installs for CI

### Changes

#### `libs/ai_infra/pyproject.toml`

Update to package mode with explicit package inclusion.

Expected outcomes:
- `poetry install` installs `ai_infra`
- dependent projects can declare it as a path dependency during local development

#### `domains/agent_platform/pyproject.toml`

Add:
- real package metadata
- dependency on `ai_infra`
- console script entrypoint, for example:
  - `agent-platform = "agent_platform.cli.agent_cli:main"`

#### `domains/app_agent_api/pyproject.toml`

Add:
- real package metadata
- dependency on `ai_infra`
- dependency on `agent_platform`
- script or application module export, for example:
  - `agent-api = "app_agent_api.wsgi:main"`

### Acceptance criteria
- each project installs successfully in a clean environment
- installed scripts run without `PYTHONPATH` or `sys.path` changes

## Phase 3: Replace direct-file execution with supported entrypoints

### Goals
- define one supported way to run the CLI and one supported way to run the API

### Changes

#### CLI

Remove `domains/agent_platform/src/app.py` as the supported launcher.

Options:
- delete it entirely
- or keep a minimal compatibility wrapper temporarily that imports the installed package and emits a warning

Preferred supported command:

```bash
cd domains/agent_platform && poetry run agent-platform skill-list
```

#### API

Replace `domains/app_agent_api/src/agent_api/app.py` as the supported run command.

Preferred supported command:

```bash
cd domains/app_agent_api && poetry run agent-api
```

Also expose:
- a stable `create_app()` import target for production servers

### Acceptance criteria
- repo docs no longer instruct users to run `python3 domains/.../app.py`
- CLI and API both run through installed scripts

## Phase 4: Make configuration and asset loading package-safe

### Goals
- stop relying on brittle path math for config and prompt assets
- separate repo-root discovery from packaged resource loading

### Current risk

`AgentPlatformConfigExtractor` currently derives paths via:
- `Path(__file__).resolve().parents[4]`

This is fragile once the project is installed in editable or wheel form.

### Changes

Split configuration into:
- runtime settings:
  - workspace root
  - state directory
  - host/port
- packaged static assets:
  - prompt templates
  - capability catalog
  - skill definitions

Use:
- environment variables or typed settings for workspace/state roots
- packaged resource loading for static config assets

Potential implementation:
- `importlib.resources` for packaged YAML/JSON prompt assets
- explicit environment contract for `AGENT_PLATFORM_WORKSPACE_ROOT`
- explicit environment contract for `AGENT_PLATFORM_STATE_DIR`

### Acceptance criteria
- no business-critical asset path depends on `parents[4]`
- installs work outside the repo root

## Phase 5: Establish production-grade API serving model

### Goals
- stop treating `wsgiref.simple_server` as the deployment path

### Changes

Keep:
- `create_app()` as the application factory

Add:
- WSGI entrypoint module suitable for Gunicorn
- optionally ASGI migration only if there is a real need; do not add framework churn without requirements

Recommended minimal production shape:
- `app_agent_api.wsgi:app`
- local dev may still use a simple server wrapper
- production docs point to Gunicorn or equivalent

### Acceptance criteria
- production docs reference a standard application server
- local server wrapper is clearly marked dev-only

## Phase 6: Add test coverage for packaging and runtime contracts

### Goals
- make installability and entrypoint integrity testable

### Required tests

#### Unit tests
- `SandboxPolicy`
- `TerminationPolicy`
- `CapabilityExecutionService`
- `RunSupervisor`
- `AgentSessionManager`
- file-backed stores

#### Integration tests
- CLI entrypoint works after install
- API application factory works after install
- packaged prompt/config assets load correctly
- path sandbox rejects out-of-workspace command arguments

#### Packaging tests
- importing `agent_platform`, `app_agent_api`, and `ai_infra` succeeds in a clean environment
- no tests rely on source-tree path hacks

### Acceptance criteria
- test suite passes from installed package roots
- there are no test-only `sys.path` patches for the main package flow

## Phase 7: Add CI enforcement

### Goals
- fail early if import/install behavior regresses

### Required CI checks
- install `libs/ai_infra`
- install `domains/agent_platform`
- install `domains/app_agent_api`
- run tests for affected projects
- run a CLI smoke command
- import the API factory

Recommended smoke commands:

```bash
cd domains/agent_platform && poetry run agent-platform skill-list
cd domains/app_agent_api && poetry run python -c "from app_agent_api.wsgi import create_app; create_app()"
```

### Acceptance criteria
- CI proves packaging, imports, and basic runtime wiring

## Concrete File-Level Worklist

### `libs/ai_infra`
- update `libs/ai_infra/pyproject.toml`
- verify package inclusion rules

### `domains/agent_platform`
- replace `domains/agent_platform/pyproject.toml`
- create `domains/agent_platform/src/agent_platform/__init__.py`
- move `cli/`, `startup/`, `infrastructure/` under `agent_platform/`
- remove path-bootstrapping from the current launcher
- add console script entrypoint
- update config asset loading
- update README and architecture docs

### `domains/app_agent_api`
- replace `domains/app_agent_api/pyproject.toml`
- move `agent_api/` into a stable package namespace if needed
- remove path-bootstrapping from the current launcher
- expose `create_app()` and stable WSGI module
- add console script or server instructions
- update README and architecture docs

### `docs/`
- update `docs/ARCHITECTURE.md`
- update project READMEs
- add install and run instructions based on packaged entrypoints
- remove direct-source execution as the primary guidance

## Recommended Execution Order

1. Restructure `agent_platform` into a real package namespace
2. Restructure `app_agent_api` into a real package namespace
3. Convert `ai_infra`, `agent_platform`, and `app_agent_api` to installable Poetry packages
4. Replace source-file run paths with console scripts and WSGI module targets
5. Refactor config/resource loading away from repo-path assumptions
6. Add unit/integration/packaging tests
7. Add CI install/import/smoke checks
8. Remove any temporary compatibility wrappers

## Non-Goals For This Migration

Do not expand platform scope while fixing packaging:
- no new capabilities
- no new skills
- no approval workflow expansion
- no retrieval redesign
- no framework migration unless runtime requirements demand it

This migration is about execution hygiene, packaging correctness, and operability.

## Definition Of Done

- no `sys.path.insert` remains in application code
- no bare imports like `startup`, `cli`, or `infrastructure` remain in the agent projects
- all three projects are installable packages
- CLI runs via installed console script
- API runs via supported installed module or script
- config and prompt assets load without repo-root path hacks
- tests cover install/import/runtime basics
- CI verifies the supported install and launch paths
