# Agent Platform Architecture

This library provides the MVP composition root, local adapters, and CLI for the
capability-oriented agent platform defined in `plan_tasks.md`.

It now also owns the reusable backend implementation for retrieval-grounded
responses:

- `agent_platform.clients.llm`: Ollama-compatible HTTP client code
- `agent_platform.gateways.retrieval`: Weaviate-backed retrieval adapters
- `agent_platform.rag`: message validation, grounding, citation shaping, and
  response orchestration
- `agent_platform.startup`: config extraction and service wiring

This package is library code, not a deployable service. The long-running HTTP
backend remains `domains/ai_backend`, which should import and expose these
services rather than reimplement them.
