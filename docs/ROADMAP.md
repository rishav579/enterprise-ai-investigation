# Project Implementation Roadmap

This roadmap defines the step-by-step, incremental development lifecycle for the **Enterprise AI Investigation & Decision System**. Each phase builds upon the verified foundation of preceding phases.

---

## 🗺️ Phases Overview

```
Phase 0 ──► Phase 1 ──► Phase 2 ──► Phase 3 ──► Phase 4
Foundations Enterprise  Controlled   Investigation Evidence &
            Data Setup  Tools Engine  Planner       Decision

   ──► Phase 5 ──► Phase 6 ──► Phase 7 ──► Phase 8 ──► Phase 9
       AI Model    Eval &      Frontend    Deployment  Portfolio
       Integration Hardening   Dashboard   Packaging   Finalization
```

---

### Phase 0 — Foundation
- [x] Initialize Git repository with `main` branch and remote origin.
- [x] Establish architecture documentation (`README.md`, `ARCHITECTURE.md`, `ROADMAP.md`, `DECISIONS.md`).
- [x] Define standard project folder layout (`src/`, `tests/`, `data/`, `docs/`).
- [x] Configure Python environment, packaging files (`pyproject.toml`), and `.gitignore`.

---

### Phase 1 — Enterprise Data Foundation
- [x] Design synthetic enterprise domain schema (SaaS operational data: customers, subscriptions, support tickets, billing events, product incidents, release events).
- [x] Implement database schema and table definitions using SQLAlchemy 2.0.
- [x] Build deterministic, idempotent data seed scripts generating multi-table planted business anomalies (cancellation spike, billing gateway regression, support SLA degradation).
- [x] Create mock knowledge base postmortem document.
- [x] Implement read-oriented safe query service and Pydantic validation models.
- [x] Verify data integrity, query performance, and scenario signal presence using pytest test suite.
- [x] Implement minimal FastAPI `/health` endpoint.

---

### Phase 2 — Controlled Investigation Tools
- [x] Build the core `ToolRegistry` and abstract base `BaseTool` class.
- [x] Implement `SQLInvestigationTool`:
  - Token-level statement validation (`SELECT` and `WITH` only).
  - Multi-statement detection and mutation keyword blocklist.
  - Parameterized bindings and row limit capping (`truncated` flag).
  - Clean structured output schemas (`SQLQueryResult`).
- [x] Implement `DocumentRetrievalTool`:
  - Safe local document repository listing, identifier retrieval, and keyword search.
  - Path traversal and absolute file system path rejection.
  - Excerpt extraction with line numbers and context.
- [x] Implement comprehensive security guardrail tests (SQL injection, mutations, path traversals).
- [x] Implement deterministic multi-step investigation scenario evaluation test suite.

---

### Phase 3 — Investigation Planning & Orchestration
- [x] Design typed Pydantic models: `InvestigationRequest`, `InvestigationPlan`, `InvestigationStep`, `InvestigationStepResult`, `InvestigationRunResult`, `StepStatus`, `InvestigationStatus`.
- [x] Implement deterministic `InvestigationPlanner` with keyword-based scenario detection and canonical step sequences (no LLM).
- [x] Implement `InvestigationOrchestrator` executing plans via `ToolRegistry` with dependency tracking.
- [x] Dependency-aware execution: blocked steps receive explicit `BLOCKED` status when dependencies fail.
- [x] Graceful error isolation: a failed step does not abort the full investigation.
- [x] Comprehensive unit tests for planner determinism, keyword matching, dependency validation, and `max_steps` capping.
- [x] Integration tests for orchestrator: structured results, ordering, row counts, dependency blocking, unregistered tool rejection.
- [x] End-to-end evaluation scenario: verifies all 9 churn investigation steps complete and produce anomalous evidence signals.

---

### Phase 4 — Evidence Collection & Auditability
- [x] Typed evidence domain model (`EvidenceItem`, `EvidenceStore`, `EvidenceType`, typed content schemas).
- [x] Deterministic content hash (`SHA-256` via stdlib `hashlib`) for every evidence item.
- [x] `EvidenceCollector`: faithful, non-LLM conversion of tool outputs to typed evidence.
- [x] `DOCUMENT_SEARCH_SUMMARY` evidence type ensures every search step is auditable even with 0 matches.
- [x] `evidence_ids` attached to each `InvestigationStepResult`.
- [x] `total_evidence_items` and `audit_event_count` added to `InvestigationRunResult`.
- [x] `AuditTrail`: append-only, immutable `AuditEvent` records with deterministic sequence numbers.
- [x] Audit events for: investigation start/end, plan creation, step start/complete/fail/block, evidence collection.
- [x] Orchestrator extended with evidence collection and audit trail (all Phase 3 contracts preserved).
- [x] No evidence fabricated for FAILED or BLOCKED steps.
- [x] Comprehensive unit tests: hash stability, mutation detection, EvidenceStore append-only semantics, audit immutability.
- [x] Integration tests: evidence IDs in step results, provenance, no-fabrication on failures.
- [x] End-to-end evaluation: hash stability across runs, provenance checks on SQL and document evidence.

---

### Phase 5 — Grounded Investigation Synthesis
- [x] Strongly typed synthesis domain models (`InvestigationReport`, `Finding`, `Recommendation`, `ConfidenceLevel`, `PriorityLevel`, `SynthesisStatus`).
- [x] Provider-agnostic `LLMProvider` interface with deterministic, fully offline `MockLLMProvider`.
- [x] Evidence-constrained prompt builder (`PromptBuilder`) with clear prompt injection data boundaries.
- [x] Deterministic citation validation (`CitationValidator`) enforcing same-run provenance for every cited evidence ID.
- [x] Cross-run isolation: foreign run evidence IDs are strictly rejected.
- [x] Graceful insufficient evidence handling: returns `root_cause=None` and `INSUFFICIENT_EVIDENCE` status without hallucinating.
- [x] Robust prompt-injection defense: documents with malicious commands are treated strictly as data.
- [x] Integrated `InvestigationSynthesizer` service connecting orchestrator, evidence store, prompt builder, provider, and validator.
- [x] Audit trail integration with `SYNTHESIS_STARTED`, `SYNTHESIS_GENERATED`, `SYNTHESIS_VALIDATED`, `SYNTHESIS_FAILED` events.
- [x] FastAPI `/investigations/investigate` endpoint executing end-to-end investigation and synthesis.
- [x] Complete unit, integration, and evaluation test suite (195 tests total, 0 failures).

---

### Phase 6 — Evaluation & Hardening
- [x] Develop an offline **Golden Evaluation Dataset** containing multi-domain investigation scenarios with ground truth.
- [x] Build automated evaluation harnesses:
  - [x] SQL correctness evaluation against ground-truth queries.
  - [x] Evidence retrieval recall and precision.
  - [x] Guardrail testing (injection attacks, attempts to run mutating SQL).
- [x] Implement audit trail export and verification tools.
- [x] Document deterministic benchmark results.

---

### Phase 7 — Frontend
- [x] Build a clean, responsive web interface for interacting with investigations (React 19 + TypeScript + Vite).
- [x] Interactive timeline showing ordered investigation steps, tool executions, and raw evidence artifacts.
- [x] Evidence inspector drawer with formatted SQL query / data grid view, document excerpts, and SHA-256 hash validation.
- [x] Grounded synthesis report view with 100% verified citation badges and root cause breakdown.
- [x] Human review workflow simulation with explicit sign-off / reject / request-more-evidence actions.
- [x] Comprehensive frontend unit and integration test suite (32 tests passing).
- [x] Production build verification and end-to-end local HTTP smoke test.

---

### Phase 8 — Deployment
- [ ] Create Dockerfile for containerized backend execution.
- [ ] Create `docker-compose.yml` for unified local setup (API, Database, Frontend).
- [ ] Implement health check endpoints (`/health`, `/ready`).
- [ ] Add environment configuration templates (`.env.example`).

---

### Phase 9 — Portfolio Finalization
- [ ] Write comprehensive documentation, quickstart guide, and API documentation.
- [ ] Record demonstration walkthroughs and scenario case studies.
- [ ] Review all codebase files for clean architecture, type annotations, and documentation comments.
- [ ] Final repository polish.
