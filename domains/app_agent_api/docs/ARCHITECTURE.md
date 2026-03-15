# Agent API Architecture

This domain exposes the `agent_platform` MVP over HTTP without duplicating
orchestration logic. Routes translate HTTP requests into calls on the
`AgentPlatformServiceFactory` service graph.

Deployment shape:
- long-running containerized HTTP service
- managed through `./stack.sh up app_agent_api`
- depends on `libs/agent_platform` and `libs/ai_infra`
- consumes the repo workspace through a bind mount at `/workspace`
