# Local Stack Scripts

These scripts centralize local infrastructure lifecycle for development and testing so services can be started consistently as one stack or by domain.

## Usage

```bash
./stack.sh up
./stack.sh down
./stack.sh wipe
./stack.sh up storage
./stack.sh up vector
./stack.sh up llm
./stack.sh logs lineage
./stack.sh ps
./stack.sh ps app
```

## Domain-by-domain start

```bash
./stack.sh up storage
./stack.sh up vector
./stack.sh up lineage
./stack.sh up queue
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

All domains join the shared external Docker network `rag-local`, so services resolve each other by container service name when started independently.
The `llm` domain builds a custom Ollama image and bakes `LLM_MODEL` (defaults to `llama3.2:1b`) during image build.

## Local endpoints

- MinIO console: http://localhost:9001
- Weaviate: http://localhost:8080
- Marquez API: http://localhost:5000
- Marquez UI: http://localhost:3000
- Ollama API: http://localhost:11434
- rag-api: http://localhost:8000
