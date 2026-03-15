# Agent API Architecture

This domain exposes the `agent_platform` MVP over HTTP without duplicating
orchestration logic. Routes translate HTTP requests into calls on the
`AgentPlatformServiceFactory` service graph.
