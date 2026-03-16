# Agent Platform Architecture

This library provides the MVP composition root, local adapters, and CLI for the
capability-oriented agent platform defined in `plan_tasks.md`.

It now also owns the reusable backend implementation for retrieval-grounded
responses:

- `agent_platform.agent_runtime`: objective execution/runtime orchestration
- `agent_platform.clients.llm`: Ollama-compatible HTTP client code
- `agent_platform.gateways.retrieval`: Weaviate-backed retrieval adapters
- `agent_platform.grounded_response`: message validation, grounding, citation
  shaping, and response orchestration
- `agent_platform.startup`: config extraction and service wiring

Runtime path handling is centralized in startup and shared workspace-bound path
validation, while packaged prompts/capability metadata continue to load through
package resources rather than repo-relative file paths.

This package is library code, not a deployable service. The long-running HTTP
backend remains `domains/agent_api`, which should import and expose these
services rather than reimplement them. The CLI entrypoint now lives in
`domains/agent_cli`, keeping executable adapters out of the library package.
