# Enterprise AI Investigation & Decision System

> **Portfolio & Educational Disclaimer:**
> This repository is an educational portfolio project simulating an enterprise-grade AI investigation and decision-support system. It is designed to demonstrate production-grade AI system architecture, safety guardrails, controlled tool execution, and evidence-first decision making. It does **not** claim real company usage, real customer data, or fabricated performance metrics.

---

## 📌 Problem Statement

In enterprise environments, operational anomalies (such as sudden customer churn spikes, billing discrepancies, or support escalations) require cross-functional investigation across structured relational databases and unstructured internal documents. 

Standard LLM chat interfaces often hallucinate answers, lack access to live data, or pose severe security risks if granted unconstrained database or shell access. Enterprises need an **auditable, deterministic, and evidence-grounded AI investigation system** where every conclusion is traceable back to verified raw evidence, tools operate within strict sandboxes, and actions require human authorization.

---

## 🏢 Synthetic Business Investigation Scenario

The system currently models a realistic SaaS operational scenario:

> *"Customer cancellations increased significantly during Q3 2025. An internal analyst needs to investigate whether the increase is related to billing issues, support performance, product incidents, customer segments, or other operational factors."*

### Planted Multi-Table Business Signals:
1. **Software Release:** Deployment of `billing-gateway` version `v2.4.0` on 2025-09-02 introduced a webhook confirmation bug.
2. **Product Incident:** A P1 incident (`INC-2025-002`) on 2025-09-05 where valid enterprise/pro customer payments were erroneously flagged as failed.
3. **Billing Failures:** Failed subscription payment events surged from <3% to >30% in September for affected cohorts.
4. **Support Queue Overload:** An influx of billing-related support tickets caused average resolution times to surge from ~4.5 hours to >45 hours.
5. **Customer Churn Spike:** Subscriptions for affected pro/enterprise customers suffered an acute spike in cancellations citing payment and lockout issues.

Solving this investigation requires correlating data across all 6 relational tables and internal postmortem documents.

---

## 🗄️ Relational Database Schema

The database is built on SQLite (with PostgreSQL-ready SQLAlchemy abstractions) and comprises 6 normalized entities:

| Table | Description | Key Fields |
| :--- | :--- | :--- |
| `customers` | Core customer registry | `customer_id`, `segment`, `region`, `signup_date`, `plan` |
| `subscriptions` | Customer subscription states | `subscription_id`, `customer_id`, `status`, `cancellation_date`, `cancellation_reason` |
| `billing_events` | Charge and payment lifecycle | `billing_event_id`, `customer_id`, `event_date`, `event_type`, `amount`, `status` |
| `support_tickets` | Support ticket queue & SLAs | `ticket_id`, `customer_id`, `created_at`, `resolved_at`, `priority`, `category`, `status` |
| `product_incidents` | Major platform incident records | `incident_id`, `incident_date`, `severity`, `service`, `description` |
| `release_events` | Software deployment history | `release_id`, `release_date`, `service`, `version`, `change_type` |

---

## 🔧 Controlled Investigation Tools (Phase 2)

The system exposes a secure, deterministic tool layer under `src/tools/` governed by a centralized `ToolRegistry`. Tools communicate exclusively via strictly typed Pydantic input and output schemas:

### 1. `sql_investigation`
- **Purpose:** Executes read-only analytical SQL queries against the enterprise relational database.
- **Safety Boundaries:**
  - Enforces `SELECT` or `WITH` (CTE) statements only.
  - Multi-statement execution (semicolons separating queries) is strictly prohibited.
  - Discrete token check disallows mutation keywords: `INSERT`, `UPDATE`, `DELETE`, `DROP`, `ALTER`, `TRUNCATE`, `CREATE`, `ATTACH`, `PRAGMA`, `EXEC`, `VACUUM`, etc.
  - Parameterized query values (`:param`) are strictly isolated from SQL text.
  - Configurable row limits (`max_rows`) with explicit `truncated: bool` flag.
  - Max query length (5,000 chars) and max parameter count (50 params) limits.

### 2. `document_retrieval`
- **Purpose:** Discovers and retrieves internal postmortems, policy memos, and runbooks from configured document directories.
- **Actions Supported:**
  - `list`: Lists available documents with metadata (title, byte size, path).
  - `get`: Reads full document text by identifier (`document_id`).
  - `search`: Deterministic keyword/phrase search across documents with line numbers and context snippets.
- **Safety Boundaries:**
  - Absolute paths (`/etc/`, `C:\`) and directory traversal sequences (`../`, `..\`) are strictly rejected.
  - File access is locked exclusively to the configured knowledge base directory.

---

## 🔄 Investigation Flow (Target Architecture)

```
Business Question / Incident Alert
               │
               ▼
   [ Investigation Planner ]  (Upcoming Phase 3)
               │
               ▼
   [ Controlled Tool Registry ]  (Implemented in Phase 2)
       ├── Read-Only SQL Investigation Tool (`sql_investigation`)
       └── Document & Policy Retrieval Tool (`document_retrieval`)
               │
               ▼
     [ Evidence Collector ]   (Upcoming Phase 4)
  (Raw queries, records, citations)
               │
               ▼
     [ Root-Cause Analysis ]
               │
               ▼
  [ Evidence-Backed Recommendation ]
               │
               ▼
    [ Human Approval / Sign-Off ]
```

---

## 🚀 Getting Started

### 1. Environment Setup
```bash
pip install -e .
# Or install dev dependencies:
pip install -e ".[dev]"
```

### 2. Seed the Deterministic Database
Populate the SQLite database with synthetic enterprise records:
```bash
python -m src.data.seed_database
```

### 3. Run the Test & Evaluation Suite
Run all unit tests, security guardrail tests, integration tests, and scenario evaluations:
```bash
python -m pytest
```

### 4. Start the API Server
```bash
uvicorn src.api.main:app --reload --port 8000
```
Verify the health endpoint:
```bash
curl http://localhost:8000/health
# Returns: {"status": "ok"}
```

---

## ⚠️ Current Phase & Limitations

- **Current Status:** `Phase 2 — Controlled Investigation Tools` (Completed)
- **Next Up:** `Phase 3 — Investigation Planner`
- **Current Limitations:**
  - **No LLM or Autonomous Agent:** The tools and tests currently run in deterministic, offline-capable Python without live AI models (scheduled for Phase 5).
  - **No Vector Search:** Document retrieval uses deterministic keyword/phrase indexing without embedding models.
  - **No Web Investigation API:** The FastAPI app currently exposes `/health`; full investigation execution endpoints will be added in subsequent phases.

---

## 📚 Documentation Links
- [Architecture Details (ARCHITECTURE.md)](docs/ARCHITECTURE.md)
- [Implementation Roadmap (ROADMAP.md)](docs/ROADMAP.md)
- [Architecture Decision Records (DECISIONS.md)](docs/DECISIONS.md)
