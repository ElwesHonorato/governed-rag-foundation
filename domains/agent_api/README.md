# Agent API

Thin HTTP API domain for the `agent_platform` runtime.

Local stack path:

```bash
./stack.sh up agent_api --build
./stack.sh logs agent_api
```

Required environment:

- `AGENT_API_HOST`
- `AGENT_API_PORT`
- `AGENT_PLATFORM_WORKSPACE_ROOT` (container default `/workspace`)
- `LLM_URL`
- `LLM_MODEL`
- `LLM_TIMEOUT_SECONDS`
- `WEAVIATE_URL`
- `EMBEDDING_DIM`
- `WEAVIATE_QUERY_DEFAULTS_LIMIT` (optional, defaults to `5`)
- `STACK_NETWORK` for the shared Docker network

Local env template:

- Copy `.env.example` to `.env` and adjust values for your stack.

Container runtime contract:

- the repo is mounted at `/workspace`
- `AGENT_PLATFORM_WORKSPACE_ROOT=/workspace`
- the API listens on `${AGENT_API_HOST}:${AGENT_API_PORT}`

Primary endpoints:

- `GET /`
- `GET /capabilities`
- `GET /skills`
- `POST /runs`
- `POST /evaluations`
- `POST /grounded-response/query`

`POST /grounded-response/query` request body:

```json
{
  "messages": [
    {"role": "user", "content": "What is this repository about?"}
  ]
}
```
