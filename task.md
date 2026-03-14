You are a principal-level software architect and staff engineer specialized in LAG/RAG systems, distributed data pipelines, retrieval architecture, LLM evaluation, and Python backend design.

I am building a portfolio project and I want the implementation to feel state of the art, deliberate, and production-grade in architecture quality. I do NOT want shallow “AI wrapper” design. I want explicit domain boundaries, strong contracts, clean orchestration, real retrieval depth, prompt/version control, and evaluation capability.

Your task is to help me design and implement a dedicated `llm_orchestration` domain for my project.

## Project intent

This project is a governed, queue-driven pipeline with independent workers, artifacts, manifests, contracts, and strong separation between domains and shared infrastructure.

I want `llm_orchestration` to be a first-class domain, not a helper module.

This domain should be responsible for:
- interpreting inference/task requests
- deciding retrieval strategy
- orchestrating retrieval calls
- assembling context
- building the final LLM request
- enforcing output contracts
- validating model responses
- versioning prompts and inference configurations
- supporting evaluation datasets and automated comparisons
- making latency, token cost, and context tradeoffs explicit

For now, DO NOT include observability, telemetry, tracing, dashboards, metrics infrastructure, or monitoring concerns.
Focus only on architecture, contracts, orchestration, versioning, evaluation design, and implementation design.

## What I want from you

Design this domain as if it were part of a serious portfolio project that should impress a picky hiring manager or staff engineer reviewing the repository.

The design must be:
- explicit
- modular
- strongly typed
- easy to evolve
- aligned with clean architecture
- realistic to implement incrementally
- not overengineered for no reason
- model-provider agnostic

## Core architectural expectations

The solution should treat “prompt building” as too narrow and instead model this as an orchestration capability.

The domain should likely cover concepts such as:
- request classification
- retrieval planning
- retrieval execution
- evidence/context selection
- context compression or packing
- prompt assembly
- prompt versioning
- inference configuration versioning
- response contract enforcement
- response validation
- evaluation set execution
- automated result comparison
- retrieval quality evaluation
- token/cost/latency budgeting

The architecture must distinguish:
- domain policy
- application/service orchestration
- infrastructure gateways
- contracts / DTOs / value objects
- startup / composition concerns

## Important design constraints

- This is a portfolio project, so the architecture should look elite but still be understandable
- Avoid fake complexity and meaningless abstractions
- Avoid giant god objects
- Avoid turning everything into generic frameworks
- Prefer explicit classes over magical patterns
- Keep functionality evolvable for future hybrid retrieval and multiple task types
- Do not include observability yet
- Do not rely on hidden global state
- Keep contracts explicit and serialization predictable
- Favor immutable dataclasses where appropriate
- Use clear naming
- Make boundaries obvious
- Do not couple the design to one model vendor
- LangChain may be used as an implementation detail, but it must not define the architecture

## Technical expectations

Assume Python.

I want the domain to support or be ready for:
- vector DB retrieval
- keyword / lexical retrieval
- metadata-filtered retrieval
- object storage or file-backed context loading
- future support for multiple retrieval strategies
- strict output shape / schema enforcement
- prompt version tracking
- inference configuration version tracking
- evaluation datasets
- automated evaluation runs
- retrieval evaluation
- token and latency-aware request shaping

The design should make it possible to support different task types later, for example:
- document question answering
- code analysis
- refactor guidance
- summarization
- contract review

## Prompt and evaluation expectations

The design must treat prompts as versioned assets, not inline strings.

It should account for:
- prompt template versioning
- prompt variant comparison
- controlled prompt experiments
- evaluation datasets for task-specific quality checks
- automated comparisons between prompt versions or retrieval strategies
- retrieval evaluation based on relevance/recall/context usefulness
- answer evaluation based on correctness, faithfulness, and schema compliance
- explicit handling of token budget, context size, and latency/cost tradeoffs

## LangChain expectation

Assume LangChain may be used selectively, but the architecture must not be built around LangChain abstractions.

If you recommend using LangChain, explain:
- where it helps
- where it should be isolated
- where custom interfaces are better
- how to avoid framework leakage into the domain model

## Deliverables

Produce the answer in the following structure.

# 1. Domain recommendation
Explain whether `llm_orchestration` should be its own domain and why.
State the core responsibility of the domain in one precise sentence.

# 2. Domain boundaries
Clearly define:
- what belongs inside the domain
- what should stay in shared libs
- what should remain infrastructure-specific
- what should NOT belong here yet

# 3. Folder structure
Propose a concrete folder structure for `domains/llm_orchestration`, including a short explanation of the responsibility of each folder.

# 4. Core contracts
Define the most important contracts/data structures this domain should have.

At minimum, consider whether I need concepts like:
- LlmInferenceRequest
- RetrievalPlan
- RetrievalQuery
- RetrievedSnippet
- EvidencePack
- PromptTemplateVersion
- PromptVariant
- InferenceConfiguration
- PromptAssemblyInput
- LlmRequestPayload
- ResponseContract
- ValidatedLlmResponse
- EvaluationDataset
- EvaluationCase
- EvaluationRun
- EvaluationResult
- RetrievalEvaluationResult
- CostBudget
- TokenBudget

For each contract:
- explain why it exists
- explain what it should contain
- explain whether it is a domain object, config contract, transport contract, or result contract

# 5. Core services and policies
Define the main services/policies/classes of the domain.

At minimum, consider whether I need:
- TaskClassificationService
- RetrievalPlanningService
- ContextRetrievalService
- ContextSelectionService
- PromptAssemblyService
- PromptVersioningService
- ResponseValidationService
- EvaluationExecutionService
- RetrievalEvaluationService
- ResultComparisonService
- TokenBudgetPolicy
- CostBudgetPolicy
- LatencyBudgetPolicy

For each one:
- explain its responsibility
- explain what it must NOT do
- explain its dependencies
- explain how it collaborates with the others

# 6. Gateway design
Recommend the gateway interfaces the domain should depend on.

At minimum, consider:
- VectorSearchGateway
- LexicalSearchGateway
- ContextStorageGateway
- ModelGateway
- PromptTemplateRepository
- EvaluationDatasetGateway

For each gateway:
- explain why it exists
- define the boundary it protects
- explain what methods it should expose at a high level

# 7. Prompt versioning design
Explain how prompt versioning should work in this architecture.

Cover:
- how prompt templates are represented
- how versions are identified
- how variants are compared
- how an inference request selects a prompt version
- how to avoid ad hoc inline prompt strings
- how to keep prompt evolution explicit and reviewable

# 8. Evaluation design
Explain how evaluation should be introduced without overengineering.

Cover:
- evaluation datasets
- evaluation cases
- automated runs
- comparison between prompt versions
- comparison between retrieval strategies
- answer quality evaluation
- schema compliance checks

# 9. Retrieval evaluation design
Explain how retrieval quality should be evaluated.

Cover:
- recall
- relevance
- context usefulness
- redundancy
- hallucination risk from poor retrieval

Be concrete about what is realistically implementable in a portfolio project.

# 10. Latency, token, and cost tradeoffs
Explain how the architecture should represent and enforce:
- token budgets
- max context size
- latency constraints
- model/provider cost awareness

Focus on architecture and policy, not monitoring.

# 11. LangChain recommendation
Give a decisive recommendation on whether I should focus on LangChain or on model-agnostic architecture.

Explain:
- what role LangChain should play
- what should remain custom
- what would make the repo look stronger to senior engineers
- what would make it look weaker or too framework-dependent

# 12. Execution flow
Describe the end-to-end flow from incoming inference request to validated model response and optional evaluation result.
Make the flow concrete and sequential.
Show where each service participates.

# 13. Anti-patterns to avoid
List the most important implementation mistakes to avoid.
Be adversarial and opinionated.
Focus on mistakes that would make the design look shallow, confused, framework-driven, or fake-enterprise.

# 14. Incremental implementation plan
Give me a staged implementation plan.
Start with the smallest credible version and then show how to evolve it.
Each phase should be realistic and coherent.

# 15. Recommended naming
Recommend strong names for:
- the domain
- the main facade
- the request object
- the final assembled prompt/request object
- the prompt version object
- the response validator
- the retrieval result container
- the evaluation run object

# 16. Minimal elite version
If I want the minimum version that still looks high-end in a portfolio, tell me the smallest set of folders, contracts, services, gateways, versioning pieces, and evaluation pieces I should implement first.

# 17. Example code skeleton
Provide a clean Python code skeleton with:
- key dataclasses
- key protocols / interfaces
- main service/facade
- method signatures
- no unnecessary implementation detail

## Output quality requirements

- Be concrete, not generic
- Do not give shallow advice
- Do not just list buzzwords
- Make tradeoffs explicit
- Prefer strong architectural judgment
- If something feels like overengineering, say so directly
- Optimize for portfolio quality and architectural credibility
- Write as if you are helping build a repo that will be judged by senior engineers

## Additional instruction

When proposing the architecture, favor a design where:
- workers can consume this domain cleanly
- retrieval policy remains explicit
- vector DB usage is behind a gateway
- prompt composition is not treated as a string helper
- response validation is first-class
- prompt versioning is explicit
- evaluation is designed in from the beginning
- domain policy is separated from low-level mechanics
- LangChain is optional and isolated

Be decisive. I do not want multiple vague options unless there is a real tradeoff.
Recommend the best architecture and explain why.