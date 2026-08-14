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

### 3.7. Evidence Collection Engine
- Stores every fact discovered during tool execution as an **Evidence Item**.
- Each item contains: `evidence_id`, `source_tool`, `raw_payload`, `timestamp`, `step_index`, and `citation_tag`.
- The final synthesis layer is strictly constrained to reference only registered Evidence Items.

### 3.8. Decision & Recommendation Layer
- Synthesizes findings into a structured decision payload:
  - **Executive Summary:** Clear narrative of what occurred.
  - **Evidence Table:** Specific data points linked to evidence IDs.
  - **Root Cause Hypotheses:** Evaluated as Supported, Rejected, or Inconclusive.
  - **Recommended Actions:** Proposed operational remediations.
  - **Risk & Uncertainty Assessment:** Known data limitations and confidence level.

### 3.9. Security & Guardrails
- **No Unrestricted Execution:** No shell access, no `eval()`, no dynamic imports.
- **Prompt Injection Defense:** Inputs and tool responses are demarcated with strict boundary markers; tool outputs are treated as untrusted data.
- **Sanitized SQL Error Handling:** Database engine errors are captured and sanitized before reflection to prevent leaking underlying infrastructure topology.

### 3.10. Audit Trail & Reproducibility
- An append-only audit log records the complete lifecycle of every investigation.
- Stores:
  1. Initial prompt and user context.
  2. Investigation plan steps.
  3. Raw tool inputs and raw tool outputs.
  4. Model reasoning steps.
  5. Human approval decisions, reviewer identity, and timestamps.

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
