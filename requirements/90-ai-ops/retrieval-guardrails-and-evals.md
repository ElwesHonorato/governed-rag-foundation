# AI Ops - Guardrails and Evaluation

## AI-01 Grounding Policy
Responses must be grounded in retrieved evidence and include source references.

## AI-02 Retrieval Guardrails
- Prefer hybrid retrieval with metadata filtering.
- Reject or defer when retrieval confidence is below threshold.

## AI-03 Evaluation Focus
Track and improve:
- Retrieval precision/recall
- Citation correctness
- Latency and cost per query
- Safety and policy adherence
