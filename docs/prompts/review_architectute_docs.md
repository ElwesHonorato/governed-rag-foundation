Review the file `ARCHITECTURE.md` in this module.

Your task is to refactor it into a high-quality onboarding architecture document that clearly explains this module to a new joiner.

The goal is not to summarize, but to make the module understandable, navigable, extensible, and transparent about its current limitations and future direction.

---

# REQUIRED STRUCTURE

The document MUST follow this exact structure:

# 1. Purpose

- What problem this module solves.
- Why it exists.
- What it does **and does not** do.
- Its boundaries within the system.

---

# 2. High-Level Responsibilities

- Core responsibilities.
- Non-responsibilities.
- Clear separation of concerns.

---

# 3. Architectural Overview

- Explain the overall design.
- Describe the layering (startup, services, processors, gateways, contracts, etc.).
- Identify the design patterns used (Composition Root, Dependency Injection, Factory, Ports & Adapters, etc.).
- Explain why these patterns were chosen.

---

# 4. Module Structure

- Describe the folder/package layout.
- Explain what belongs where.
- Clarify how dependencies flow between layers.

Add a Mermaid diagram that visualizes:

- Layers
- Dependency direction
- Key abstractions

---

# 5. Runtime Flow (Golden Path)

Explain the standard execution path step by step:

- Entry point
- Configuration loading
- Dependency construction
- Service initialization
- Main processing loop
- Shutdown/termination behavior (if applicable)

Add a Mermaid flowchart illustrating the runtime flow.

---

# 6. Key Abstractions

For each important abstraction (e.g., runtime factory, worker launcher, gateway, service, processor):

- What it represents
- Why it exists
- What it depends on
- What depends on it
- How to extend it safely

---

# 7. Extension Points

- Where new features should be added.
- Where new integrations should plug in.
- How to add new workers or services following existing conventions.
- How to avoid violating architectural boundaries.

---

# 8. Known Issues & Technical Debt

Document architectural or design issues that have already been identified, including:

- Structural weaknesses
- Pattern inconsistencies
- Coupling problems
- Missing abstractions
- Areas that need refactoring
- Known scalability or maintainability concerns

For each issue, describe:

- What the issue is
- Why it is a problem
- Suggested future direction (if known)

Be factual and technical. Do not invent issues — infer from the current codebase.

---

# 9. Future Roadmap / Planned Enhancements

Document foreseeable future improvements, such as:

- Planned features
- Architectural evolutions
- Integration improvements
- Performance enhancements
- Governance/observability extensions

Clarify whether each item is:

- Confirmed roadmap
- Likely evolution
- Speculative improvement based on architectural direction

Avoid vague statements. Be concrete and grounded in current design.

---

# 10. Anti-Patterns / What Not To Do

- Common mistakes that would break the architecture.
- What layers must not depend on.
- What should not be instantiated outside the composition root.
- How to avoid architectural drift.

---

# 11. Glossary (Optional but Recommended)

- Define module-specific terminology.
- Clarify ambiguous concepts.

---

# DIAGRAM REQUIREMENTS

Include:

1. A high-level structural diagram (layers and dependencies).
2. A runtime flow diagram (happy path).

Use Mermaid syntax.

---

# CONSTRAINTS

- Do not invent architecture — infer from the actual codebase.
- Do not add speculative components beyond reasonable architectural inference.
- Be precise and technical.
- Optimize for engineers onboarding to the project.
- Avoid generic filler text.
- If something is unclear from the code, state assumptions explicitly.
- Keep the tone professional and engineering-focused.