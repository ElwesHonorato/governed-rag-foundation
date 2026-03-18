# Agent API Architecture

This domain exposes the `agent_platform` MVP over HTTP without duplicating
orchestration logic. Routes translate HTTP requests into calls on the
grounded-response runtime graph.

Current responsibilities:
- expose the grounded-response endpoint used by the UI flow
- remain a thin transport layer over the grounded-response runtime

Key runtime wiring:
- `src/agent_api/app.py` is the process startup entrypoint and assembles runtime inputs, including the grounded-response runtime graph.
- `src/agent_api/adapters/http/grounded_response_http_handler.py` translates HTTP requests into grounded-response service calls.
- `src/agent_api/adapters/http/application.py` handles the WSGI application boundary and takes prebuilt collaborators.
- `src/agent_api/adapters/http/router.py` dispatches the supported HTTP routes.
- `src/agent_api/adapters/http/request_normalization.py` handles WSGI request normalization.
- `../../libs/agent/settings/src/agent_settings/settings.py` provides the shared environment-backed settings bundle used by the domain composition root.

Deployment shape:
- long-running containerized HTTP service
- managed through `./stack.sh up agent_api`
- depends on `libs/agent/platform` and `libs/agent/core`
- configured through `.env` values documented in `.env.example`
