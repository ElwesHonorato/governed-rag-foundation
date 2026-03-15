# Agent API

Thin HTTP API domain for the `agent_platform` runtime.

Local stack path:

```bash
./stack.sh up app_agent_api --build
./stack.sh logs app_agent_api
```

Required environment:

- `LLM_URL`
- `LLM_MODEL`
- `LLM_TIMEOUT_SECONDS`

Container runtime contract:

- the repo is mounted at `/workspace`
- `AGENT_PLATFORM_WORKSPACE_ROOT=/workspace`
- the API listens on `0.0.0.0:${AGENT_API_PORT:-8010}`
