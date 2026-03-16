# MVP-First Implementation Plan: Capability-Oriented Agent Platform

Source of truth:
- `task.md`
- repo constraints from `AGENTS.md`
- existing repo architecture in `docs/ARCHITECTURE.md`
- DI guidance in `docs/patterns/dependency-injection.md`

Objective:
- implement a portfolio-grade capability-oriented AI agent platform in Python
- keep the first delivery intentionally narrow, demonstrable, and aligned with existing repo patterns
- avoid architecture overgrowth by shipping one credible vertical slice before expanding platform breadth

## 1. Implementation stance

### 1.1 Repo-aligned placement
- Create a new deployable domain at `domains/agent_platform/` as the composition root and CLI surface.
- Create a new shared library at `libs/agent/core/` for reusable contracts, orchestration logic, policies, and gateway interfaces.
- Keep deployable wiring and concrete adapters in `domains/agent_platform`.
- Keep `libs/agent/core` independent of `domains/`.

### 1.2 Delivery discipline
- Favor immutable dataclasses and enums for contracts.
- Prefer explicit services, registries, and gateways over framework-driven abstractions.
- Represent plans, decisions, and execution results as typed artifacts.
- Keep LLM output advisory and structured; never let it directly execute tools.

### 1.3 MVP constraint
- Build one end-to-end slice first.
- Do not try to implement the full target platform surface in the first pass.
- Ship the minimum that proves the architecture is real:
  - typed capability registry
  - one planner path
  - one supervisor loop
  - local session persistence
  - prompt version selection
  - one evaluation path

## 2. MVP scope

## 2.1 Build now

The MVP should implement only these capabilities:
- `vector_search`
- `filesystem_read`
- `command_run_safe`
- `llm_synthesize`

The MVP should implement only these skills:
- `analyze_repository`
- `summarize_document`

The MVP should support only these runtime behaviors:
- create session
- plan from a selected skill
- execute a step sequence under supervisor control
- checkpoint and inspect run state
- emit normalized execution records

The MVP should support only these persistence choices:
- local filesystem-backed stores for:
  - sessions
  - checkpoints
  - prompt templates
  - capability catalog
  - evaluation runs
  - vector index fixture data

The MVP should support only these prompt/runtime features:
- prompt template selection by version
- one active prompt variant per skill
- one model gateway interface with a local/mock adapter or narrow real adapter

The MVP should support only this vector retrieval bootstrap strategy:
- one reproducible local vector index fixture built from the current repo snapshot, using an allowlisted subset of files or extracted repo excerpts
- fixture build happens outside the agent runtime through a small bootstrap script
- fixture vectors are produced by a deterministic local embedding strategy or checked-in serialized vectors, not by a live external embedding service
- `vector_search` queries only that local fixture in the first slice

The MVP should support only these evaluation features:
- offline replay/evaluation of captured runs
- schema compliance and task completion scoring

## 2.2 Explicitly deferred until after MVP works

Defer these items:
- handoffs between skills or agents
- multi-agent orchestration
- workflow trigger capabilities
- cost-budget enforcement beyond simple placeholders
- metadata filtering and knowledge graph queries
- broad MCP provider support
- runtime memory sophistication beyond persisted run/session state
- result comparison across model variants
- rich prompt experimentation system
- production-grade auth and external credentials handling
- filesystem mutation capabilities
- approval pause/resume flows

Reason:
- these features increase surface area faster than they increase proof of architectural quality

## 3. Target architecture for MVP

### 3.1 Library layout
- `libs/agent/core/src/ai_infra/contracts/`
- `libs/agent/core/src/ai_infra/registry/`
- `libs/agent/core/src/ai_infra/policies/`
- `libs/agent/core/src/ai_infra/runtime/`
- `libs/agent/core/src/ai_infra/kernel/`
- `libs/agent/core/src/ai_infra/services/`
- `libs/agent/core/src/ai_infra/gateways/`
- `libs/agent/core/src/ai_infra/evaluation/`

### 3.2 Domain layout
- `domains/agent_platform/src/app.py`
- `domains/agent_platform/src/cli/agent_cli.py`
- `domains/agent_platform/src/startup/`
- `domains/agent_platform/src/infrastructure/`
- `domains/agent_platform/src/config/`
- `domains/agent_platform/docs/ARCHITECTURE.md`
- `domains/agent_platform/README.md`

### 3.3 Boundary split
- `libs/agent/core`: stable contracts, supervisor/runtime logic, policies, registry, kernel abstractions.
- `domains/agent_platform`: startup composition root, local adapters, CLI, config assets, concrete stores.

## 4. MVP phases

## 4.1 Phase 1: Core contracts and serialization

Implement only the contracts required for the first vertical slice.

Build now:
- `AgentRun`
- `ExecutionPlan`
- `ActionStep`
- `StepDependency`
- `CapabilityDescriptor`
- `CapabilityRequest`
- `CapabilityResult`
- `NextStepDecision`
- `ReplanDecision`
- `TerminationDecision`
- `PromptTemplate`
- `PromptVersion`
- `InferenceConfiguration`
- `AgentSession`
- `SessionState`
- `SessionCheckpoint`

Defer:
- `InterruptSignal`
- `ResumeToken`
- `HandoffRequest`
- `HandoffResult`
- advanced artifact graph contracts
- prompt variants beyond the minimum needed for versioning
- richer evaluation-case hierarchy

Acceptance:
- contracts are explicit dataclasses/enums
- serialization is deterministic
- cross-layer communication does not rely on untyped dict blobs

## 4.2 Phase 2: Capability registry and catalog

Build a local file-backed capability registry.

Build now:
- capability metadata with:
  - name
  - category
  - backend kind
  - version
  - risk classification
  - input schema reference
  - output schema reference
  - side-effect flag
  - preconditions
  - postconditions
  - invariants
- `CapabilityRegistry`
- `CapabilityCatalog`
- `CapabilityResolver`
- local YAML or JSON catalog under `domains/agent_platform/src/config/`

Defer:
- dynamic capability enable/disable APIs
- capability graph optimization beyond simple dependency checks
- remote capability registry backends

Acceptance:
- CLI can list capabilities
- supervisor can resolve a capability by name/version
- behavioral contracts are executable policy inputs
- vector backends can be swapped through the gateway boundary without changing supervisor logic

## 4.3 Phase 3: Skills and typed planning

Build one planner path that turns a user goal plus skill into a typed plan.

Build now:
- skill definition contract
- file-backed skill registry
- `CapabilityPlanningService`
- planning support for:
  - `analyze_repository`
  - `summarize_document`

Planner constraints:
- emit step sequences from a bounded skill template
- allow simple conditional replanning after failed steps
- do not attempt general autonomous long-horizon planning
- prefer `filesystem_read` or `command_run_safe` before `vector_search` when direct workspace inspection is sufficient

Defer:
- open-ended skill synthesis
- multi-plan search
- planner learning/evaluation loops

Acceptance:
- each plan step references a known capability
- plans are inspectable before execution
- the plan can be reissued in a deterministic serialized form

## 4.4 Phase 4: Supervisor loop and execution runtime

Implement the minimal supervised loop.

Build now:
- `RunSupervisor`
- `NextStepDecider`
- `CapabilityExecutionService`
- `StepResultEvaluationService`
- `PlanRevisionService`
- `ResponseValidationService`
- `AgentRunManager`
- `ExecutionStateManager`
- `ExecutionJournal`

Required runtime loop:
1. load run and session state
2. validate current step readiness
3. check sandbox and capability policies
4. execute capability through a gateway
5. normalize the result
6. validate postconditions
7. append execution record and checkpoint
8. continue, replan, or terminate

Defer:
- sophisticated memory summarization
- complex branching execution graphs
- speculative parallel step execution

Acceptance:
- no capability executes outside the supervisor
- every step produces a normalized record
- failure handling results in a typed replan or termination decision
- `llm_synthesize` only consumes normalized tool outputs and prompt inputs assembled by platform services

## 4.5 Phase 5: Session persistence

Make run state durable and inspectable.

Build now:
- `AgentSessionManager`
- `SessionStateStore`
- `CheckpointManager`
- filesystem-backed session and checkpoint stores

Defer:
- `InterruptManager`

Acceptance:
- a run can be resumed from the last checkpoint after process restart
- session and run history are visible in CLI

## 4.6 Phase 6: Local adapters and CLI surface

Add only the adapters needed for the MVP.

Build now:
- `FilesystemGateway`
- `CommandExecutionGateway`
- `VectorSearchGateway`
- `ModelGateway`
- `PromptTemplateRepository`
- local adapters for each
- a local vector index bootstrap script and fixture loader
- CLI commands:
  - `agent run "<task>"`
  - `agent capability list`
  - `agent skill list`
  - `agent session show <session_id>`

Constraints:
- command execution must be allowlisted and read-only
- filesystem access is read-only and workspace-bounded
- `vector_search` should target one local backend with a narrow query/result contract
- the first demo must not depend on an external pre-populated vector database
- the first demo must not depend on a live external embedding API during bootstrap
- the bootstrap path must be deterministic and documented

Defer:
- workflow gateway
- MCP execution backend beyond interface seam

Acceptance:
- a local end-to-end run is possible without external infrastructure
- the CLI interacts with services and kernel layers rather than bypassing them

## 4.7 Phase 7: Prompt versioning and evaluation

Add the minimum platform-control signals that make the project credible.

Build now:
- local prompt repository
- prompt version selection in run metadata
- prompt assembly service for the two MVP skills
- `EvaluationRun`
- offline evaluation runner for captured runs
- initial evaluation checks:
  - schema compliance
  - task completion success

Defer:
- prompt variant experiments
- broad benchmark suites
- retrieval usefulness scoring beyond a minimal relevance signal

Acceptance:
- every run records the prompt version used
- an evaluation command can score a captured run artifact

## 5. Build order

1. Scaffold `libs/agent/core`.
2. Scaffold `domains/agent_platform`.
3. Implement core contracts and serialization helpers.
4. Implement local capability catalog and skill registry.
5. Implement supervisor loop and runtime records.
6. Implement filesystem-backed session and checkpoint stores.
7. Implement the local vector index bootstrap script and sample fixture corpus.
8. Implement the deterministic local embedding strategy or checked-in vector fixture format used by bootstrap.
9. Implement local adapters for workspace file read, allowlisted commands, vector search, and model synthesis.
10. Implement CLI commands.
11. Implement prompt version selection and offline evaluation.
12. Update docs.

## 6. Concrete file plan for MVP

### 6.1 Core library
- `libs/agent/core/src/ai_infra/contracts/agent_run.py`
- `libs/agent/core/src/ai_infra/contracts/execution_plan.py`
- `libs/agent/core/src/ai_infra/contracts/action_step.py`
- `libs/agent/core/src/ai_infra/contracts/step_dependency.py`
- `libs/agent/core/src/ai_infra/contracts/capability_descriptor.py`
- `libs/agent/core/src/ai_infra/contracts/capability_request.py`
- `libs/agent/core/src/ai_infra/contracts/capability_result.py`
- `libs/agent/core/src/ai_infra/contracts/next_step_decision.py`
- `libs/agent/core/src/ai_infra/contracts/replan_decision.py`
- `libs/agent/core/src/ai_infra/contracts/termination_decision.py`
- `libs/agent/core/src/ai_infra/contracts/prompt_template.py`
- `libs/agent/core/src/ai_infra/contracts/prompt_version.py`
- `libs/agent/core/src/ai_infra/contracts/inference_configuration.py`
- `libs/agent/core/src/ai_infra/contracts/evaluation_run.py`

### 6.2 Runtime and services
- `libs/agent/core/src/ai_infra/services/run_supervisor.py`
- `libs/agent/core/src/ai_infra/services/capability_planning_service.py`
- `libs/agent/core/src/ai_infra/services/next_step_decider.py`
- `libs/agent/core/src/ai_infra/services/capability_execution_service.py`
- `libs/agent/core/src/ai_infra/services/step_result_evaluation_service.py`
- `libs/agent/core/src/ai_infra/services/plan_revision_service.py`
- `libs/agent/core/src/ai_infra/services/prompt_assembly_service.py`
- `libs/agent/core/src/ai_infra/services/response_validation_service.py`
- `libs/agent/core/src/ai_infra/runtime/agent_run_manager.py`
- `libs/agent/core/src/ai_infra/runtime/execution_state_manager.py`
- `libs/agent/core/src/ai_infra/runtime/execution_journal.py`

### 6.3 Kernel, policies, registry, evaluation
- `libs/agent/core/src/ai_infra/kernel/agent_session_manager.py`
- `libs/agent/core/src/ai_infra/kernel/session_state_store.py`
- `libs/agent/core/src/ai_infra/kernel/checkpoint_manager.py`
- `libs/agent/core/src/ai_infra/policies/capability_policy.py`
- `libs/agent/core/src/ai_infra/policies/termination_policy.py`
- `libs/agent/core/src/ai_infra/policies/sandbox_policy.py`
- `libs/agent/core/src/ai_infra/gateways/model_gateway.py`
- `libs/agent/core/src/ai_infra/gateways/vector_search_gateway.py`
- `libs/agent/core/src/ai_infra/gateways/command_execution_gateway.py`
- `libs/agent/core/src/ai_infra/gateways/filesystem_gateway.py`
- `libs/agent/core/src/ai_infra/gateways/prompt_template_repository.py`
- `libs/agent/core/src/ai_infra/registry/capability_registry.py`
- `libs/agent/core/src/ai_infra/registry/capability_catalog.py`
- `libs/agent/core/src/ai_infra/registry/capability_resolver.py`
- `libs/agent/core/src/ai_infra/evaluation/offline_evaluation_runner.py`

### 6.4 Domain startup, config, infrastructure, CLI
- `domains/agent_platform/src/app.py`
- `domains/agent_platform/src/cli/agent_cli.py`
- `domains/agent_platform/src/startup/contracts.py`
- `domains/agent_platform/src/startup/config_extractor.py`
- `domains/agent_platform/src/startup/service_factory.py`
- `domains/agent_platform/src/infrastructure/local_command_runner.py`
- `domains/agent_platform/src/infrastructure/local_filesystem_adapter.py`
- `domains/agent_platform/src/infrastructure/local_vector_search.py`
- `domains/agent_platform/src/infrastructure/bootstrap_vector_index.py`
- `libs/agent/platform/src/agent_platform/gateways/retrieval/deterministic_embedding_fixture.py`
- `domains/agent_platform/src/infrastructure/local_prompt_repository.py`
- `domains/agent_platform/src/infrastructure/local_session_store.py`
- `domains/agent_platform/src/infrastructure/local_checkpoint_store.py`
- `domains/agent_platform/src/infrastructure/local_capability_catalog.py`
- `domains/agent_platform/src/config/capabilities.yaml`
- `domains/agent_platform/src/config/skills.yaml`
- `domains/agent_platform/src/config/prompts/`
- `domains/agent_platform/src/config/vector_fixture/`

## 7. Validation plan

### 7.1 Required checks
- `python3 -m compileall libs domains`
- project-level pytest for the new modules if test scaffolding is added
- bootstrap the local vector fixture and verify at least one deterministic query returns seeded hits
- verify bootstrap output is reproducible across repeated runs on the same fixture corpus
- CLI smoke tests for:
  - capability listing
  - skill listing
  - safe end-to-end run
  - resumed run from stored checkpoint

### 7.2 MVP scenarios
- run `analyze_repository` against this repo using `filesystem_read` and `command_run_safe`
- run the vector bootstrap script against the current repo snapshot, then run a task that enriches direct workspace inspection with `vector_search`
- confirm `llm_synthesize` receives normalized tool outputs and produces the final answer artifact
- force a step failure and confirm typed replan or termination
- evaluate a captured run artifact offline

## 8. Documentation deliverables

- update `docs/ARCHITECTURE.md` with `domains/agent_platform` and `libs/agent/core`
- add `domains/agent_platform/docs/ARCHITECTURE.md`
- add `domains/agent_platform/README.md`
- document:
  - control plane vs execution plane in MVP terms
  - supervisor loop
  - capability registry shape
  - vector search adapter boundary
  - vector fixture bootstrap workflow for the current repo snapshot
  - deferred items and why they were deferred

## 9. Post-MVP expansion order

Only after the MVP works end-to-end:
1. add approval-gated mutation capabilities such as `filesystem_write`
2. add MCP gateway implementation beyond a stub
3. add workflow trigger capabilities
4. add richer budget governance
5. add prompt variants and comparison evaluation
6. add artifact registry and handoff flows
7. add more advanced retrieval and context assembly

## 10. Risks and controls

### 10.1 Risk: architecture theater
- Control: require every new abstraction to serve the MVP flow directly.

### 10.2 Risk: hidden LLM execution authority
- Control: only typed capabilities resolved by the registry may execute.

### 10.3 Risk: repo pattern drift
- Control: keep composition roots in `domains/`, reusable logic in `libs/`, and use explicit startup wiring.

### 10.4 Risk: too many integrations too early
- Control: local adapters first, external systems later.

## 11. Definition of done for MVP

- `domains/agent_platform` exists with a functioning CLI
- `libs/agent/core` provides the runtime contracts and supervisor services required for the vertical slice
- capability registry, skills, supervisor loop, vector retrieval, and session persistence work end-to-end
- prompt version used for each run is recorded
- offline evaluation can score a captured run
- documentation explains the architecture and the intentionally deferred scope
- affected code compiles and MVP smoke checks pass
