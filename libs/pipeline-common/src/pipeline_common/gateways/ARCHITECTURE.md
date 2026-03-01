# Gateways Architecture

## Scope
This subsystem contains runtime adapters around external systems used by workers:
- DataHub runtime lineage
- S3-compatible object storage
- RabbitMQ-compatible stage queues
- Lightweight observability counters

## Responsibilities
- Present stable Python APIs to worker services.
- Encapsulate SDK/client specifics (`datahub`, `boto3`, `pika`).
- Keep external connectivity and protocol details out of worker business logic.

## Layer Placement
- Observed layer: Infrastructure Adapter
- Upstream consumers: `pipeline_common.startup.runtime_factory` and worker service factories
- Downstream dependencies: external SDKs and network services

## Patterns Used
- Adapter/Facade: `ObjectStorageGateway`, `StageQueue`, `DataHubGraphClient`
- Factory: `gateways/factories/*` create configured gateway objects
- Protocol port: lineage runtime exposes `LineageRuntimeGateway`

## Anti-Patterns / Risks
- Hidden I/O in constructor:
  - `StageQueue.__init__` opens AMQP connection.
- Adapter leakage risk:
  - Worker services still frequently type against concrete `DataHubRuntimeLineage`.
- Mixed responsibility pressure:
  - Runtime lineage adapter manages both run state and DataHub emission workflow.

## Submodules
```text
gateways/
|- factories/
|  |- lineage_gateway_factory.py
|  |- object_storage_gateway_factory.py
|  `- queue_gateway_factory.py
|- lineage/
|  |- lineage.py
|  |- runtime_contracts.py
|  `- ARCHITECTURE.md
|- object_storage/object_storage.py
|- queue/queue.py
`- observability/counters.py
```

## Fit In Broader System
- Gateways are the worker runtime infrastructure boundary.
- They are instantiated in composition roots indirectly via startup/runtime factory.
- Worker services should treat them as runtime ports, not as domain logic containers.
