# Agent Platform MVP Testing

This guide translates the validation section of `plan_tasks.md` into concrete commands you can run from the repository root.

The production-grade path is now:
- install the local packages with Poetry
- run the installed console scripts

Example setup:

```bash
cd libs/agent/platform && POETRY_VIRTUALENVS_IN_PROJECT=true poetry install
cd /home/sultan/repos/governed-rag-foundation/domains/ai_backend && POETRY_VIRTUALENVS_IN_PROJECT=true poetry install
```

## Baseline Sanity Check

```bash
python3 -m compileall libs domains
```

## CLI Smoke Checks

List registered capabilities:

```bash
cd libs/agent/platform
./.venv/bin/agent-platform capability-list
```

List registered skills:

```bash
cd libs/agent/platform
./.venv/bin/agent-platform skill-list
```

Run the default `analyze_repository` skill:

```bash
cd libs/agent/platform
AGENT_PLATFORM_WORKSPACE_ROOT=/home/sultan/repos/governed-rag-foundation ./.venv/bin/agent-platform run "review this repository structure"
```

This should create session and run artifacts under `/home/sultan/repos/governed-rag-foundation/.agent_platform/localdata` by default when `AGENT_PLATFORM_WORKSPACE_ROOT` is set to the repo root.

## Inspect Stored State

After a run completes, copy the `session_id` and `run_id` from the JSON output.

Inspect the saved session:

```bash
cd libs/agent/platform
./.venv/bin/agent-platform session-show <session_id>
```

Evaluate the saved run:

```bash
cd libs/agent/platform
./.venv/bin/agent-platform eval-run <run_id>
```

## MVP Scenario Checks

### `analyze_repository`

```bash
cd libs/agent/platform
AGENT_PLATFORM_WORKSPACE_ROOT=/home/sultan/repos/governed-rag-foundation ./.venv/bin/agent-platform run "review this repository structure"
```

Verify that the result includes:
- `command_run_safe` output from `git status --short`
- `filesystem_read` output from `plan_tasks.md`
- `vector_search` hits from the local fixture
- `llm_synthesize` final output

### `summarize_document`

This skill expects `task.md` at the repository root.

```bash
cd libs/agent/platform
AGENT_PLATFORM_WORKSPACE_ROOT=/home/sultan/repos/governed-rag-foundation ./.venv/bin/agent-platform run "summarize task.md" --skill summarize_document
```

### Offline Evaluation

```bash
cd libs/agent/platform
./.venv/bin/agent-platform eval-run <run_id>
```

## HTTP API Checks

Start the API server:

```bash
cd domains/ai_backend
AGENT_PLATFORM_WORKSPACE_ROOT=/home/sultan/repos/governed-rag-foundation ./.venv/bin/ai-backend
```

Then, in another terminal, exercise the endpoints:

Get capabilities:

```bash
curl -s http://127.0.0.1:8010/capabilities
```

Get skills:

```bash
curl -s http://127.0.0.1:8010/skills
```

Create a run:

```bash
curl -s \
  -H 'Content-Type: application/json' \
  -d '{"objective":"review this repo","skill_name":"analyze_repository"}' \
  http://127.0.0.1:8010/runs
```

Evaluate a run:

```bash
curl -s \
  -H 'Content-Type: application/json' \
  -d '{"run_id":"<run_id>"}' \
  http://127.0.0.1:8010/evaluations
```

## Negative-Path Checks

These verify the hardening added after review.

Out-of-workspace command paths should be rejected:

```bash
PYTHONPATH=./libs/agent/core/src python3 -c 'from ai_infra.policies.sandbox_policy import SandboxPolicy; policy = SandboxPolicy("."); policy.validate_command(["ls", "/etc"])'
```

This should raise a `ValueError`.

Non-zero command execution should produce a failed capability result:

```bash
PYTHONPATH=./libs/agent/core/src:./libs/agent/platform/src python3 -c 'from ai_infra.services.capability_execution_service import CapabilityExecutionService; from ai_infra.services.prompt_assembly_service import PromptAssemblyService; from ai_infra.contracts.capability_request import CapabilityRequest; from ai_infra.contracts.agent_run import AgentRun; from ai_infra.contracts.execution_plan import ExecutionPlan; from agent_platform.gateways.filesystem.local_filesystem_gateway import LocalFilesystemGateway; from agent_platform.gateways.command.local_command_gateway import LocalCommandGateway; from agent_platform.gateways.retrieval.local_vector_search import LocalVectorSearch; from agent_platform.infrastructure.local_embedding_fixture import DeterministicEmbeddingFixture; from agent_platform.gateways.prompts.local_prompt_repository import LocalPromptRepository; DummyModelGateway = type(\"DummyModelGateway\", (), {\"synthesize\": lambda self, prompt, context: \"unused\"}); service = CapabilityExecutionService(LocalFilesystemGateway(\".\"), LocalCommandGateway(\".\"), LocalVectorSearch(\".agent_platform/localdata/vector_fixture/index.json\", DeterministicEmbeddingFixture()), DummyModelGateway(), PromptAssemblyService(LocalPromptRepository())); run = AgentRun(run_id=\"run-1\", session_id=\"session-1\", skill_name=\"analyze_repository\", objective=\"obj\", status=\"running\", prompt_version=\"v1\", execution_plan=ExecutionPlan(skill_name=\"analyze_repository\", objective=\"obj\", steps=())); result = service.execute(CapabilityRequest(capability_name=\"command_run_safe\", session_id=\"session-1\", run_id=\"run-1\", step_id=\"step-1\", input_payload={\"command\": [\"rg\", \"definitely-no-match-pattern\", \"docs/ARCHITECTURE.md\"]}), run); print(result.success); print(result.error_message)'
```

Expected output:
- `False`
- an error message including `Command exited with code 1`

## Current Gaps

- The plan mentions resumed runs from checkpoints, but there is no resume CLI command yet.
- The default skills depend on `plan_tasks.md` and `task.md` existing at the repository root.
