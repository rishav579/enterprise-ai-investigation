# Enterprise AI Investigation & Decision System

> **Portfolio & Educational Disclaimer:**
> This repository is an educational portfolio project simulating an enterprise-grade AI investigation and decision-support system. It demonstrates production-grade AI system architecture, safety guardrails, controlled tool execution, deterministic planning, evidence collection with integrity hashing, an immutable audit trail, and evidence-grounded report synthesis with strict citation validation. It does **not** claim real company usage, real customer data, or fabricated performance metrics.

---

## 📌 Problem Statement

In enterprise environments, operational anomalies (such as sudden customer churn spikes, billing discrepancies, or support escalations) require cross-functional investigation across structured relational databases and unstructured internal documents.

Standard LLM chat interfaces often hallucinate answers, lack access to live data, or pose severe security risks if granted unconstrained database or shell access. Enterprises need an **auditable, deterministic, and evidence-grounded AI investigation system** where every conclusion is traceable back to verified raw evidence, tools operate within strict sandboxes, and actions require human authorization.

---

## 🏢 Synthetic Business Investigation Scenario

The system currently models a realistic SaaS operational scenario:

> *"Customer cancellations increased significantly during Q3 2025. An internal analyst needs to investigate whether the increase is related to billing issues, support performance, product incidents, customer segments, or other operational factors."*

### Planted Multi-Table Business Signals:
1. **Software Release:** `billing-gateway` `v2.4.0` deployed on 2025-09-02 introduced a webhook confirmation bug.
2. **Product Incident:** P1 incident (`INC-2025-002`) on 2025-09-05 — valid payments erroneously flagged as failed.
3. **Billing Failures:** Failed charges surged from <3% to >30% in September for affected cohorts.
4. **Support Queue Overload:** Resolution times surged from ~4.5 hrs to >45 hrs during the incident window.
5. **Customer Churn Spike:** Pro/enterprise customers in EU-Central and US-East cancelled at >5x baseline rate.

Solving this investigation requires correlating all 6 relational tables plus internal postmortem documents.

---

## 🗄️ Database Schema

| Table | Description |
| :--- | :--- |
| `customers` | Customer accounts: `segment`, `region`, `plan`, `signup_date` |
| `subscriptions` | Subscription lifecycle: `status`, `cancellation_date`, `cancellation_reason` |
| `billing_events` | Payment transactions: `event_type`, `amount`, `status` |
| `support_tickets` | Support queue: `priority`, `category`, `created_at`, `resolved_at`, `status` |
| `product_incidents` | Platform incidents: `severity`, `service`, `description` |
| `release_events` | Deployments: `service`, `version`, `change_type` |

---

## 🧠 Investigation & Synthesis Architecture (Phases 1–5)

```
Business Question
      │
      ▼
[ InvestigationPlanner ]          — deterministic, keyword/scenario detection
      │
      ▼
[ InvestigationPlan ]             — typed Pydantic model with declared dependencies
      │
      ▼
[ InvestigationOrchestrator ]     — executes via ToolRegistry only
  respects step order
  dependency-aware (BLOCKED on unmet deps)
  graceful per-step error isolation
  records AuditEvents for every lifecycle transition
      │
      ├──→ [ EvidenceCollector ]  — deterministic, downstream of tools
      │       SQL results → SQL_RESULT evidence
      │       Doc get     → DOCUMENT_TEXT evidence
      │       Doc search  → DOCUMENT_SEARCH_SUMMARY + DOCUMENT_MATCH
      │       Doc list    → DOCUMENT_LISTING evidence
      │       Failed/blocked steps → ZERO evidence (no fabrication)
      │       Every EvidenceItem carries a SHA-256 content hash
      │
      ├──→ [ AuditTrail ]         — append-only, immutable events
      │       INVESTIGATION_STARTED → PLAN_CREATED
      │       STEP_STARTED → STEP_COMPLETED | STEP_FAILED | STEP_BLOCKED
      │       EVIDENCE_COLLECTED
      │       SYNTHESIS_STARTED → SYNTHESIS_GENERATED → SYNTHESIS_VALIDATED
      │       INVESTIGATION_COMPLETED
      │
      ▼
[ InvestigationSynthesizer ]      — read-only consumer of EvidenceStore
      │
      ├──→ [ PromptBuilder ]      — encapsulates data inside safety boundaries
      ├──→ [ LLMProvider ]        — abstract provider (MockLLMProvider offline)
      ├──→ [ CitationValidator ]  — strictly verifies all cited evidence IDs
      │
      ▼
[ InvestigationReport ]           — typed, evidence-backed report
  findings with valid evidence_ids
  root cause, contributing factors, recommendations
  citation_valid: True/False, synthesis_status
```

---

## 🔒 Evidence & Citation Model

Each `EvidenceItem` answers:

| Field | Question Answered |
| :--- | :--- |
| `evidence_id` | What is this item's unique identifier? (`EVID-001` etc.) |
| `investigation_run_id` | Which investigation run produced this? |
| `step_id` | Which investigation step produced this? |
| `tool_name` | Which tool produced this? |
| `evidence_type` | What kind of evidence is this? (SQL result, document text, etc.) |
| `source_reference` | What exact source/query/document? |
| `content` | What is the raw structured data? (typed schema) |
| `content_hash` | SHA-256 fingerprint — detects any content mutation |

**Strict Citation Validation:**
- Every `Finding` and `Recommendation` must link to valid evidence IDs in the active run.
- Foreign run evidence citations are strictly rejected (Cross-Run Isolation).
- If evidence is insufficient, `root_cause` is set to `null` with status `INSUFFICIENT_EVIDENCE`.
- Prompt injection commands in retrieved documents are treated strictly as inert textual data.

---

## 🔧 Controlled Investigation Tools (Phase 2)

| Tool | Purpose |
| :--- | :--- |
| `sql_investigation` | Read-only SELECT/WITH queries with token-level mutation blocking |
| `document_retrieval` | `list`, `get`, `search` over the knowledge base repository |

**Security boundaries:** No shell execution, no arbitrary filesystem access, no dynamic code evaluation. SQL mutations (`DELETE`, `DROP`, `ALTER`, etc.) and path traversal (`../`) are strictly rejected.

---

## 🖥️ Frontend Investigation Workspace (Phase 7)

The system includes a dedicated, responsive operations web interface built with **React 19**, **TypeScript**, and **Vite** located in `frontend/`:

- **Interactive Investigation Timeline:** Real-time step inspection displaying status pills, tool dispatches, query payloads, row counts, and collected artifact tokens.
- **Evidence Inspector Drawer:** Deep inspection modal for raw SQL data grids, full document text excerpts, query provenance, and canonical SHA-256 tamper-evident hash validation.
- **Synthesized Findings & Root Cause View:** Structured executive summary, primary root cause alert box, confidence badges (`HIGH`, `MEDIUM`, `LOW`), and strict `100% Verified` citation tokens.
- **Human Review Simulation:** Explicit simulated human authorization workflow ("Approve", "Reject", "Request More Evidence") with review logs and timestamped reviewer notes.
- **Immutable Audit Log Stream:** Filterable chronological stream of lifecycle transitions (`INVESTIGATION_STARTED`, `PLAN_CREATED`, `STEP_COMPLETED`, `EVIDENCE_COLLECTED`, `SYNTHESIS_VALIDATED`).

---

## 🚀 Getting Started

### 1. Backend Setup & Test Suite
```bash
# Install Python dependencies
pip install -e ".[dev]"

# Seed the enterprise SQLite database
python -m src.data.seed_database

# Run complete backend pytest suite (195 tests)
python -m pytest

# Run offline golden evaluation benchmark runner
python run_evaluation.py

# Start FastAPI backend server on port 8000
python -m uvicorn src.api.main:app --reload --port 8000
```

### 2. Frontend Workspace Setup & Tests
```bash
# Navigate to frontend
cd frontend

# Install dependencies
npm install

# Run frontend test suite (32 tests across 8 test suites)
npm test

# Build production bundle
npm run build

# Start local Vite development server on port 5173
npm run dev
```

Open `http://localhost:5173` in your browser to interact with the investigation console.

---

## 🧪 Deterministic Evaluation & Benchmark (Phase 6)

The project includes an offline **Golden Evaluation Dataset** (`src/evaluation/`) testing multi-domain scenarios:
- `scenario_A_churn`: Q3 Customer Churn Spike (100% evidence recall, exact root cause identification).
- `scenario_B_support_spike`: Regional support SLA degradation.
- `scenario_C_product_incident`: API Gateway P1 incident correlation.
- `scenario_D_insufficient`: Insufficient evidence handling (zero-hallucination verification).
- `scenario_E_security_sql`: SQL mutation rejection (DELETE/DROP blocked).
- `scenario_F_security_traversal`: Path traversal boundary rejection.

Run evaluation locally:
```bash
python run_evaluation.py
```

---

## ⚠️ Current Status & Architecture Invariants

- **Current Phase:** `Phase 7 — Frontend Investigation Workspace` (Completed & Verified)
- **Next Phase:** `Phase 8 — Deployment` (Planned)
- **Verification & Test Status:**
  - Backend: 195/195 tests passing (`python -m pytest`)
  - Frontend: 32/32 tests passing across 8 suites (`npm test`)
  - Evaluation Harness: 6/6 golden evaluation scenarios passing (`python run_evaluation.py`)
  - Production Bundle: `npm run build` cleanly compiled with TypeScript checks
- **Current Limitations & Operational Boundaries:**
  - **No Public Deployment:** The system is currently verified for local development and demonstration; containerized deployment and Docker Compose orchestrations are scheduled for Phase 8.
  - **Offline Provider:** Grounded synthesis utilizes the deterministic offline `MockLLMProvider` (pluggable for enterprise OpenAI/Anthropic SDK adapters).
  - **Zero-Fabrication Invariant:** All factual findings and recommendations must link to valid evidence IDs verified against the immutable `EvidenceStore`.
  - **Zero-Network Invariant:** Capable of running in fully offline / air-gapped test and review environments without API keys or external telemetry dependencies.
  - **Human Review Simulation:** The frontend provides a safe, clearly labeled simulation of internal decision sign-off without executing arbitrary unverified backend mutations.

---

## 📚 Documentation
- [Architecture Specification (ARCHITECTURE.md)](docs/ARCHITECTURE.md)
- [Project Roadmap (ROADMAP.md)](docs/ROADMAP.md)
- [Architecture Decision Records (DECISIONS.md)](docs/DECISIONS.md)

