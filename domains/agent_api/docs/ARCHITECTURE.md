# Agent API Architecture

This domain exposes the `agent_platform` MVP over HTTP without duplicating
orchestration logic. Routes translate HTTP requests into calls on the
grounded-response runtime graph.

Current responsibilities:
- expose the grounded-response endpoint used by the UI flow
- remain a thin transport layer over the grounded-response runtime

Key runtime wiring:
- `src/agent_api/app.py` is the process startup entrypoint and assembles runtime inputs, including the grounded-response runtime graph.
- `src/agent_api/startup/engine_factory.py` is the backend-facing boundary for API runtime construction.
- `src/agent_api/adapters/http/web_application_factory.py` contains the class-based composition root for HTTP adapter wiring.
- `src/agent_api/adapters/http/application.py` handles the WSGI application boundary and takes prebuilt collaborators.
- `src/agent_api/adapters/http/request_normalization.py` handles WSGI request normalization.
- `src/agent_api/settings.py` owns the domain's concrete HTTP settings model and environment-backed provider.
- `../../libs/agent/settings/src/agent_settings/settings/settings_provider.py` provides the shared `SettingsProvider` abstraction used by the domain composition root.

Deployment shape:
- long-running containerized HTTP service
- managed through `./stack.sh up agent_api`
- depends on `libs/agent/platform` and `libs/agent/core`
- configured through `.env` values documented in `.env.example`
