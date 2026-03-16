# AI UI To AI Backend Migration Plan

## Decision

Adopt this target architecture:

- `domains/ai_ui` becomes the UI-only application shell.
- `domains/ai_backend` becomes the long-running backend service for RAG and agent operations.
- `libs/agent/platform` owns reusable backend logic:
  - LLM gateway/client code
  - vector retrieval code
  - RAG orchestration services
  - agent runtime orchestration

Do not create a second long-running service for `agent_platform`. Keep it as a library package and let `ai_backend` remain the only backend container in this area.

## Why

Current state is split incorrectly for the intended future:

- `ai_ui` currently owns UI, request normalization, retrieval, and LLM orchestration.
- `ai_backend` currently owns only generic agent-run transport.
- `agent_platform` does not yet own the RAG backend behavior that should be reusable.

That shape causes three problems:

1. The product UI app contains backend logic that should be reusable elsewhere.
2. The backend service does not yet expose the product-facing RAG contract the UI actually needs.
3. Retrieval and LLM infrastructure are trapped inside `ai_ui` instead of living in the shared runtime package.

## Current Findings

### `ai_ui` is still a vertical app

- `[routes.py](/home/sultan/repos/governed-rag-foundation/domains/ai_ui/src/ai_ui/routes.py)` constructs `RetrievalClient` and `PromptService` directly inside the Flask route layer.
- `[prompt_service.py](/home/sultan/repos/governed-rag-foundation/domains/ai_ui/src/ai_ui/services/prompt_service.py)` owns:
  - request normalization
  - latest-user-query extraction
  - retrieval grounding
  - citation shaping
  - LLM chat invocation
- `[retrieval_client.py](/home/sultan/repos/governed-rag-foundation/domains/ai_ui/src/ai_ui/retrieval_client.py)` owns Weaviate access.
- `[llm_client.py](/home/sultan/repos/governed-rag-foundation/domains/ai_ui/src/ai_ui/llm_client.py)` owns Ollama HTTP access.

This means `ai_ui` is not a UI shell. It is currently the real backend.

### `ai_backend` is not yet the product backend

- `[routes.py](/home/sultan/repos/governed-rag-foundation/domains/ai_backend/src/ai_backend/routes.py)` exposes generic endpoints such as `/capabilities`, `/skills`, `/runs`, and `/evaluations`.
- It does not expose a RAG query endpoint for the existing UI flow.
- It does not currently own Weaviate-backed retrieval behavior.

So `ai_backend` is deployable, but not yet the backend that `ai_ui` can depend on for its main product flow.

### `ai_ui` contains policy drift

- `[prompt_service.py](/home/sultan/repos/governed-rag-foundation/domains/ai_ui/src/ai_ui/services/prompt_service.py)` still contains a backward-compatibility branch for old `prompt` clients.

That conflicts with the repo rule in `AGENTS.md`: no backward compatibility unless explicitly requested.

## Target Architecture

### `libs/agent/platform`

This package becomes the reusable backend implementation. Add or formalize these areas:

- `agent_platform.llm`
  - HTTP gateway/client for the configured LLM backend
  - request/response validation
  - retry and error mapping
- `agent_platform.retrieval`
  - vector search gateway
  - retrieval query building
  - chunk/result parsing
- `agent_platform.rag`
  - input contract validation
  - context assembly
  - citation shaping
  - response generation orchestration
- `agent_platform.startup`
  - wiring for config, adapters, and services

This code must be backend-only and transport-agnostic. No Flask route logic, template logic, or UI behavior belongs here.

### `domains/ai_backend`

This remains the single long-running backend service and exposes two backend families:

- generic agent-runtime endpoints
- product-facing RAG endpoints

Add a dedicated RAG API surface, for example:

- `POST /rag/query`
- optional later:
  - `POST /rag/chat`
  - `GET /rag/health`

`ai_backend` should translate HTTP into library calls and nothing more. It should not absorb retrieval or prompt logic directly into its route layer.

### `domains/ai_ui`

This becomes the UI shell:

- render the UI
- accept browser/user input
- call `ai_backend` over HTTP
- present backend responses

After migration it should no longer:

- talk directly to Weaviate
- talk directly to Ollama
- own prompt orchestration logic
- own retrieval grounding logic

If that leaves it as mostly templates plus a small HTTP client, that is correct.

## Required Contract

Define one canonical backend contract for the existing RAG flow.

Recommended request:

```json
{
  "messages": [
    {"role": "user", "content": "What is this repository about?"}
  ]
}
```

Recommended response:

```json
{
  "model": "llama3.2",
  "response": "Repository summary...",
  "assistant_message": {
    "role": "assistant",
    "content": "Repository summary..."
  },
  "citations": [
    {
      "source_uri": "s3a://bucket/example.html",
      "doc_id": "doc-1",
      "chunk_id": "chunk-9",
      "quote": "Quoted text...",
      "distance": 0.12
    }
  ]
}
```

Do not preserve the old `prompt` fallback request shape. Cut over the UI and fail fast on invalid payloads.

## Migration Phases

### Phase 1: Extract backend logic into `agent_platform`

Move or rewrite these responsibilities inside `libs/agent/platform`:

- from `[llm_client.py](/home/sultan/repos/governed-rag-foundation/domains/ai_ui/src/ai_ui/llm_client.py)` into `agent_platform.llm`
- from `[retrieval_client.py](/home/sultan/repos/governed-rag-foundation/domains/ai_ui/src/ai_ui/retrieval_client.py)` into `agent_platform.retrieval`
- from `[prompt_service.py](/home/sultan/repos/governed-rag-foundation/domains/ai_ui/src/ai_ui/services/prompt_service.py)` into `agent_platform.rag`

Required rules:

- keep transport-independent interfaces
- keep explicit typed contracts where possible
- do not keep Flask-specific response tuples in library code
- remove backward-compatibility fallback for `prompt`

Expected result:

- `agent_platform` can execute the current UI-originated retrieval flow without importing `ai_ui`

### Phase 2: Extend `ai_backend` with RAG endpoints

Add a backend route that delegates into the new `agent_platform.rag` service.

Required work:

- extend `[routes.py](/home/sultan/repos/governed-rag-foundation/domains/ai_backend/src/ai_backend/routes.py)`
- extend `[config.py](/home/sultan/repos/governed-rag-foundation/domains/ai_backend/src/ai_backend/config.py)` if needed
- extend service startup/wiring to include the new RAG service

Required config adoption:

- `LLM_URL`
- `LLM_MODEL`
- `LLM_TIMEOUT_SECONDS`
- `WEAVIATE_URL`
- `EMBEDDING_DIM`
- `WEAVIATE_QUERY_DEFAULTS_LIMIT`

Those should move into `agent_platform` config extraction, then be consumed by `ai_backend`.

Expected result:

- `ai_backend` can serve the same prompt/chat behavior currently implemented by `ai_ui`

### Phase 3: Convert `ai_ui` into a UI client

Replace direct backend wiring in `[routes.py](/home/sultan/repos/governed-rag-foundation/domains/ai_ui/src/ai_ui/routes.py)`.

Delete from `ai_ui`:

- direct construction of `RetrievalClient`
- direct construction of `PromptService`
- direct `OllamaClient` usage for the main RAG flow

Add instead:

- a small HTTP client to `ai_backend`
- request/response mapping for the UI

Keep in `ai_ui`:

- Flask app bootstrap
- templates
- UI asset handling
- product presentation concerns

Expected result:

- `ai_ui` is now a frontend shell over `ai_backend`

### Phase 4: Delete obsolete backend code from `ai_ui`

Once the UI is cut over, remove:

- `[llm_client.py](/home/sultan/repos/governed-rag-foundation/domains/ai_ui/src/ai_ui/llm_client.py)`
- `[retrieval_client.py](/home/sultan/repos/governed-rag-foundation/domains/ai_ui/src/ai_ui/retrieval_client.py)`
- `[services/prompt_service.py](/home/sultan/repos/governed-rag-foundation/domains/ai_ui/src/ai_ui/services/prompt_service.py)`

Also simplify `[config.py](/home/sultan/repos/governed-rag-foundation/domains/ai_ui/src/ai_ui/config.py)` so it only contains frontend/UI-service settings plus the backend URL for `ai_backend`.

Expected result:

- there is only one backend implementation path for RAG

## Operational Model

Keep the runtime model simple:

- `ai_backend` runs as the backend container under `stack.sh`
- `ai_ui` runs as the UI container under `stack.sh`
- `agent_platform` remains a library package with no separate container

That gives one frontend service and one backend service, not two backends with overlapping logic.

## Config Model

### Backend-owned config

These belong to the backend side and should be consumed by `agent_platform` via `ai_backend`:

- `LLM_URL`
- `LLM_MODEL`
- `LLM_TIMEOUT_SECONDS`
- `WEAVIATE_URL`
- `EMBEDDING_DIM`
- `WEAVIATE_QUERY_DEFAULTS_LIMIT`

### Frontend-owned config

`ai_ui` should eventually need only:

- `AI_BACKEND_URL` or equivalent backend base URL
- UI-specific settings if any

It should no longer need direct vector DB or LLM credentials/settings.

## Risks

1. `ai_backend` may become a dumping ground.

Do not solve this by moving prompt logic into HTTP routes. Keep `ai_backend` thin and move logic into `agent_platform`.

2. `agent_platform` may become too generic too early.

Do not over-abstract the first extraction. First reproduce the existing RAG flow cleanly. Generalize only after the move works.

3. The UI contract may drift during migration.

Lock the request/response schema first, then migrate against that explicit contract.

4. Hidden backward compatibility may survive.

Remove the old `prompt` fallback and update callers in one cut. Do not carry dual request formats.

## Definition Of Done

The migration is complete only when all of the following are true:

- `ai_ui` no longer imports or constructs LLM or retrieval clients for the main chat flow
- `ai_ui` no longer contains prompt orchestration logic
- `ai_backend` exposes a stable RAG endpoint used by `ai_ui`
- `agent_platform` owns reusable LLM, retrieval, and RAG orchestration code
- backend infra config is owned by `ai_backend` and `agent_platform`, not by the UI shell
- old `prompt` compatibility fallback is removed
- docs and stack instructions reflect the new boundary

## Recommended Execution Order

1. Extract LLM and retrieval adapters into `agent_platform`
2. Extract prompt orchestration into `agent_platform.rag`
3. Add `POST /rag/query` to `ai_backend`
4. Cut `ai_ui` over to HTTP calls into `ai_backend`
5. Delete old backend code from `ai_ui`
6. Update docs and stack env contracts

## Non-Goals

Do not do these in the same change unless they are independently required:

- replacing Flask in `ai_ui`
- replacing the WSGI stack in `ai_backend`
- inventing a second backend service for `agent_platform`
- preserving old request payload formats
