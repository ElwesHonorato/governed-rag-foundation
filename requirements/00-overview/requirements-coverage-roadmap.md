# Requirements Coverage Roadmap

## Current Repository State Summary
- Repository provides local-stack scaffolding and two runtime services:
- `apps/rag-api`: Flask API exposing `/`, `/ui`, and `/prompt`; currently functions as a direct Ollama chat proxy without retrieval, citation, filtering, or policy enforcement (`apps/rag-api/src/rag_api/routes.py`, `apps/rag-api/src/rag_api/services/prompt_service.py`).
- `domains/worker_*`: isolated pipeline worker stages for scan, parse, chunk, embed, index, manifest, and metrics (`domains/worker_*/docker-compose.yml`).
- Infrastructure domains are defined for MinIO, Weaviate, Redis, Marquez, Ollama, and app services (`domains/*/docker-compose.yml`), but most domain capabilities are not yet integrated into business logic.
- No automated test suite is present in application code; acceptance criteria are documented but not executable (`requirements/80-testing-acceptance/acceptance-criteria-global-logistics-hub.md`).
- Requirements set is comprehensive across functional, data, architecture, security, AI ops, and non-functional domains, while implementation is currently foundation-stage.

## Requirement-to-Implementation Coverage Matrix
Legend: `Covered` = implemented and traceable in code, `Partial` = scaffolded/incomplete, `Missing` = not implemented.

| Requirement ID | Requirement Summary | Current Coverage | Evidence in Repository | Gap Notes |
|---|---|---|---|---|
| FR-01 | Unified ingestion across unstructured/structured/streaming/APIs/DB | Partial | `domains/worker_scan/src/app.py`, `domains/worker_parse_document/src/app.py` | Current implementation covers S3-driven document flow only; SharePoint/SAP/Oracle/Kafka/Flink/API/DB connectors are still missing. |
| FR-02 | Retrieval for delays/contracts/IoT | Missing | `apps/rag-api/src/rag_api/routes.py` | No retrieval pipeline; `/prompt` calls LLM directly. |
| FR-03 | Multimodal query support (text/tables/images) | Missing | `apps/rag-api/src/rag_api/services/prompt_service.py` | No multimodal parsing, indexing, or query path. |
| FR-04 | Metadata-filtered retrieval (`source_type`, `timestamp`, domain) | Missing | `apps/rag-api/src/rag_api/routes.py` | No retrieval query API or metadata filter handling. |
| NFR-01 | 1,000+ concurrent users | Missing | `apps/rag-api/src/rag_api/app.py` | Single-process Flask app; no load/perf controls or benchmark evidence. |
| NFR-02 | Hybrid retrieval (BM25 + semantic) | Missing | `domains/vector/docker-compose.yml` | Weaviate deployed but no hybrid retrieval logic implemented. |
| NFR-03 | Caching for latency/cost optimization | Missing | `domains/cache/docker-compose.yml` | Redis deployed but unused in app logic. |
| NFR-04 | Reliability under peak/degraded upstream | Partial | `apps/rag-api/src/rag_api/llm_client.py` | Basic retry for some LLM failures only; no circuit breaking, fallback retrieval, or resilience policy. |
| A-01 | Full governed RAG flow (ingest->chunk->mask->embed->hybrid retrieve->grounded response) | Missing | `domains/worker_*/src`, `apps/rag-api/src/rag_api/services/prompt_service.py` | Worker stages exist, but masking and governed retrieval/grounded response behavior are still incomplete. |
| A-02 | Context-aware chunking, parent-child indexing, versioned indexing | Partial | `domains/worker_chunk_text/src/app.py`, `domains/worker_index_weaviate/src/app.py` | Chunking and indexing stages exist, but advanced context-aware and versioning features are incomplete. |
| INT-01 | S3 + SharePoint document sources | Partial | S3 config in `.env.example`; S3 usage in `domains/worker_*/src` | S3 pipeline is present; SharePoint integration remains missing. |
| INT-02 | SAP + Oracle shipment logs | Missing | N/A in app code | No connectors/contracts/ingestion jobs. |
| INT-03 | Kafka/Flink streaming for IoT | Missing | N/A in app code | No stream consumers/processors. |
| INT-04 | Port congestion + weather APIs | Missing | N/A in app code | No API clients or scheduled ingestion. |
| INT-05 | Controlled DB access to operational stores | Missing | N/A in app code | No DB integration layer or policy controls. |
| D-01 | Canonical schema normalization | Missing | N/A in app code | No canonical model or mapping layer. |
| D-02 | Format-aware parsing for tables/images/text | Missing | N/A in app code | No parser/orchestration components. |
| D-03 | Semantic chunking + parent-child indexing | Missing | N/A in app code | No chunking/index services. |
| D-04 | Cross-modal embeddings + late-interaction evaluation | Missing | N/A in app code | No embedding service or evaluation harness. |
| D-05 | Metadata enrichment (`source_type`, `timestamp`, `security_clearance`) | Missing | N/A in app code | Metadata schema not enforced in pipeline/indexing. |
| SEC-01 | PII/PHI masking before vectorization | Missing | N/A in app code | No detection/masking stage before persistence. |
| SEC-02 | RBAC authorization by user/document | Missing | `apps/rag-api/src/rag_api/routes.py` | No authn/authz stack. |
| SEC-03 | Query-time authorization filters | Missing | N/A in app code | No security metadata filter layer in retrieval. |
| AC-01 | Ingestion coverage for all source classes | Missing | `domains/worker_scan/src/app.py` | Current ingestion remains limited to S3-driven processing. |
| AC-02 | Canonical data normalization | Missing | N/A in app code | No canonical mapping validation. |
| AC-03 | Relevant hybrid retrieval with citations | Missing | `apps/rag-api/src/rag_api/services/prompt_service.py` | No retrieval/citation subsystem. |
| AC-04 | Source/version/process traceability | Missing | Marquez infra defined in `domains/lineage/docker-compose.yml` | Lineage infra exists; no lineage events emitted from app/pipeline. |
| AC-05 | Security masking + RBAC enforcement | Missing | N/A in app code | Security requirements not implemented. |
| AC-06 | Stable 1,000+ user behavior with acceptable latency | Missing | N/A in app code | No performance profile/tests/SLO evidence. |
| AI-01 | Grounded responses with source references | Missing | `apps/rag-api/src/rag_api/services/prompt_service.py` | Current responses are not evidence-grounded/cited. |
| AI-02 | Hybrid retrieval + metadata guardrails + low-confidence defer | Missing | N/A in app code | No guardrail pipeline/confidence model. |
| AI-03 | Evals for retrieval/citations/latency/cost/safety | Missing | N/A in app code | No evaluation datasets, runners, or dashboards. |

Coverage snapshot (deterministic):
- `Covered`: 0 / 32
- `Partial`: 4 / 32 (`FR-01`, `NFR-04`, `INT-01`, infra-only support for `AC-04`)
- `Missing`: 28 / 32

## Identified Gaps (with severity and impact)
| Gap ID | Severity | Impact | Description | Affected Requirements |
|---|---|---|---|---|
| GAP-01 | Critical | Product cannot satisfy core purpose | No retrieval pipeline; assistant is an LLM proxy without vector search, ranking, or citations. | FR-02, FR-04, NFR-02, AI-01, AI-02, AC-03 |
| GAP-02 | Critical | Enterprise use cases not ingestible | Multi-source ingestion connectors (SharePoint, SAP, Oracle, Kafka/Flink, APIs, DB) are absent. | FR-01, INT-01..INT-05, AC-01 |
| GAP-03 | Critical | Governance/compliance exposure | No masking, RBAC, or query-time authorization filters. | SEC-01..SEC-03, AC-05 |
| GAP-04 | High | Retrieval quality and explainability blocked | No parsing/chunking/indexing/versioning/metadata enrichment pipeline. | A-01, A-02, D-01..D-05, AC-02, AC-04 |
| GAP-05 | High | Production readiness not demonstrable | No reliability architecture, SLOs, load testing, or failure-mode controls. | NFR-01, NFR-04, AC-06 |
| GAP-06 | High | Cost/latency optimization missing | Redis cache not integrated in retrieval/response path. | NFR-03 |
| GAP-07 | Medium | AI safety and quality cannot be governed | No retrieval confidence gating or evaluation framework. | AI-02, AI-03 |
| GAP-08 | Medium | Progress cannot be objectively tracked | Acceptance criteria are not encoded into automated tests/quality gates. | AC-01..AC-06 |

## Prioritized Execution Roadmap (dependency-aware, step-by-step)
Status legend: `P0` immediate, `P1` near-term, `P2` follow-on.

### Phase 0 - Foundation Decisions and Contracts (P0)
1. Finalize architecture decisions as ADRs for vector DB profile, embedding model set, retrieval strategy, and security/compliance scope.
- Dependencies: none.
- Outputs: `requirements/99-decisions/*.md` ADRs; updated `requirements/95-open-questions/*` closure notes.
2. Define canonical data contracts and metadata schema (`source_type`, `timestamp`, `security_clearance`, source identifiers, version IDs).
- Dependencies: Step 1.
- Outputs: versioned schema docs and shared Python models package.
3. Define target SLO/SLA envelopes (p95 latency, throughput, availability) and cost budgets.
- Dependencies: Step 1.
- Outputs: NFR baseline doc + measurable acceptance thresholds.

### Phase 1 - Governed Ingestion Backbone (P0)
4. Build connector framework with pluggable source adapters and ingestion job orchestration.
- Dependencies: Steps 1-3.
- Outputs: adapters for S3/SharePoint/SAP/Oracle/APIs/DB + stream adapter contract for Kafka/Flink.
5. Implement normalization and format-aware parsing pipeline (text/table/image) with canonical schema mapping.
- Dependencies: Steps 2 and 4.
- Outputs: parser modules, mapping rules, parse quality checks.
6. Implement security pre-processing: PII/PHI detection and masking/redaction before chunking/vector writes.
- Dependencies: Steps 2 and 5.
- Outputs: masking service, policy configs, audit logs.
7. Implement chunking/index prep with parent-child relationships and versioned document lineage IDs.
- Dependencies: Steps 2, 5, and 6.
- Outputs: chunk builder + index payload model.
8. Implement embedding/index writer for Weaviate with enriched metadata and version tagging.
- Dependencies: Step 7.
- Outputs: embedding pipeline workers + write/read validation checks.
9. Emit lineage events to Marquez for ingestion and transformation stages.
- Dependencies: Steps 4-8.
- Outputs: lineage emitter + traceability dashboards.

### Phase 2 - Retrieval and Response Plane (P0)
10. Build retrieval service supporting hybrid retrieval (semantic + lexical/BM25 equivalent) with metadata filters.
- Dependencies: Step 8.
- Outputs: retrieval API, filter parser, ranking pipeline.
11. Implement authorization layer (authn + RBAC policy evaluation + query-time security filters).
- Dependencies: Steps 2 and 10.
- Outputs: role model, policy engine integration, enforcement middleware.
12. Replace direct `/prompt` proxy with grounded answer pipeline (retrieve, cite, generate, confidence-score, defer on low confidence).
- Dependencies: Steps 10 and 11.
- Outputs: revised `rag-api` service endpoints + citation payload contract.
13. Add caching strategy (Redis) for frequent query patterns and retrieval artifacts.
- Dependencies: Steps 10 and 12.
- Outputs: cache keys/TTL policy, hit-rate and latency telemetry.

### Phase 3 - Production Hardening and Verification (P1)
14. Add observability baseline (structured logs, metrics, traces) across API, workers, and integrations.
- Dependencies: Steps 4-13.
- Outputs: dashboards for throughput, latency, failure rates, and cost/query.
15. Implement resilience patterns (timeouts, retries with backoff, circuit breakers, degraded-mode behavior).
- Dependencies: Steps 10-14.
- Outputs: reliability playbooks and fault-injection tests.
16. Build acceptance/e2e/performance test suites mapped 1:1 to AC-01..AC-06 and AI-01..AI-03.
- Dependencies: Steps 4-15.
- Outputs: CI quality gates and release blocking criteria.
17. Execute scale and chaos validation for 1,000+ concurrent users and upstream degradation scenarios.
- Dependencies: Steps 15 and 16.
- Outputs: benchmark reports and SLO conformance evidence.

### Phase 4 - Advanced Retrieval and Optimization (P2)
18. Extend multimodal retrieval (cross-modal embeddings, image-aware querying, table-specialized retrieval).
- Dependencies: Steps 5, 8, 10, and 12.
- Outputs: multimodal index + relevance eval improvements.
19. Evaluate and optionally ship late-interaction retrieval (ColBERT-style) for precision-sensitive domains.
- Dependencies: Steps 10 and 16.
- Outputs: A/B evaluation, decision ADR, rollout plan.
20. Close remaining open questions and operationalize governance reviews (security/compliance cadence).
- Dependencies: all prior steps.
- Outputs: periodic review checklist and signed-off operating model.

Roadmap sequencing rationale:
- Retrieval and security are blocked by canonical metadata and ingestion completeness.
- Acceptance and scale verification are meaningful only after governed retrieval behavior exists.
- Advanced multimodal and late-interaction optimization should follow baseline production readiness.

### Immediate Vertical Slice Plan (HTML: S3 -> Weaviate)
Tracked as a separate epic ticket:
- `requirements/sprints/on-going/01_html-s3-weaviate-vertical-slice-epic.md`

## Risks, Assumptions, and Open Questions
### Risks
- Delayed decisions on vector DB/embedding model/compliance scope will stall implementation across ingestion, retrieval, and security.
- Building all source connectors in one release increases delivery risk; staged rollout per source class is safer.
- Security masking quality can degrade retrieval utility if policy and redaction granularity are not calibrated.
- Performance targets may be unattainable without early load-testing feedback loops.

### Assumptions
- Weaviate, Redis, Marquez, MinIO, and Ollama remain baseline local infrastructure choices.
- Existing requirement documents remain authoritative unless superseded by ADRs.
- Hybrid retrieval can be implemented with current vector stack (or with approved adjunct search component).

### Open Questions Requiring Decision
- Primary vector DB and retrieval architecture final choice.
- Standard embedding models for text and images.
- V1 requirement for late-interaction retrieval.
- Concrete SLOs (p95 latency, availability) and budget constraints.
- Final RBAC matrix by role/business unit/region.
- Conflict resolution policy for multi-system source-of-truth disagreements.

## Definition of Done for Full Requirement Coverage
- All requirement IDs in sections `20` to `90` have status `Covered` in this matrix with code-level evidence.
- End-to-end governed RAG flow is operational: multi-source ingest, normalization, masking, chunking, embedding, hybrid retrieval, grounded generation, and citation output.
- Security controls are enforced in both ingestion and retrieval paths (masking + RBAC + query-time filters), with auditability.
- Lineage traceability is available per response to source/version/processing steps.
- Automated acceptance suite validates AC-01..AC-06; AI eval suite validates AI-01..AI-03 with pass thresholds.
- Performance and reliability evidence demonstrates 1,000+ concurrent-user target within approved SLOs.
- Open questions are either resolved into ADRs or explicitly accepted as deferred with documented rationale.

## Change Log
- 2026-02-09: Initial creation of requirements coverage roadmap. Baseline assessment indicates foundation infrastructure is present but product capability coverage is largely missing; established deterministic coverage matrix, critical gaps, and dependency-aware execution roadmap.
- 2026-02-09: Added immediate HTML vertical-slice execution plan (`rag-data/01_incoming` to Weaviate) with ordered implementation steps, idempotency guidance, observability counters, and slice-specific acceptance criteria.
- 2026-02-09: Moved the HTML vertical-slice plan into a dedicated epic ticket document and left a roadmap reference link.
- 2026-02-09: Relocated the HTML vertical-slice epic into `requirements/sprints/on-going/` and refreshed the roadmap reference.
