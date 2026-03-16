# Agent Platform Future Extraction Plan

## Purpose

`agent_platform` already lives under `libs/agent/platform`. This plan covers the remaining work needed to make that library easy to extract into its own repository later without another structural rewrite.

## Current State

- reusable agent runtime code lives in `libs/agent/platform`
- `domains/agent_api` consumes it as a package dependency
- `domains/agent_platform` has been removed
- the current source layout is:
  - `libs/agent/platform/src/agent_platform/cli`
  - `libs/agent/platform/src/agent_platform/startup`
  - `libs/agent/platform/src/agent_platform/infrastructure`
  - `libs/agent/platform/src/agent_platform/config`

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

That means the main extraction-critical namespace work is already done inside this monorepo.

## Required Work Before Extraction

### 1. Keep the package namespace stable

Current requirement:
- keep imports under `agent_platform.*`
- do not reintroduce generic top-level modules such as `startup`, `cli`, or `infrastructure`

Why this matters:
- extracted libraries should not expose generic top-level module names
- the repo split stays mostly a packaging move only if this namespace remains stable

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
- install `libs/agent/platform` from its own directory
- run the CLI after install
- instantiate the service factory with explicit environment
- run `domains/agent_api` against the installed package

Stronger optional check:
- install the package from a temporary directory outside the repo
- run a smoke command with explicit environment

## Dependency Shape

Keep this split:
- `libs/agent/core` as the lower-level shared runtime library
- `libs/agent/platform` as the higher-level reusable product library
- `domains/agent_api` as the deployable HTTP shell

This keeps the future extracted repo flexible:
- it can carry both packages
- or `agent_platform` can continue consuming `ai_infra` as a separate dependency

## Definition Of Done For Extraction Readiness

- `libs/agent/platform` exposes a unique `agent_platform` package namespace
- `domains/agent_api` depends only on the packaged library
- no code depends on removed `domains/agent_platform` paths
- assets load without repo-relative path assumptions
- install/import/runtime checks pass from a clean environment

## Short Version

The move to `libs/` and the `agent_platform` namespace restoration are complete. The remaining work for future extraction is to harden package/resource boundaries and prove clean-environment installability.
