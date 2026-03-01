# Dependency Injection

## Intent
Inject dependencies explicitly so modules are reusable, testable, and stable under refactor.

## When To Use
- Startup contracts (`RuntimeContextFactory`, `WorkerRuntimeLauncher`).
- Worker service graph assembly (`WorkerServiceFactory` implementations).

## How To Apply
1. Prefer constructor injection over hidden global/env access inside business classes.
2. Keep interface contracts in shared library (`libs/pipeline-common`).
3. Inject runtime dependencies (`lineage`, `queue`, `storage`) through context objects.
4. Keep env loading in composition roots where feasible.

## Example
- `RuntimeContextFactory` receives typed settings objects.
- `WorkerRuntimeLauncher` receives a runtime factory and strategy collaborators.
- Services receive concrete gateways/processors, not env lookups.

## Anti-Patterns
- Calling `*.from_env()` in deep service/processor layers.
- Creating external clients ad hoc inside processing methods.
- Tight coupling to one worker domain from shared `libs/`.

## Notes
- Current repo has per-project tooling differences; keep DI contracts minimal and avoid framework-specific assumptions.
