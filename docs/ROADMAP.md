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

### Phase 3 — Investigation Planner
- [ ] Design the investigation state machine and session model (`InvestigationContext`, `InvestigationStep`).
- [ ] Implement hypothesis generation and step-by-step query planning.
- [ ] Implement the execution loop (Step -> Tool Selection -> Observation -> Next Step / Termination).
- [ ] Add guardrails: step count limits, timeout handling, and cyclic execution detection.
- [ ] Write unit tests for planner flow with deterministic mock tool outputs.

---

### Phase 4 — Evidence & Decision Engine
- [ ] Build the `EvidenceCollector` module:
  - Artifact storage for query outputs, document chunks, and metric calculations.
  - Unique evidence identification (`EVID-001`, `EVID-002`) and citation linking.
- [ ] Implement structured recommendation synthesis:
  - Root-cause classification.
  - Supporting vs. refuting evidence matrix.
  - Remediation action proposal.
- [ ] Implement the Human-in-the-Loop approval gate:
  - Approval state transitions (`PENDING_REVIEW`, `APPROVED`, `REJECTED`, `AMENDED`).
  - Signature and audit metadata logging.

---

### Phase 5 — AI Integration
- [ ] Build the provider-agnostic LLM interface (`LLMClient` abstraction).
- [ ] Implement concrete adapters (OpenAI, Anthropic, Ollama / Local Models).
- [ ] Design structured prompt templates with strict schema enforcement (JSON output parsing via Pydantic).
- [ ] Implement fallback and retry logic for structured parsing failures.
- [ ] Verify end-to-end investigation runs with real/mocked model responses.

---

### Phase 6 — Evaluation & Hardening
- [ ] Develop an offline **Golden Evaluation Dataset** containing multi-domain investigation scenarios with ground truth.
- [ ] Build automated evaluation harnesses:
  - SQL correctness evaluation against ground-truth queries.
  - Evidence retrieval recall and precision.
  - Guardrail testing (injection attacks, attempts to run mutating SQL).
- [ ] Implement audit trail export and verification tools.
- [ ] Document deterministic benchmark results.

---

### Phase 7 — Frontend
- [ ] Build a clean, responsive web interface for interacting with investigations.
- [ ] Interactive timeline showing investigation steps, tool executions, and raw evidence.
- [ ] Evidence inspector with SQL query view and document viewer.
- [ ] Decision approval dashboard with explicit human sign-off actions.

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
