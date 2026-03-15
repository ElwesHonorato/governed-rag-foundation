# AI Backend

Thin HTTP backend domain for the `agent_platform` runtime.

Local stack path:

```bash
./stack.sh up ai_backend --build
./stack.sh logs ai_backend
```

Required environment:

- `LLM_URL`
- `LLM_MODEL`
- `LLM_TIMEOUT_SECONDS`
- `WEAVIATE_URL`
- `EMBEDDING_DIM`
- `WEAVIATE_QUERY_DEFAULTS_LIMIT` (optional, defaults to `5`)

Container runtime contract:

- the repo is mounted at `/workspace`
- `AGENT_PLATFORM_WORKSPACE_ROOT=/workspace`
- the API listens on `0.0.0.0:${AI_BACKEND_PORT:-8010}`

Primary endpoints:

- `GET /`
- `GET /capabilities`
- `GET /skills`
- `POST /runs`
- `POST /evaluations`
- `POST /rag/query`

`POST /rag/query` request body:

```json
{
  "messages": [
    {"role": "user", "content": "What is this repository about?"}
  ]
}
```
