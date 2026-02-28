# Governed RAG Foundation

Reference repository for a locally runnable, governed RAG stack.

Runtime configuration is centralized in `.env` at the repository root.
Core infrastructure image tags are hardcoded in the domain compose files.

## Repository Layout

- `domains/app_rag_api`: API service for RAG operations.
- `libs/pipeline-common`: Shared pipeline helpers used by isolated worker domains.
- `domains/`: Docker Compose definitions split by domain:
  - `infra_storage` (MinIO)
  - `infra_vector` (Weaviate)
  - `infra_queue` (RabbitMQ broker)
  - `infra_lineage` (DataHub quickstart)
  - `infra_portainer` (Docker container UI)
  - `infra_llm` (Ollama)
  - `app_rag_api` (rag-api only)
  - `app_vector_ui` (standalone Weaviate query UI)
  - `worker_scan`
  - `worker_parse_document`
  - `worker_chunk_text`
  - `worker_embed_chunks`
  - `worker_index_weaviate`
  - `worker_manifest`
  - `worker_metrics`
- `tooling/ops/`: Shared stack lifecycle helpers used by `stack.sh`.
- `stack.sh`: Entry point for bringing the local stack up/down.

## Development Strategy

This repository follows a modular monorepo approach during the solo development phase:

- Each domain is treated as an independently deployable unit.
- Domains are kept together in one repo to reduce coordination overhead and speed up iteration.
- The target future state is polyrepo: each domain can be split into its own repository.

To keep that future split low-risk, current changes should preserve clear boundaries:

- No direct cross-domain Python imports.
- Shared logic lives in `libs/pipeline-common`.
- Domain-local runtime wiring stays inside each domain.
- Domain contracts/config keys stay explicit and versionable.

## Requirements Tracking

- Requirements workspace: `docs/requirements/README.md`
- Coverage roadmap (canonical): `docs/requirements/00-overview/requirements-coverage-roadmap.md`

## Getting Started

Recommended first-run order from repository root:

```bash
./stack.sh up infra_storage
./stack.sh up infra_vector
./stack.sh up infra_queue
./stack.sh up infra_lineage
./stack.sh up infra_portainer
./stack.sh up infra_llm
./stack.sh up app_rag_api
./stack.sh up app_vector_ui
./stack.sh up worker_scan
./stack.sh up worker_parse_document
./stack.sh up worker_chunk_text
./stack.sh up worker_embed_chunks
./stack.sh up worker_index_weaviate
./stack.sh up worker_manifest
./stack.sh up worker_metrics
```

Then check status/logs:

```bash
./stack.sh ps
./stack.sh logs app_rag_api
```

## Local Stack Commands

Run from repository root:

```bash
./stack.sh up                 # start all domains
./stack.sh up <domain>        # start one domain, e.g. infra_storage or worker_scan
./stack.sh down               # stop running domains
./stack.sh wipe               # stop stack and remove volumes
./stack.sh logs <domain>      # follow one domain logs
./stack.sh ps                 # show stack status
```

When finished:

```bash
./stack.sh down
```

## Local Endpoints

- MinIO Console: `http://localhost:9001`
- Weaviate: `http://localhost:8080`
- RabbitMQ Management UI: `http://localhost:15672`
- DataHub GMS: value of `DATAHUB_GMS_URL`
- DataHub frontend: `http://localhost:${DATAHUB_MAPPED_FRONTEND_PORT}`
- Portainer: `https://localhost:9443`
- Ollama API: `http://localhost:11434`
- rag-api: `http://localhost:8000`
- vector-ui: `http://localhost:8010`

## Lineage Guide

- `./stack.sh up infra_lineage` runs DataHub quickstart services from `domains/infra_lineage/docker-compose.yml`.
- Workers emit runtime lineage to DataHub GMS via `DATAHUB_GMS_SERVER` and `DATAHUB_ENV`.
- Legacy `make lineage-*` tooling has been removed from this repository.

## Python Dependencies (Poetry)

Python projects in this repository are managed independently with Poetry (one `pyproject.toml` per app/lib/worker).

Projects include:
- `domains/app_rag_api`
- `libs/pipeline-common`
- `domains/worker_*`

Typical workflow (run inside the project directory you are working on):

```bash
cd <project-dir>
poetry install
```

Run project commands through Poetry:

```bash
poetry run <command>
```

Update lock files only when dependencies change:

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
- Start domains independently or as a full stack, depending on what you are developing.
- `domains/infra_llm` builds a custom Ollama image and bakes `LLM_MODEL` (default: `llama3.2:1b`) at build time.
- To build with a different model:
  - `LLM_MODEL=<your-model> ./stack.sh up infra_llm`
