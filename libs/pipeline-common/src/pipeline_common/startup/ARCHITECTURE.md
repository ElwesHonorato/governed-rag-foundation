# Startup Architecture

## Scope
`pipeline_common.startup` defines worker bootstrap contracts and orchestrates the standard startup pipeline.

## Responsibilities
- Define startup extension contracts:
  - `WorkerConfigExtractor`
  - `WorkerServiceFactory`
  - `WorkerService`
- Build a shared `WorkerRuntimeContext` with configured gateways.
- Execute the startup sequence consistently across all worker domains.

## Layer Placement
- Observed layer: Application Wiring + Composition Utilities
- Upstream consumers: `domains/worker_*/src/app.py`
- Downstream dependencies: `pipeline_common.settings` and `pipeline_common.gateways`

## Runtime Startup Flow
```text
worker app.py (composition root)
  -> SettingsProvider(...).bundle
  -> RuntimeContextFactory(data_job_key, settings_bundle)
      -> build lineage/storage/queue gateways
      -> parse DataHub custom properties into job_properties
  -> WorkerRuntimeLauncher(...)
      -> config_extractor.extract(job_properties)
      -> service_factory.build(runtime_context, worker_config)
      -> service.serve()
```

## Patterns Used
- Template-method-like orchestration: fixed launcher sequence with pluggable extractor/factory.
- Factory: runtime and service construction classes.
- Dependency injection: runtime context and typed config are injected into worker services.

## Anti-Patterns / Risks
- Hidden I/O in constructor:
  - `RuntimeContextFactory.__init__` builds runtime context immediately.
- Tight coupling to runtime data shape:
  - extractors assume `job_properties["job"]` schema with strict keys.

## Fit In Broader System
- This is the common worker bootstrap backbone used by all worker domains.
- It standardizes initialization and keeps worker `app.py` files shallow.
