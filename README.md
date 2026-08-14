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

Solving this investigation requires correlating data across all 6 relational tables rather than relying on a single isolated column.

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

## 🔄 Investigation Flow (Target Architecture)

```
Business Question / Incident Alert
               │
               ▼
   [ Investigation Planner ]
               │
               ▼
   [ Controlled Tool Registry ]
       ├── Read-Only SQL Investigation Tool
       ├── Document & Policy Retrieval Tool
       └── Domain-Specific API Tools (Mocked)
               │
               ▼
     [ Evidence Collector ]
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

## 🛡️ Core Architectural Principles

- **Controlled Tools Only:** No arbitrary shell or dynamic code execution. Every tool has a strictly typed input/output schema.
- **Read-Only SQL Access:** All SQL queries are parsed via Abstract Syntax Tree (AST) validation and executed against read-only database connections.
- **Evidence-First Responses:** Every claim in a final recommendation must cite specific records, metrics, or document excerpts captured in the evidence collector.
- **Auditable Tool Execution:** Complete immutable audit logs capturing prompts, tool invocations, parameters, raw tool outputs, and timestamps.
- **Data & Repository Isolation:** Clear separation between domain logic, data access repositories, and AI orchestration.
- **Provider-Agnostic LLM Layer:** Abstracted model interface allowing seamless switching between OpenAI, Anthropic, or local offline models (e.g., via Ollama).
- **Deterministic Evaluation:** System performance is evaluated against reproducible, offline test scenarios with verified ground truth—avoiding subjective or fabricated benchmark numbers.

---

## 🚀 Getting Started

### 1. Environment Setup
Clone the repository and install dependencies:
```bash
pip install -e .
# Or install optional dev dependencies:
pip install -e ".[dev]"
```

### 2. Seed the Deterministic Database
Populate the SQLite database with the synthetic enterprise dataset:
```bash
python -m src.data.seed_database
```

### 3. Run the Test & Evaluation Suite
Run all unit tests, integration tests, and scenario evaluation checks:
```bash
python -m pytest
```

### 4. Start the API Server
Start the local FastAPI development server:
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

- **Current Status:** `Phase 1 — Enterprise Data Foundation` (Completed)
- **Next Up:** `Phase 2 — Controlled Investigation Tools`
- **Current Limitations:**
  - LLM orchestration and agent planning are not yet active (scheduled for Phases 2–5).
  - The API currently exposes only `/health`; investigation endpoints will be added once tool and planning engines are integrated.

---

## 📚 Documentation Links
- [Architecture Details (ARCHITECTURE.md)](docs/ARCHITECTURE.md)
- [Implementation Roadmap (ROADMAP.md)](docs/ROADMAP.md)
- [Architecture Decision Records (DECISIONS.md)](docs/DECISIONS.md)
