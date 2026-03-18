# Local Stack Operations

These scripts centralize local infrastructure lifecycle for development and testing so services can be started consistently as one stack or by domain.

## Usage

```bash
./stack.sh up
./stack.sh down
./stack.sh wipe
./stack.sh up infra_storage
./stack.sh up infra_vector
./stack.sh up infra_llm
./stack.sh logs infra_lineage
./stack.sh ps
./stack.sh ps ai_ui
```

## Domain-by-domain start

```bash
./stack.sh up infra_storage
./stack.sh up infra_vector
./stack.sh up infra_lineage
./stack.sh up infra_portainer
./stack.sh up infra_queue
./stack.sh up infra_llm
./stack.sh up agent_api
./stack.sh up ai_ui
./stack.sh up app_vector_ui
./stack.sh up worker_scan
./stack.sh up worker_parse_document
./stack.sh up worker_chunk_text
./stack.sh up worker_embed_chunks
./stack.sh up worker_index_weaviate
```

All domains join the shared external Docker network `rag-local`, so services resolve each other by container service name when started independently.
The `infra_llm` domain builds a custom Ollama image and bakes `LLM_MODEL` (defaults to `llama3.2:1b`) during image build.

## Local endpoints

- MinIO console: http://localhost:9001
- Weaviate: http://localhost:8080
- DataHub GMS: http://localhost:${DATAHUB_MAPPED_GMS_PORT}
- DataHub frontend: http://localhost:${DATAHUB_MAPPED_FRONTEND_PORT}
- Portainer: https://localhost:${PORTAINER_HTTPS_PORT}
- Ollama API: http://localhost:11434
- agent-api: http://localhost:${AGENT_API_PORT}
- ai-ui: http://localhost:8000
- vector-ui: http://localhost:${VECTOR_UI_PORT:-8010}
