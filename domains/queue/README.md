# queue domain

This domain is the pipeline traffic controller. It decouples stages so each worker can process jobs independently and reliably.

## Deep Dive

### What runs here
- `rabbitmq` (`rabbitmq:3-management-alpine`)

### How it contributes to RAG
- Carries stage-to-stage work messages:
  - `q.parse_document`
  - `q.chunk_text`
  - `q.embed_chunks`
  - `q.index_weaviate`
- Carries stage DLQs:
  - `q.scan.dlq`
  - `q.parse_document.dlq`
  - `q.chunk_text.dlq`
  - `q.embed_chunks.dlq`
  - `q.index_weaviate.dlq`
- Enables resilient asynchronous processing between workers.

### Runtime dependencies
- RabbitMQ credentials via `RABBITMQ_DEFAULT_USER`, `RABBITMQ_DEFAULT_PASS`.
- Data persisted in named volume `rabbitmq-data`.

### Interface
- AMQP on `${RABBITMQ_PORT}:5672`.
- RabbitMQ management UI on `${RABBITMQ_MANAGEMENT_PORT}:15672`.
