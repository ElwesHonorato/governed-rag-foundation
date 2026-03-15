# Agent Platform Future Extraction Plan

## Purpose

`agent_platform` already lives under `libs/agent_platform`. This plan covers the remaining work needed to make that library easy to extract into its own repository later without another structural rewrite.

## Current State

- reusable agent runtime code lives in `libs/agent_platform`
- `domains/app_agent_api` consumes it as a package dependency
- `domains/agent_platform` has been removed
- the current source layout is:
  - `libs/agent_platform/src/cli`
  - `libs/agent_platform/src/startup`
  - `libs/agent_platform/src/infrastructure`
  - `libs/agent_platform/src/config`

## Extraction Goal

The future extracted repo should contain:

```text
agent-platform/
  pyproject.toml
  src/agent_platform/
    cli/
    startup/
    infrastructure/
    config/
  tests/
  README.md
```

That means the main remaining extraction step inside this monorepo is to restore a unique `agent_platform` package namespace before the eventual repo split.

## Required Work Before Extraction

### 1. Restore a unique package namespace

Current risk:
- imports use generic top-level module names such as `startup`, `cli`, and `infrastructure`

Required change:
- move the library to:
  - `libs/agent_platform/src/agent_platform/cli`
  - `libs/agent_platform/src/agent_platform/startup`
  - `libs/agent_platform/src/agent_platform/infrastructure`
  - `libs/agent_platform/src/agent_platform/config`
- update imports to `agent_platform.*`

Why this matters:
- extracted libraries should not expose generic top-level module names
- a stable package namespace makes the repo split mostly a packaging move

### 2. Remove repo-layout assumptions

The library must not depend on:
- the monorepo root being the current working directory
- `domains/` imports
- `stack.sh`
- source-relative paths for packaged assets

Required change:
- load static assets as package resources
- keep runtime state fully externalized through config

### 3. Tighten the public contract

Define what belongs to the reusable library surface:
- CLI entrypoint
- startup/service-factory APIs
- infrastructure adapters that are intended product surface

Keep out of the extracted package:
- deployable HTTP shell concerns
- containerization
- stack wiring
- repo-local operational conventions

### 4. Add extraction-readiness tests

Required checks:
- install `libs/agent_platform` from its own directory
- run the CLI after install
- instantiate the service factory with explicit environment
- run `domains/app_agent_api` against the installed package

Stronger optional check:
- install the package from a temporary directory outside the repo
- run a smoke command with explicit environment

## Dependency Shape

Keep this split:
- `libs/ai_infra` as the lower-level shared runtime library
- `libs/agent_platform` as the higher-level reusable product library
- `domains/app_agent_api` as the deployable HTTP shell

This keeps the future extracted repo flexible:
- it can carry both packages
- or `agent_platform` can continue consuming `ai_infra` as a separate dependency

## Definition Of Done For Extraction Readiness

- `libs/agent_platform` exposes a unique `agent_platform` package namespace
- `domains/app_agent_api` depends only on the packaged library
- no code depends on removed `domains/agent_platform` paths
- assets load without repo-relative path assumptions
- install/import/runtime checks pass from a clean environment

## Short Version

The move to `libs/` is complete. The remaining work for future extraction is to restore the `agent_platform` namespace, harden package/resource boundaries, and prove clean-environment installability. 
