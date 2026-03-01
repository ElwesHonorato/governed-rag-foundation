# Settings Architecture

## Scope
`pipeline_common.settings` provides environment-driven runtime settings loading for worker bootstrapping.

## Responsibilities
- Declare capability-scoped settings requests (`SettingsRequest`).
- Lazily load requested settings (`storage`, `queue`, `datahub`) from environment.
- Return a typed `SettingsBundle` used by startup composition.

## Layer Placement
- Observed layer: Infrastructure Configuration Adapter
- Upstream consumers: worker composition roots and runtime factory
- Downstream dependencies: env vars and gateway-specific settings modules

## Patterns Used
- Provider: `SettingsProvider` encapsulates capability-aware loading.
- Data-transfer bundle: `SettingsBundle` transports loaded settings to runtime factory.
- Null-object via optional fields: unrequested capabilities are `None`.

## Anti-Patterns / Risks
- Constructors/properties may perform environment reads repeatedly; caching is at bundle call site, not provider field level.
- DB/cache support is declared but intentionally unimplemented (`NotImplementedError`).

## Fit In Broader System
- Settings are the first boundary crossed in worker composition roots.
- This module keeps env parsing separate from business services and gateway code.
