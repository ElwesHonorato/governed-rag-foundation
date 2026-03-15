# AI Backend Architecture

This domain exposes the `agent_platform` MVP over HTTP without duplicating
orchestration logic. Routes translate HTTP requests into calls on the
`AgentPlatformServiceFactory` service graph.

Current responsibilities:
- expose generic agent-runtime endpoints such as runs and evaluations
- expose the retrieval-grounded backend endpoint used by the RAG UI flow
- remain a thin transport layer over `agent_platform`

Deployment shape:
- long-running containerized HTTP service
- managed through `./stack.sh up ai_backend`
- depends on `libs/agent_platform` and `libs/ai_infra`
- consumes the repo workspace through a bind mount at `/workspace`
- configured through `.env` values documented in `.env.example`
