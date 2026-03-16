# Agent API Architecture

This domain exposes the `agent_platform` MVP over HTTP without duplicating
orchestration logic. Routes translate HTTP requests into calls on the
`EngineFactory` service graph.

Current responsibilities:
- expose generic agent-runtime endpoints such as runs and evaluations
- expose the grounded-response endpoint used by the UI flow
- remain a thin transport layer over `agent_platform`

Key runtime wiring:
- `src/agent_api/app.py` is the process startup entrypoint and assembles runtime inputs, including the `agent_platform` engine graph.
- `src/agent_api/engine_factory.py` is the backend-facing boundary for agent-platform engine construction.
- `src/agent_api/adapters/http/web_application_factory.py` contains the class-based composition root for HTTP adapter wiring.
- `src/agent_api/adapters/http/application.py` handles the WSGI application boundary and takes prebuilt collaborators.
- `src/agent_api/adapters/http/request_normalization.py` handles WSGI request normalization.
- `../../libs/agent/settings/src/agent_settings/settings` loads backend runtime settings via a shared settings provider pattern.

Deployment shape:
- long-running containerized HTTP service
- managed through `./stack.sh up agent_api`
- depends on `libs/agent/platform` and `libs/agent/core`
- consumes the repo workspace through a bind mount at `/workspace`
- configured through `.env` values documented in `.env.example`
