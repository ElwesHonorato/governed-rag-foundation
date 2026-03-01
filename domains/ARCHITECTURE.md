# Domains Architecture

## Scope
`domains/` contains independently runnable deployable units:
- pipeline workers (`worker_*`)
- user-facing apps (`app_*`)
- governance apply tool (`gov_governance`)
- infrastructure compose domains (`infra_*`)

## Worker Subsystem (`domains/worker_*`)

### Responsibilities
- Implement stage-specific processing loops over queue/object-storage resources.
- Emit runtime lineage for each processing run.
- Transform payloads between pipeline stages.

### Common Internal Structure
```text
worker_x/
|- src/app.py                    # composition root
|- src/startup/config_extractor.py
|- src/startup/service_factory.py
|- src/services/*.py             # runtime behavior
`- src/contracts/contracts.py    # typed worker config contracts
```

### Patterns Used
- Composition Root in `app.py`
- Strategy-like config extraction (`WorkerConfigExtractor`)
- Factory-based service graph assembly (`*ServiceFactory`)
- Long-running service loop contract (`WorkerService.serve`)

### Anti-Patterns / Risks
- Some services type against concrete runtime lineage class instead of port interface.
- I/O side effects can happen during service factory build (`ensure_schema`, bucket bootstrap).

## App Subsystem (`domains/app_*`)
- Thin Flask services with local client wiring.
- Route handlers keep business logic in service/client helpers.
- Layering is pragmatic rather than strict clean architecture.

## Governance Subsystem (`domains/gov_governance`)
- Separate composition root and apply orchestration.
- Manager-per-entity pattern with shared resolved reference maps.
- Direct DataHub SDK usage in orchestration/managers is intentional for this tool path.

## Infra Subsystem (`domains/infra_*`)
- Docker-compose packages for local infrastructure dependencies.
- No runtime Python architecture beyond deployment wiring.

## Fit In Broader System
- Worker domains form the data pipeline runtime.
- App domains provide query and inspection interfaces.
- Governance domain manages catalog topology/config used by runtime lineage and job config extraction.
