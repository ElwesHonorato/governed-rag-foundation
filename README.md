# Governed RAG Foundation

Reference repository for a locally runnable, governed RAG stack.

Runtime configuration is centralized in `.env` at the repository root.
Core infrastructure image tags and the shared Docker network are hardcoded in the domain compose files.

## Repository Layout

- `apps/rag-api`: API service for RAG operations.
- `libs/pipeline-common`: Shared pipeline helpers used by isolated worker domains.
- `domains/`: Docker Compose definitions split by domain:
  - `storage` (MinIO)
  - `vector` (Weaviate)
  - `queue` (RabbitMQ broker)
  - `lineage` (Marquez)
  - `llm` (Ollama)
  - `app` (rag-api only)
  - `worker_scan`
  - `worker_parse_document`
  - `worker_chunk_text`
  - `worker_embed_chunks`
  - `worker_index_weaviate`
  - `worker_manifest`
  - `worker_metrics`
- `scripts/`: Shared shell helpers used by `stack.sh`.
- `stack.sh`: Entry point for bringing the local stack up/down.

## Requirements Tracking

- Requirements workspace: `requirements/README.md`
- Coverage roadmap (canonical): `requirements/00-overview/requirements-coverage-roadmap.md`

## Local Stack Commands

Run from repository root:

```bash
./stack.sh up
./stack.sh down
./stack.sh wipe
./stack.sh up storage
./stack.sh up vector
./stack.sh up queue
./stack.sh up lineage
./stack.sh up llm
./stack.sh up app
./stack.sh up worker_scan
./stack.sh up worker_parse_document
./stack.sh logs worker_scan
./stack.sh ps
```

## Getting Started

Recommended first-run order from repository root:

```bash
./stack.sh up storage
./stack.sh up vector
./stack.sh up queue
./stack.sh up lineage
./stack.sh up llm
./stack.sh up app
./stack.sh up worker_scan
./stack.sh up worker_parse_document
./stack.sh up worker_chunk_text
./stack.sh up worker_embed_chunks
./stack.sh up worker_index_weaviate
./stack.sh up worker_manifest
./stack.sh up worker_metrics
```

Quick checks:

```bash
./stack.sh ps
./stack.sh logs app
```

When finished:

```bash
./stack.sh down
```

## Local Endpoints

- MinIO Console: `http://localhost:9001`
- Weaviate: `http://localhost:8080`
- RabbitMQ Management UI: `http://localhost:15672`
- Marquez API: `http://localhost:5000`
- Marquez UI: `http://localhost:3000`
- Ollama API: `http://localhost:11434`
- rag-api: `http://localhost:8000`

## Python Dependencies (Poetry)

Python app domains use Poetry with project-local virtual environments (`.venv`) via `poetry.toml`.

- `apps/rag-api`

Typical workflow:

```bash
cd apps/rag-api
poetry install
```

If lock files need updates:

```bash
poetry lock
```

## Notes

- Domain compose files join the shared external Docker network `rag-local`.
- Hardcoded infrastructure images:
  - MinIO: `minio/minio:latest`
  - Weaviate: `cr.weaviate.io/semitechnologies/weaviate:1.27.7`
  - RabbitMQ: `rabbitmq:3-management-alpine`
  - Postgres: `postgres:15-alpine`
  - Marquez API: `marquezproject/marquez:latest`
  - Marquez Web: `marquezproject/marquez-web:latest`
- Start domains independently or as a full stack, depending on what you are developing.
- `domains/llm` builds a custom Ollama image and bakes `LLM_MODEL` (default: `llama3.2:1b`) at build time.
- To build with a different model:
  - `LLM_MODEL=<your-model> ./stack.sh up llm`
