# ai_ui domain

This domain is the UI/front-door of the AI system. It receives browser or client requests and forwards prompt execution to `ai_backend`.

## Deep Dive

### What runs here
- `ai-ui` (Flask app from `domains/ai_ui`)

### How it contributes to RAG
- Accepts prompt requests from clients.
- Forwards prompt execution to `ai_backend`.
- Returns the backend response to the caller.

### Runtime dependencies
- `AI_BACKEND_URL` for the backend service.
- `AI_BACKEND_TIMEOUT_SECONDS` (optional, defaults to `30`).

### Interface
- Exposes HTTP on `${AI_UI_PORT}:8000`.
- Joins shared external network `${STACK_NETWORK}`.
