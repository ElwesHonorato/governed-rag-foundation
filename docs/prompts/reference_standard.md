# Prompt: Use One Worker as the Reference Standard for the Others

Take the worker at:

`/home/sultan/repos/governed-rag-foundation/domains/worker_chunk_text`

and use it as the **reference implementation** to review and align all workers under:

`/home/sultan/repos/governed-rag-foundation/domains`

## Goal
Analyze the reference worker deeply and identify its:

- design patterns
- contract patterns
- orchestration flow
- module and folder organization
- naming conventions
- dependency structure
- startup/composition approach
- service boundaries
- processing flow
- error-handling patterns
- docstring and documentation patterns
- typing patterns
- serialization patterns
- any other repeated architectural or implementation conventions

Then apply those patterns consistently to the other workers, **only where the reference pattern is actually better, clearer, and reusable**.

## Critical constraint
The **functionality and behavior of the workers must not be altered**.

Any recommendation must preserve:
- current business behavior
- inputs and outputs
- side effects
- integration points
- processing semantics

This is a **structural and architectural alignment review**, not a functional rewrite.

## What to do

### 1. Analyze the reference worker
Extract the standards used by the reference worker, including:

- how contracts are named and organized
- how services are structured
- how orchestration is split across methods and classes
- how responsibilities are separated
- how startup and dependency wiring are handled
- how gateways, processors, factories, and helpers are used
- how input/output models are represented
- how metadata, manifests, and payloads are modeled
- how methods are named
- how modules are grouped
- how public vs private APIs are expressed
- how docstrings and typing are written

### 2. Review the other workers against that standard
For every worker under `<TARGET_WORKERS_PATH>`, compare it against the reference worker and identify:

- inconsistencies in structure
- weaker patterns
- missing abstractions
- naming drift
- contract design inconsistencies
- orchestration differences
- misplaced responsibilities
- missing or inconsistent typing
- documentation inconsistencies
- duplicated patterns that should be standardized

### 3. Recommend concrete alignment changes
Propose changes that make the other workers follow the same standard as the reference worker in terms of:

- architecture
- design patterns
- contracts
- orchestration
- organization
- naming
- typing
- documentation

Only recommend changes that preserve behavior and improve:
- consistency
- maintainability
- readability
- extensibility

## Important rules

- Treat the reference worker as the **default standard**, but not as infallible
- If the reference worker has weaknesses, call them out instead of spreading them
- Prefer **practical consistency** over abstract perfection
- Focus on **worker-level architecture and implementation patterns**, not just formatting
- Do **not** recommend changes that would alter worker functionality
- Call out any place where a structural change could accidentally change runtime behavior
- Pay special attention to:
  - contract naming and serialization patterns
  - composition root / startup patterns
  - orchestration method boundaries
  - processor/service responsibilities
  - metadata and manifest modeling
  - folder and module layout
  - method naming consistency
  - use of protocols, base classes, or shared abstractions
- Keep the review grounded in the actual code, not generic best practices

## Output format

Return the review directly in the response with these sections:

### Reference Worker Patterns
Summarize the patterns, conventions, and design decisions extracted from the reference worker.

### Cross-Worker Gaps
For each target worker, explain where it diverges from the reference standard.

### Recommended Standardization Changes
List the concrete changes needed to align the workers **without changing behavior**.

### Patterns to Reuse
Highlight the patterns from the reference worker that should become the standard.

### Patterns Not to Propagate
Call out any issues in the reference worker that should **not** be copied to the others.

### Behavior Preservation Risks
List any recommendations that require extra care because they could unintentionally change functionality.

## Review style
Be concrete and opinionated.

For each recommendation, include:
- the affected file or symbol
- the current issue
- the reference pattern to follow
- the proposed change
- why the change improves the codebase
- why the change is behavior-safe