# Prompt: Analyze Worker Architecture and Produce Implementation Plan (plan_tasks.md)

You are an expert Python systems engineer.

Your task is to analyze the repository and produce a structured implementation plan documenting how to introduce Spark as the processing engine for workers.

You MUST leverage the following architectural document as primary context:

/home/sultan/repos/governed-rag-foundation/docs/ARCHITECTURE.md

Use it to understand intended design principles, layering, responsibilities, and runtime flow.

However:

- Do NOT assume the implementation perfectly matches the document.
- Validate architecture against actual code.
- Identify where implementation diverges from documentation.

This is an analysis + planning task.
Do NOT modify any source files.
Do NOT implement Spark yet.
Do NOT refactor anything.

Your output must be a new markdown file:

plan_tasks.md

This file must contain the complete technical analysis and step-by-step migration plan.

---

# Objectives

You must read the entire repository and produce a detailed plan covering:

## 1️⃣ Current Worker Architecture

- Identify all worker entrypoints.
- Explain how workers are launched.
- Map entrypoints to layers described in ARCHITECTURE.md.
- Describe runtime lifecycle from startup to shutdown.
- Identify composition roots, factories, builders, and dependency wiring.

## 2️⃣ Runtime Flow

Trace the full flow of a single unit of work:

- Ingestion
- Orchestration
- Processing
- Storage/output
- Acknowledgement

Produce a clear text-based flow diagram.

## 3️⃣ Infrastructure Boundaries

- Identify how queue integration is implemented.
- Identify storage integration layers.
- Identify processing engine abstraction (if any).
- Evaluate coupling to the current processing engine.

Map these to architectural contracts defined in ARCHITECTURE.md.

## 4️⃣ Data Processing Engine Assessment

- Determine how data processing is currently implemented.
- Identify where the processing engine is instantiated.
- Identify how tightly coupled workers are to the current engine.
- Determine whether an abstraction layer already exists.

## 5️⃣ Architectural Alignment Analysis

Compare implementation with ARCHITECTURE.md:

- Clean boundaries
- Violations
- Missing abstractions
- Implicit coupling
- Technical debt impacting migration

Be precise and reference file paths.

---

# Migration Plan Section

After the analysis, the second half of plan_tasks.md must include:

## 6️⃣ Spark Integration Strategy

Define:

- Minimal changes required to introduce Spark cluster usage
- Where SparkSession should be instantiated
- Whether a processing abstraction is needed
- Whether current worker lifecycle supports Spark reuse
- Required Docker changes
- Required dependency changes

## 7️⃣ Refactor Steps (Ordered Tasks)

Provide a numbered, incremental plan:

- Step 1: ...
- Step 2: ...
- Step 3: ...

Each step must include:
- Files to modify
- Why the change is needed
- Expected impact
- Risk level (Low / Medium / High)

## 8️⃣ Risk & Impact Analysis

- Operational risks
- Runtime behavior changes
- Resource impact (memory / CPU)
- Backward compatibility concerns

## 9️⃣ Final State Architecture Diagram (Text Form)

Show how the system will look after Spark integration, mapped to ARCHITECTURE.md principles.

---

# Output Requirements

- Output MUST be written to a new file: plan_tasks.md
- The file must be well-structured Markdown.
- Use clear section headers.
- Include file paths in code blocks when referencing implementation.
- No speculative assumptions.
- Base all analysis strictly on repository contents + ARCHITECTURE.md.

---

# Critical Constraints

- Do NOT modify any existing code.
- Do NOT introduce new services in this step.
- Do NOT implement Spark.
- Only analyze and produce the implementation plan.