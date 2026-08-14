# Enterprise AI Investigation & Decision System

> **Portfolio & Educational Disclaimer:**
> This repository is an educational portfolio project simulating an enterprise-grade AI investigation and decision-support system. It demonstrates production-grade AI system architecture, safety guardrails, controlled tool execution, deterministic planning, evidence collection with integrity hashing, and a complete investigation audit trail. It does **not** claim real company usage, real customer data, or fabricated performance metrics.

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

## 🧠 Investigation Architecture (Phases 1–4)

```
Business Question
      │
      ▼
[ InvestigationPlanner ]          — deterministic, no LLM
  keyword-based scenario detection
  canonical step sequence generation
      │
      ▼
[ InvestigationPlan ]             — typed Pydantic model
  ordered InvestigationStep list
  step dependencies declared
      │
      ▼
[ InvestigationOrchestrator ]     — executes via ToolRegistry only
  respects step order
  dependency-aware (BLOCKED on unmet deps)
  graceful per-step error isolation
  records AuditEvents for every lifecycle transition
      │
      ├──→ [ EvidenceCollector ]  — deterministic, no LLM
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
      │       EVIDENCE_COLLECTED → INVESTIGATION_COMPLETED
      │
      ▼
[ InvestigationRunResult ]        — fully typed, Phase 4 extended
  per-step results with evidence_ids
  total_evidence_items, audit_event_count
  overall status (COMPLETED / PARTIAL / FAILED)
```

> **Note:** No LLM reasoning or autonomous agent is active yet. The planner uses explicit, deterministic scenario definitions. LLM integration is planned for Phase 5.

---

## 🔒 Evidence Model

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

**Evidence collection is deterministic and does NOT use an LLM.**

---

## 🔧 Controlled Investigation Tools (Phase 2)

| Tool | Purpose |
| :--- | :--- |
| `sql_investigation` | Read-only SELECT/WITH queries with token-level mutation blocking |
| `document_retrieval` | `list`, `get`, `search` over the knowledge base repository |

**Security boundaries:** No shell execution, no arbitrary filesystem access, no dynamic code evaluation. SQL mutations (`DELETE`, `DROP`, `ALTER`, etc.) and path traversal (`../`) are strictly rejected.

---

## 🚀 Getting Started

### 1. Install dependencies
```bash
pip install -e ".[dev]"
```

### 2. Seed the database
```bash
python -m src.data.seed_database
```

### 3. Run all tests (167 tests)
```bash
python -m pytest
```

### 4. Start the API server
```bash
uvicorn src.api.main:app --reload --port 8000
curl http://localhost:8000/health   # {"status": "ok"}
```

---

## ⚠️ Current Status & Limitations

- **Current Phase:** `Phase 4 — Evidence Collection & Auditability` (Completed)
- **Next Phase:** `Phase 5 — AI Integration (LLM Client Abstraction)`
- **Limitations:**
  - No LLM reasoning yet — planner is deterministic and rule-based.
  - No recommendation synthesis yet (Phase 5+).
  - No human approval workflow yet (Phase 5+).
  - FastAPI exposes only `/health`; investigation endpoints come in a later phase.
  - Evidence stores are in-memory per run; persistence comes in a later phase.

---

## 📚 Documentation
- [Architecture (ARCHITECTURE.md)](docs/ARCHITECTURE.md)
- [Roadmap (ROADMAP.md)](docs/ROADMAP.md)
- [Architecture Decision Records (DECISIONS.md)](docs/DECISIONS.md)
