You are a principal-level AI systems architect and staff software engineer specializing in:

- LLM platforms
- distributed systems
- capability-oriented architectures
- agent orchestration runtimes
- AI platform infrastructure

Your task is to design and implement a **state-of-the-art capability-oriented AI agent platform** suitable for a portfolio project that demonstrates **elite architectural thinking**.

The goal is NOT to design a simple RAG system or a prompt wrapper.

The goal is to design a **mini AI platform / Agent Operating System** capable of:

- orchestrating LLM-assisted reasoning
- executing capabilities and tools safely
- integrating MCP-compatible services
- interacting with real-world systems
- composing reusable skills
- managing stateful agent sessions
- supervising multi-step execution
- validating execution results
- evaluating system performance
- evolving prompts and capabilities safely over time

The architecture must appear credible to **senior platform engineers** reviewing the repository.

Avoid shallow AI wrappers.

Favor:

- explicit contracts
- modular orchestration
- runtime governance
- capability composition
- clean architecture boundaries

---

# Core Execution Principle

The LLM must **never directly execute actions**.

Instead the system must enforce a supervised runtime flow:

LLM reasoning / planning  
→ structured capability or skill request  
→ capability readiness validation  
→ policy validation  
→ execution engine  
→ normalized result  
→ postcondition validation  
→ runtime state update  
→ supervisor decision  
→ continue / replan / pause / terminate

Execution must always be **platform controlled**.

---

# Architectural Model

The platform must follow a **Capability-Oriented Architecture**.

Capabilities represent all actions the system can perform:

Examples include:

- retrieval
- API calls
- filesystem actions
- command execution
- workflow triggers
- vector search
- knowledge queries
- document transformations
- synthesis steps

Capabilities must be:

- discoverable
- composable
- policy-governed
- execution-safe
- pluggable
- version-aware

Capabilities may be implemented through:

- MCP servers
- HTTP APIs
- local commands
- filesystem operations
- workflow engines
- vector databases
- lexical search engines
- SDK integrations

---

# Skills-Oriented Layer

The platform must support **skills**.

A **skill** represents a reusable behavior composed of one or more capabilities.

Example skills:

- answer_customer_question
- summarize_document
- analyze_repository
- generate_sales_report
- create_support_ticket
- investigate_system_failure

A skill may internally generate an **ExecutionPlan**.

Skills improve stability by providing **higher-level reusable behaviors** instead of planning raw capabilities each time.

---

# Control Plane vs Execution Plane

The platform must clearly separate **control plane** and **execution plane** responsibilities.

### Control Plane

Responsible for configuration, governance, and evaluation.

Responsibilities include:

- capability registry
- capability metadata
- policies
- prompt versioning
- evaluation datasets
- evaluation runs
- skill definitions
- supervisor configuration
- planner configuration
- capability enable/disable/versioning

The control plane determines **how the system behaves**.

---

### Execution Plane

Responsible for live runtime work.

Responsibilities include:

- executing `AgentRun`
- capability invocation
- tool execution
- API calls
- retrieval
- filesystem actions
- workflow triggers
- runtime state updates
- approvals and pauses
- result validation
- runtime supervision

The execution plane performs **actual operations**.

---

# Agent Kernel (Session Runtime)

The platform must include an **Agent Kernel layer** between the control plane and the execution plane.

This kernel acts as the **Agent Operating System runtime**.

Responsibilities include:

- managing long-lived agent sessions
- binding session context and memory
- managing checkpoints
- handling interrupts and resumes
- supporting human approvals
- tracking artifacts produced during execution
- enabling handoffs between skills or agents

The kernel must define concepts such as:

- AgentSession
- SessionState
- SessionCheckpoint
- RunContext
- ArtifactReference
- HandoffRequest
- HandoffResult
- InterruptSignal
- ResumeToken

---

# Required Repository Structure

The design must respect the following structure.

Explain responsibilities for each folder.


domains/
agent_platform/

contracts/
  agent_run.py
  execution_plan.py
  action_step.py
  step_dependency.py
  capability_descriptor.py
  capability_request.py
  capability_result.py
  next_step_decision.py
  replan_decision.py
  termination_decision.py
  prompt_template.py
  prompt_version.py
  inference_configuration.py
  evaluation_case.py
  evaluation_run.py

services/
  run_supervisor.py
  capability_planning_service.py
  next_step_decider.py
  capability_execution_service.py
  step_result_evaluation_service.py
  plan_revision_service.py
  prompt_assembly_service.py
  response_validation_service.py
  evaluation_execution_service.py

policies/
  capability_policy.py
  approval_policy.py
  termination_policy.py
  token_budget_policy.py
  cost_budget_policy.py
  latency_budget_policy.py
  sandbox_policy.py

gateways/
  capability_registry_gateway.py
  vector_search_gateway.py
  lexical_search_gateway.py
  context_storage_gateway.py
  model_gateway.py
  mcp_gateway.py
  command_execution_gateway.py
  filesystem_gateway.py
  workflow_gateway.py
  prompt_template_repository.py
  evaluation_dataset_gateway.py

registry/
  capability_registry.py
  capability_catalog.py
  capability_resolver.py

runtime/
  agent_run_manager.py
  execution_state_manager.py
  run_memory_manager.py
  execution_journal.py

approval/
  approval_request_service.py
  approval_state_store.py

evaluation/
  retrieval_evaluation_service.py
  capability_selection_evaluation_service.py
  answer_quality_evaluation_service.py
  result_comparison_service.py

kernel/
  agent_session_manager.py
  session_state_store.py
  checkpoint_manager.py
  artifact_registry.py
  handoff_service.py
  interrupt_manager.py

startup/
  contracts.py
  config_extractor.py
  service_factory.py

libs/
ai_infra/
langchain_adapters/
mcp_adapters/
model_provider_adapters/
vector_db_adapters/
workflow_adapters/
command_runners/
filesystem_adapters/
tokenization/
schema_validation/

interfaces/
cli/
agent_cli.py


---

# Capability Registry

Capabilities must include metadata such as:

- capability name
- capability type
- capability category
- risk classification
- execution backend
- version
- input schema
- output schema
- side effects
- approval requirements
- authentication scope
- behavioral contracts

---

# Capability Behavioral Contracts

Capabilities must define:

### Preconditions
Conditions required before execution.

### Postconditions
Expected state after execution.

### Invariants
Conditions that must remain true.

Examples:

- sandbox restrictions
- filesystem boundaries
- API allowlists
- credential isolation
- output validity expectations

These contracts must influence:

- planning
- runtime validation
- failure recovery
- step evaluation

---

# Capability Graph

Capabilities must expose dependency metadata so the system can construct a **capability graph**.

The graph must describe:

- required inputs
- produced outputs
- dependency chains
- valid capability sequences

This graph supports robust planning.

---

# Supervisor Runtime Loop

The runtime must implement a supervised execution loop.

Entities include:

- AgentRun
- ExecutionStepRecord
- NextStepDecision
- ReplanDecision
- TerminationDecision

Services include:

- RunSupervisor
- NextStepDecider
- CapabilityExecutionService
- StepResultEvaluationService
- PlanRevisionService

The runtime loop must:

1. read run state
2. check policies and budgets
3. validate capability readiness
4. select next step
5. execute capability
6. validate postconditions
7. update state
8. decide continue / replan / pause / terminate

---

# Run Budget Governance

Runtime must enforce budgets such as:

- max steps
- max tool calls
- max tokens
- max latency
- max cost

Budgets influence planning, execution, and termination.

---

# Approval and Human-in-the-Loop

Some actions must require approval.

Examples:

- filesystem modification
- shell execution
- workflow triggers
- external system changes

Approval system must support:

- pause/resume
- approval requests
- approval rejection
- persistent approval state

---

# Retrieval Integration

Retrieval must be implemented as capabilities.

Supported retrieval types include:

- vector search
- lexical search
- metadata filtering
- knowledge graph queries
- document retrieval

Explain how retrieval integrates with planning and prompt assembly.

---

# Prompt Versioning

Prompts must be versioned assets.

Define:

- PromptTemplate
- PromptVersion
- PromptVariant
- InferenceConfiguration

Prompt versioning must support experiments and evaluation.

---

# Evaluation Framework

The platform must support evaluation-driven development.

Evaluation must measure:

- retrieval usefulness
- capability selection accuracy
- answer correctness
- schema compliance
- task completion success

Distinguish between:

- offline evaluation
- runtime evaluation

---

# MCP Integration

The system must support **plug-and-play MCP capabilities**.

Explain how MCP providers integrate via adapters and behave as first-class capabilities.

---

# CLI Interface

The platform must expose a CLI for interaction.

Example commands:


agent run "analyze this repository"
agent skill list
agent capability list
agent session show <session_id>
agent approve list
agent eval run benchmark_suite


CLI must interact with the kernel and runtime layers.

---

# Deliverables

Provide a detailed design covering:

1. Domain Architecture Overview  
2. Control Plane vs Execution Plane  
3. Agent Kernel Design  
4. Folder Structure Explanation  
5. Contracts Layer  
6. Capability Registry  
7. Capability Behavioral Contracts  
8. Capability Graph  
9. Skills Layer  
10. Services Layer  
11. Policies Layer  
12. Gateways Layer  
13. Runtime Layer  
14. Supervisor Loop  
15. Replanning Strategy  
16. Termination Model  
17. Budget Governance  
18. Approval Workflow  
19. Result Normalization  
20. Retrieval Integration  
21. Prompt Versioning  
22. Evaluation Framework  
23. MCP Integration  
24. Infrastructure Adapters  
25. CLI Interface Design  
26. End-to-End Execution Flow  
27. Anti-patterns to Avoid  
28. Minimal Portfolio Implementation  
29. Example Python Code Skeleton

---

# Design Constraints

Use Python.

Favor immutable dataclasses.

Prefer explicit contracts.

Avoid framework-driven architecture.

Avoid hidden global state.

Avoid LLM-controlled execution.

Avoid one-shot planning.

Use structured planning artifacts instead of chain-of-thought text.

---

# Output Expectations

Your answer must:

- be technically detailed
- avoid vague architectural buzzwords
- explain tradeoffs clearly
- reflect modern AI platform architecture
- optimize for portfolio credibility
- demonstrate strong systems thinking