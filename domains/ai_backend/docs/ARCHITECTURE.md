# AI Backend Architecture

This domain exposes the `agent_platform` MVP over HTTP without duplicating
orchestration logic. Routes translate HTTP requests into calls on the
`EngineFactory` service graph.

Current responsibilities:
- expose generic agent-runtime endpoints such as runs and evaluations
- expose the retrieval-grounded backend endpoint used by the RAG UI flow
- remain a thin transport layer over `agent_platform`

Key runtime wiring:
- `src/ai_backend/app.py` is the process startup entrypoint and assembles runtime inputs, including the `agent_platform` engine graph.
- `src/ai_backend/engine_factory.py` is the backend-facing boundary for agent-platform engine construction.
- `src/ai_backend/adapters/http/web_application_factory.py` contains the class-based composition root for HTTP adapter wiring.
- `src/ai_backend/adapters/http/application.py` handles the WSGI application boundary and takes prebuilt collaborators.
- `src/ai_backend/adapters/http/request_normalization.py` handles WSGI request normalization.
- `../../libs/runtime/src/runtime/provider.py` loads backend runtime settings via a shared settings provider pattern.

Deployment shape:
- long-running containerized HTTP service
- managed through `./stack.sh up ai_backend`
- depends on `libs/agent_platform` and `libs/ai_infra`
- consumes the repo workspace through a bind mount at `/workspace`
- configured through `.env` values documented in `.env.example`
