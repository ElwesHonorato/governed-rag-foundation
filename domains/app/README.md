# app domain

This domain is the main front door of the RAG system. If you ask a question, `rag-api` is the service that receives it, coordinates retrieval and generation, and returns the answer.

## Deep Dive

### What runs here
- `rag-api` (Flask app from `apps/rag-api`)

### How it contributes to RAG
- Accepts prompt requests from clients.
- Retrieves relevant chunks from Weaviate.
- Builds grounded prompts with context and citations.
- Calls the LLM and returns answer + citation payload.

### Runtime dependencies
- `WEAVIATE_URL` for retrieval.
- `BROKER_URL` for queue integration points.
- `S3_ENDPOINT`, `S3_ACCESS_KEY`, `S3_SECRET_KEY` for artifact access.
- `DATAHUB_GMS_URL`, `DATAHUB_OPENLINEAGE_URL`, `DATAHUB_TOKEN` for lineage integration.
- `LLM_URL`, `LLM_MODEL`, `LLM_TIMEOUT_SECONDS` for generation.
- `EMBEDDING_DIM`, `WEAVIATE_QUERY_DEFAULTS_LIMIT` for retrieval behavior.

### Interface
- Exposes HTTP on `${RAG_API_PORT}:8000`.
- Joins shared external network `${STACK_NETWORK}`.
