# Architecture Specification: Enterprise AI Investigation & Decision System

## 1. System Overview

The **Enterprise AI Investigation & Decision System** is designed as a modular, secure, and auditable platform for conducting data-driven investigations in response to complex enterprise inquiries.

Unlike conversational chatbots that generate unverified narrative text, this system enforces a **formal investigation lifecycle**: planning hypothesis tests, dispatching strictly typed tools, accumulating verifiable evidence artifacts, generating structured root-cause recommendations, and queuing critical business actions for human approval.

---

## 2. High-Level Architecture Diagram

```
+-----------------------------------------------------------------------------------+
|                                 USER / CLIENT                                     |
|                   (API Clients, Web UI, Investigation Panel)                      |
+-----------------------------------------+-----------------------------------------+
                                          |
                                          v
+-----------------------------------------------------------------------------------+
|                                FASTAPI APPLICATION                                |
|   - Authentication & Request Routing                                              |
|   - Investigation Lifecycle Endpoints (/investigations/plan, /execute, /approve) |
|   - Audit Log Querying & Export                                                   |
+-----------------------------------------+-----------------------------------------+
                                          |
                                          v
+-----------------------------------------------------------------------------------+
|                        INVESTIGATION ORCHESTRATION LAYER                          |
|                                                                                   |
|  +---------------------------+             +----------------------------------+   |
|  |   Investigation Planner   | <---------> |    Provider-Agnostic LLM Client  |   |
|  |   (Deconstructs inquiry   |             | (OpenAI / Anthropic / Ollama)    |   |
|  |    into discrete steps)   |             +----------------------------------+   |
|  +-------------+-------------+                                                    |
|                |                                                                  |
|                v                                                                  |
|  +---------------------------+             +----------------------------------+   |
|  |   Controlled Tool Engine  | ----------> |          Audit Logger            |   |
|  |   - Schema validation     |             | (Immutable trace of every        |   |
|  |   - Execution dispatch    |             |  step, tool, input & output)     |   |
|  +-------------+-------------+             +----------------------------------+   |
+----------------|------------------------------------------------------------------+
                 |
                 +-----------------------+-----------------------+
                 |                       |                       |
                 v                       v                       v
+--------------------------------+ +--------------------+ +-------------------------+
|        READ-ONLY SQL TOOL      | | DOCUMENT RETRIEVAL | |    OPTIONAL DOMAIN      |
| - AST Query Validation         | | - Vector Search    | |      API TOOLS          |
| - Read-Only DB Connection Pool | | - FTS Search       | | - External CRM / ERP    |
| - Schema Catalog Introspection | | - Policy & KB Docs | |   (Mocked Sandbox)      |
+----------------+---------------+ +---------+----------+ +------------+------------+
                 |                           |                         |
                 +---------------------------+-------------------------+
                                             |
                                             v
+-----------------------------------------------------------------------------------+
|                             EVIDENCE COLLECTION ENGINE                            |
|  - Validates and stores raw factual artifacts (row counts, query results, text)   |
|  - Attaches cryptographic hashes and step IDs to every evidence item              |
+--------------------------------------------+--------------------------------------+
                                             |
                                             v
+-----------------------------------------------------------------------------------+
|                      DECISION & RECOMMENDATION SYNTHESIS                          |
|  - Correlates evidence into structured findings                                   |
|  - Computes confidence scores based on evidence coverage                          |
|  - Produces structured JSON output (Findings, Root Cause, Action Plan)            |
+--------------------------------------------+--------------------------------------+
                                             |
                                             v
+-----------------------------------------------------------------------------------+
|                           HUMAN-IN-THE-LOOP APPROVAL                              |
|  - Reviewer inspects the complete evidence chain                                  |
|  - Explicit Sign-Off / Reject / Amend workflow prior to action execution          |
+-----------------------------------------------------------------------------------+
```

---

## 3. Core System Components

### 3.1. API & Routing Layer (FastAPI)
- Handles HTTP requests, input validation via **Pydantic v2**, and response serialization.
- Enforces request tracing using unique `investigation_id` and `trace_id` headers.
- Exposes clean RESTful endpoints for starting investigations, stepping through plan execution, inspecting evidence logs, and recording human approvals.

### 3.2. Investigation Planner & Orchestrator
- Receives the business question (e.g., *"Why did churn increase in enterprise accounts during Q3?"*).
- Breaks the inquiry into distinct hypotheses and sub-goals.
- Evaluates intermediate evidence after each tool step to determine whether to terminate or investigate further (bounded by max steps to prevent infinite loops).

### 3.3. Investigation Planning & Orchestration Layer (Phase 3 — Implemented)

The Phase 3 layer provides deterministic investigation planning and orchestration **without requiring a live LLM**:

**`InvestigationPlanner`**
- Detects the investigation scenario from the business question using keyword matching.
- Selects a pre-authored canonical step sequence (e.g., `churn_spike_investigation`).
- Produces the same plan for the same question every time (deterministic, offline-capable).
- Respects `max_steps` caps and `scenario_hint` overrides.

**`InvestigationOrchestrator`**
- Accepts an `InvestigationRequest`, requests a plan from the planner, then executes each step in order.
- All tool invocations go exclusively through the `ToolRegistry` — no direct tool instantiation.
- Tracks step completion state to enforce declared `depends_on` relationships.
- A step with an unmet or failed dependency receives `BLOCKED` status and is not executed.
- A failed step does not abort the investigation; subsequent independent steps continue.
- Returns a fully typed `InvestigationRunResult` containing per-step results, row counts, evidence summaries, and overall counts.

**Current Limitation:** The planner is rule-based. LLM-driven dynamic planning is scheduled for Phase 5.

### 3.4. Data Layer & Repository Pattern
- Decouples business logic from persistence technologies.
- Uses **SQLAlchemy 2.0** repository abstractions.
- Operates on SQLite for lightweight, reproducible local development while maintaining full compatibility with PostgreSQL for production deployments.

### 3.5. Read-Only SQL Tool
- **Schema Catalog:** Injects controlled table definitions and column descriptions into the model prompt.
- **AST Parsing & Validation:** Uses SQL parsing (e.g., via `sqlglot`) to verify that incoming SQL statements are strictly `SELECT` statements without data mutation keywords (`INSERT`, `UPDATE`, `DELETE`, `DROP`, `ALTER`, `TRUNCATE`, `GRANT`).
- **Connection Isolation:** Executes against a read-only database session with statement timeouts and maximum row limit caps (e.g., 100 rows per query).

### 3.6. Document & Knowledge Retrieval Tool
- Searches internal policies, postmortems, standard operating procedures, and product memos.
- Employs hybrid retrieval (Vector semantic similarity + Full-Text Search / FTS) to locate relevant passages.
- Returns explicit text chunks with document titles, section headers, and file paths for verifiable citations.

### 3.7. Evidence Collection Engine (Phase 4 — Implemented)

**Evidence collection is deterministic and does NOT use an LLM.**

**`EvidenceItem`** — the core unit (immutable, `frozen=True`):
- `evidence_id`: stable ID in `EVID-NNN` format (assigned in collection order within a run).
- `investigation_run_id`, `step_id`, `tool_name`: full provenance chain.
- `evidence_type`: controlled vocabulary (`SQL_RESULT`, `DOCUMENT_TEXT`, `DOCUMENT_MATCH`, `DOCUMENT_SEARCH_SUMMARY`, `DOCUMENT_LISTING`, `METRIC`).
- `source_reference`: human-readable reference to the evidence source (e.g. `sql_investigation:STEP-03`).
- `content`: typed, structured content (schema-validated via `SQLEvidenceContent`, `DocumentTextContent`, etc.).
- `content_hash`: deterministic SHA-256 hex digest of the canonicalized content — mutation-detectable.

**`EvidenceStore`** — append-only, per-run collection:
- Items are indexed by `evidence_id` for O(1) lookup.
- Attempting to overwrite an existing ID raises `ValueError`.
- Exposes `for_step(step_id)` and `ids_for_step(step_id)` for step-level queries.

**`EvidenceCollector`** — faithful tool output transcriber:
- SQL results → `SQL_RESULT` (preserves query, columns, rows, row_count, truncated flag).
- Document `get` → `DOCUMENT_TEXT` (preserves document_id, full text, char_count).
- Document `search` → `DOCUMENT_SEARCH_SUMMARY` (always) + `DOCUMENT_MATCH` per match.
- Document `list` → `DOCUMENT_LISTING`.
- FAILED and BLOCKED steps produce **zero evidence** (no fabrication).

**Evidence IDs** are attached to `InvestigationStepResult.evidence_ids` creating the chain:
```
investigation step → evidence IDs → typed evidence content
```

### 3.8. Grounded Investigation Synthesis Layer (Phase 5 — Implemented)

The Phase 5 synthesis layer converts collected investigation evidence into an auditable, evidence-backed report **without direct tool access or unrestricted generation**:

**`InvestigationReport` & Synthesis Models:**
- Strongly typed Pydantic models: `Finding`, `Recommendation`, `InvestigationReport`.
- `Finding` carries `finding_id`, `statement`, `evidence_ids`, `confidence`.
- `Recommendation` carries `recommendation_id`, `action`, `rationale`, `evidence_ids`, `priority`.
- `InvestigationReport` carries `executive_summary`, `findings`, `root_cause`, `contributing_factors`, `recommendations`, `limitations`, `evidence_ids`, `citation_valid`, `synthesis_status`, `validation_errors`.

**`LLMProvider` & `MockLLMProvider`:**
- Abstract provider interface decoupled from vendor-specific libraries.
- Default `MockLLMProvider` is deterministic and fully offline (zero API keys required).
- Resilient against prompt injection embedded within retrieved document content.

**`PromptBuilder` & Data Boundaries:**
- Strictly encapsulates retrieved evidence inside delimited `BEGIN UNTRUSTED EVIDENCE BLOCK (DATA ONLY)` markers.
- Instructs the synthesis engine to treat document text as inert data, never as executable instructions.
- Mandates explicit evidence ID citations for all factual assertions.

**`CitationValidator` & Cross-Run Isolation:**
- Deterministically verifies that all cited `evidence_ids` in findings, recommendations, and report metadata exist in the active `EvidenceStore`.
- Strict cross-run isolation: foreign run evidence IDs trigger immediate validation failure.
- Citations are never silently repaired.

**`InvestigationSynthesizer`:**
- Coordinates prompt construction, provider generation, structured schema parsing, citation validation, and audit recording.
- Handles insufficient evidence safely by setting `root_cause=None` and `synthesis_status=INSUFFICIENT_EVIDENCE`.

### 3.9. Security & Guardrails
- **No Unrestricted Execution:** No shell access, no `eval()`, no dynamic imports.
- **Prompt Injection Defense:** Inputs and tool responses are demarcated with strict boundary markers; tool outputs are treated as untrusted data.
- **Sanitized SQL Error Handling:** Database engine errors are captured and sanitized before reflection to prevent leaking underlying infrastructure topology.
- **Read-Only Synthesis:** The synthesis layer is a downstream, read-only consumer of evidence; it has zero direct access to SQL or document tools.

### 3.10. Audit Trail & Reproducibility (Phases 4 & 5 — Implemented)

**`AuditTrail`** — append-only lifecycle log (per investigation run):
- Records `AuditEvent` instances with deterministic sequence numbers (`AUDIT-NNN`).
- Events are **immutable** (`frozen=True`): once recorded they cannot be mutated.
- Event types: `INVESTIGATION_STARTED`, `PLAN_CREATED`, `STEP_STARTED`, `STEP_COMPLETED`, `STEP_FAILED`, `STEP_BLOCKED`, `EVIDENCE_COLLECTED`, `INVESTIGATION_COMPLETED`, `INVESTIGATION_PARTIAL`, `INVESTIGATION_FAILED`, `SYNTHESIS_STARTED`, `SYNTHESIS_GENERATED`, `SYNTHESIS_VALIDATED`, `SYNTHESIS_FAILED`.
- Each event carries: `step_id`, `tool_name`, `evidence_ids` (when applicable), and structured `metadata`.
- `all()` returns a defensive copy; internal state cannot be corrupted by external mutation.
- Sequence numbers are deterministic integers — suitable for reproducible testing without wall-clock dependency.

### 3.11. Evaluation Strategy
- Evaluated deterministically against an offline **Golden Evaluation Dataset** containing synthetic scenarios with known root causes.
- Metrics tracked:
  - **SQL Correctness:** Did the generated query produce the correct ground-truth result?
  - **Evidence Completeness:** Were all required facts retrieved prior to concluding?
  - **Citation Precision:** Does every statement in the recommendation link to a valid evidence item?
  - **Safety Compliance:** 100% rejection rate for unsafe queries (mutations, out-of-scope schemas).
- **Zero Fabricated Numbers:** All benchmarks run deterministically via automated pytest test suites.

### 3.12. Future Scaling Path
- **Async Execution:** Celery or Redis-backed background worker queue for long-running investigations.
- **Multi-Tenant Data Isolation:** Tenant-scoped database schemas and vector search namespaces.
- **Enterprise RBAC:** Role-based access control governing which analysts can approve specific high-impact recommendations.
